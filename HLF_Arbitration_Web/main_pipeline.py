import os
import json
import pandas as pd
from datetime import datetime

# Import your extractors
from src.extract_claim import extract_claim_data
from src.extract_soa import extract_soa_data
from src.extract_agreement import extract_agreement_data

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input_docs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_contract_groups(input_dir):
    """
    Scans the input directory and groups files by Contract Number.
    """
    files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    groups = {}

    for f in files:
        parts = f.split('_')
        if len(parts) < 2:
            continue
        
        contract_no = parts[0]
        doc_type = parts[1].lower()

        if contract_no not in groups:
            groups[contract_no] = {"Agreement": None, "SOA": None, "Claim": None}

        if "agreement" in doc_type:
            groups[contract_no]["Agreement"] = os.path.join(input_dir, f)
        elif "soa" in doc_type:
            groups[contract_no]["SOA"] = os.path.join(input_dir, f)
        elif "claim" in doc_type:
            groups[contract_no]["Claim"] = os.path.join(input_dir, f)
    
    return groups

def flatten_for_db_staging(all_data):
    """
    Transforms extracted data into 3 lists that perfectly match 
    the NeonDB table structures: Contracts, Respondents, Assets.
    """
    contracts_rows = []
    respondents_rows = []
    assets_rows = []

    for case in all_data:
        c_no = case['contract_no']
        
        # --- SOURCES ---
        agr = case.get('agreement_data') or {}
        agr_info = agr.get('agreementInfo') or {}
        soa = case.get('soa_data') or {}
        soa_fin = soa.get('financials') or {}
        claim = case.get('claim_data') or {}
        arb = agr.get('arbitration') or {}
        
        # ---------------------------------------------------------
        # 1. TABLE: CONTRACTS
        # ---------------------------------------------------------
        # Priority logic for values that appear in multiple docs
        loan_amt = agr_info.get('loanAmount') or soa_fin.get('financeAmount')
        emi_amt = agr_info.get('emiAmount') or soa_fin.get('emiAmount')
        ag_val = soa_fin.get('agreementValue') or claim.get('agreementValue', {}).get('totalReceivable')
        
        contracts_rows.append({
            "contract_no": c_no,
            "agreement_date": agr_info.get('agreementDate'),
            "loan_amount": loan_amt,
            "agreement_value": ag_val,
            "emi_amount": emi_amt,
            "arbitration_clause": arb.get('venue'), # Storing Venue as key identifier
            "disbursal_date": None, # Usually not explicitly extracted yet, placeholder
            "tenure_months": agr_info.get('tenure'),
            "finance_charges": soa_fin.get('financeCharges')
        })

        # ---------------------------------------------------------
        # 2. TABLE: RESPONDENTS
        # ---------------------------------------------------------
        # Helper to add respondent row
        def add_respondent(role, source_obj):
            if source_obj and source_obj.get('name'):
                respondents_rows.append({
                    "contract_no_ref": c_no, # For joining later
                    "role": role,
                    "full_name": source_obj.get('name'),
                    "address_line_1": source_obj.get('address'),
                    "city": None,   # Can be parsed from address later
                    "state": None,
                    "pincode": None # Can be parsed from address later
                })

        # Add Borrower (Source: Agreement preferred, SOA backup)
        bor_src = agr.get('borrower') or soa.get('customerInfo')
        add_respondent("Borrower", bor_src)

        # Add Co-Borrower (Source: Agreement only)
        add_respondent("Co-Borrower", agr.get('coBorrower'))

        # Add Guarantor (Source: Agreement preferred, SOA backup)
        guar_src = agr.get('guarantor')
        # If agreement missed it, try SOA
        if not guar_src or not guar_src.get('name'):
            if soa.get('customerInfo', {}).get('guarantorName'):
                guar_src = {
                    "name": soa['customerInfo']['guarantorName'],
                    "address": soa['customerInfo'].get('guarantorAddress')
                }
        add_respondent("Guarantor", guar_src)

        # ---------------------------------------------------------
        # 3. TABLE: ASSETS
        # ---------------------------------------------------------
        asset_info = agr.get('asset') or {}
        soa_prod = soa.get('productInfo') or {}
        
        # Merge data (Agreement usually better for Chassis/Engine)
        desc = asset_info.get('assetDescription') or soa_prod.get('productModel')
        chassis = asset_info.get('chassisNo') or soa_prod.get('chassisNo')
        engine = asset_info.get('engineNo') or soa_prod.get('engineNo')
        reg_no = asset_info.get('registrationNo') or soa_prod.get('vehicleNo')

        assets_rows.append({
            "contract_no_ref": c_no,
            "asset_type": "Vehicle",
            "description": desc,
            "identifier_1": chassis, # Chassis No
            "identifier_2": engine,  # Engine No
            "identifier_3": reg_no,  # Registration No
            "possession_status": "Repossessed" if claim.get('dates', {}).get('repoDate') else "Live"
        })

    return contracts_rows, respondents_rows, assets_rows

def save_reports(all_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save Master JSON (Audit Trail)
    json_path = os.path.join(OUTPUT_DIR, f"Master_Data_{timestamp}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, default=str)
    
    # 2. Save DB Staging Excel
    excel_path = os.path.join(OUTPUT_DIR, f"DB_Staging_Review_{timestamp}.xlsx")
    con_data, res_data, ast_data = flatten_for_db_staging(all_data)

    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Sheet 1: Contracts
            if con_data:
                pd.DataFrame(con_data).to_excel(writer, sheet_name='contracts', index=False)
            
            # Sheet 2: Respondents
            if res_data:
                pd.DataFrame(res_data).to_excel(writer, sheet_name='respondents', index=False)
            
            # Sheet 3: Assets
            if ast_data:
                pd.DataFrame(ast_data).to_excel(writer, sheet_name='assets', index=False)
                
        print(f"✅ Staging Excel Saved: {excel_path}")
        print("   (Columns match your NeonDB Schema)")

    except Exception as e:
        print(f"❌ Error creating Excel: {e}")

def main():
    print("🚀 STARTING DB STAGING PIPELINE...")
    print("-" * 50)

    # 1. Group Files
    case_groups = get_contract_groups(INPUT_DIR)
    print(f"📦 Found {len(case_groups)} Unique Cases")

    all_extracted_data = []

    # 2. Process Each Case
    for contract_no, files in case_groups.items():
        print(f"\n🔹 Processing: {contract_no}")
        
        case_data = {
            "contract_no": contract_no,
            "agreement_data": None,
            "soa_data": None,
            "claim_data": None
        }

        # Agreement
        if files["Agreement"]:
            print(f"   Reading Agreement...")
            case_data["agreement_data"] = extract_agreement_data(files["Agreement"])
        
        # SOA
        if files["SOA"]:
            print(f"   Reading SOA...")
            case_data["soa_data"] = extract_soa_data(files["SOA"])

        # Claim
        if files["Claim"]:
            print(f"   Reading Claim...")
            case_data["claim_data"] = extract_claim_data(files["Claim"])

        all_extracted_data.append(case_data)

    # 3. Generate Reports
    print("-" * 50)
    if all_extracted_data:
        save_reports(all_extracted_data)
        print("\n✅ DONE.")
    else:
        print("⚠️ No data extracted.")

if __name__ == "__main__":
    main()