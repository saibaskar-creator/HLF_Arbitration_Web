import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional, List
import json
from pydantic import BaseModel

from src.extract_agreement import extract_agreement_data
from src.extract_soa import extract_soa_data
from src.extract_claim import extract_claim_data

router = APIRouter()

class ExtractionResponse(BaseModel):
    contract_no: str
    agreement: dict
    soa: dict
    claim: Optional[dict] = None
    warnings: List[str] = []
    file_urls: dict = {}

# Ensure upload directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/extract", response_model=ExtractionResponse)
async def upload_and_extract(
    agreement_file: UploadFile = File(...),
    soa_file: UploadFile = File(...),
    claim_file: Optional[UploadFile] = File(None)
):
    try:
        # Helper to save upload file securely
        def save_upload(file: UploadFile, label: str):
            if not file: return None
            # Sanitize filename (basic)
            safe_name = f"{label}_{os.path.basename(file.filename)}"
            path = os.path.join(UPLOAD_DIR, safe_name)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            return path, safe_name

        # Initialize warnings list
        warnings = []

        # 1. Save Files
        # We assume file exists if passed (FastAPI validation)
        agr_path, agr_name = save_upload(agreement_file, "AGR")
        soa_path, soa_name = save_upload(soa_file, "SOA")
        
        clm_path = None
        clm_name = None
        if claim_file:
            clm_path, clm_name = save_upload(claim_file, "CLM")
            
        # File URLs for frontend
        base_url = "/api/files"
        file_urls = {
            "agreement": f"{base_url}/{agr_name}",
            "soa": f"{base_url}/{soa_name}",
            "claim": f"{base_url}/{clm_name}" if clm_name else None
        }

        # 2. Extract Data (Concurrent)
        agreement_path = agr_path
        soa_path = soa_path
        claim_path = clm_path

        import asyncio
        from starlette.concurrency import run_in_threadpool
        
        # Define tasks
        tasks = [
            run_in_threadpool(extract_agreement_data, agreement_path),
            run_in_threadpool(extract_soa_data, soa_path)
        ]
        if claim_path:
            tasks.append(run_in_threadpool(extract_claim_data, claim_path))
        
        # Execute in parallel
        print("🚀 Starting parallel extraction...")
        results = await asyncio.gather(*tasks)
        print("✅ Parallel extraction complete.")
        
        ag_data = results[0]
        soa_data = results[1]
        claim_data = results[2] if claim_path else None

        if not ag_data:
            warnings.append("Failed to extract data from Agreement PDF. Please extract manually.")
            ag_data = {} # Graceful fallback
        if not soa_data:
            warnings.append("Failed to extract data from SOA PDF. Please extract manually.")
            soa_data = {} # Graceful fallback

        # 3. Validate Contract Consistency
        # Logic: Agreement is source of truth, compare with SOA
        
        c_ag = ag_data.get('agreementInfo', {}).get('agreementNo')
        c_soa = soa_data.get('contractDetails', {}).get('contractNumber')
        
        def norm(s): return s.strip().replace(' ', '').upper() if s else None

        final_contract_no = c_ag # Default to Agreement
        
        if c_ag and c_soa and norm(c_ag) != norm(c_soa):
            warnings.append(f"Contract Number mismatch! Agreement: '{c_ag}', SOA: '{c_soa}'")
        elif not c_ag and not c_soa:
            warnings.append("Could not find Contract Number in either document.")

        return {
            "contract_no": final_contract_no or "UNKNOWN",
            "agreement": ag_data,
            "soa": soa_data,
            "claim": claim_data,
            "warnings": warnings,
            "file_urls": file_urls
        }

    except Exception as e:
        import traceback
        with open("error.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        # Log error in real app
        print(f"Extraction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from database import get_db_connection
from datetime import datetime

# Helper to normalize dates (Simple parser, can be robustified)
def parse_date(date_str):
    return None # TODO: Add date parsing logic based on observation

@router.get("/check-contract/{contract_no}")
async def check_contract(contract_no: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Unavailable")
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM contracts WHERE contract_no = %s", (contract_no,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return {"exists": exists}
    except Exception as e:
        conn.close()
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SaveCaseRequest(BaseModel):
    contract_no: str
    agreement: dict
    soa: dict
    claim: Optional[dict] = None

@router.post("/save-case")
async def save_case(data: SaveCaseRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Unavailable")
    
    try:
        cur = conn.cursor()
        
        # 1. Insert into Contracts
        agr_info = data.agreement.get("agreementInfo", {})
        fin = data.soa.get("financials", {})
        
        # Helper to safely clean money strings "Rs. 1,00,000" -> 100000
        def clean_money(val):
            if not val: return None
            return float(str(val).replace('Rs.','').replace(',','').strip() or 0)

        cur.execute("""
            INSERT INTO contracts (
                contract_no, agreement_date, loan_amount, agreement_value, 
                emi_amount, tenure_months, arbitration_clause, client_code
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.contract_no,
            None, # agreement_date (Need parser)
            clean_money(fin.get("financeAmount")),
            clean_money(fin.get("agreementValue")),
            clean_money(fin.get("emiAmount")),
            None, # tenure
            data.agreement.get("arbitration", {}).get("venue"),
            "HLF" # Default client code
        ))
        contract_id = cur.fetchone()['id']
        
        # 2. Insert Respondents (Borrower, Co-Borrower, Guarantor)
        def insert_respondent(role, obj):
            if obj and obj.get("name"):
                cur.execute("""
                    INSERT INTO respondents (contract_id, role, full_name, address_line_1, party_type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    contract_id, role, obj.get("name"), obj.get("address"), "Individual"
                ))

        insert_respondent("Borrower", data.agreement.get("borrower"))
        insert_respondent("Co-Borrower", data.agreement.get("coBorrower"))
        insert_respondent("Guarantor", data.agreement.get("guarantor"))

        # 3. Insert Assets
        prod = data.soa.get("productInfo", {})
        if prod:
            cur.execute("""
                INSERT INTO assets (
                    contract_id, asset_type, description, 
                    identifier_1, identifier_2, identifier_3
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                contract_id, 
                "Vehicle", 
                prod.get("productModel"),
                prod.get("chassisNo"), # Identifier 1
                prod.get("engineNo"),  # Identifier 2
                prod.get("vehicleNo")  # Identifier 3
            ))

        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "contract_id": contract_id}

    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        
        # Log error in real app
        print(f"Extraction Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
