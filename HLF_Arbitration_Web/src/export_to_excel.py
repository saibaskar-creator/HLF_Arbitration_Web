import os
import json
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
JSON_PATH = os.path.join(BASE_DIR, "case_data_master.json")
EXCEL_PATH = os.path.join(BASE_DIR, "Case_Data_Report.xlsx")

def flatten_case_data(data):
    """
    Converts nested JSON into a flat dictionary for Excel rows.
    """
    flat = {
        # --- Meta ---
        "Case ID": data.get("meta", {}).get("case_id"),
        "Generated At": data.get("meta", {}).get("generated_at"),
        
        # --- Loan Details ---
        "Agreement No": data.get("loan_details", {}).get("agreementNo"),
        "Agreement Date": data.get("loan_details", {}).get("agreementDate"),
        "Loan Amount": data.get("loan_details", {}).get("loanAmount"),
        "EMI Amount": data.get("loan_details", {}).get("emiAmount"),
        "Tenure": data.get("loan_details", {}).get("tenure"),
        
        # --- Borrower ---
        "Borrower Name": data.get("borrower", {}).get("name"),
        "Borrower Rel": data.get("borrower", {}).get("relationship"),
        "Borrower Address": data.get("borrower", {}).get("address"),
        
        # --- Guarantor ---
        "Guarantor Name": data.get("guarantor", {}).get("name"),
        "Guarantor Rel": data.get("guarantor", {}).get("relationship"),
        "Guarantor Address": data.get("guarantor", {}).get("address"),
        
        # --- Vehicle ---
        "Asset Model": data.get("vehicle_details", {}).get("assetDescription"),
        "Chassis No": data.get("vehicle_details", {}).get("chassisNo"),
        "Engine No": data.get("vehicle_details", {}).get("engineNo"),
        "Reg No": data.get("vehicle_details", {}).get("registrationNo"),
        
        # --- Financials ---
        "Total Due (SOA)": data.get("financials", {}).get("total_due"),
        "Claim Amount (Final)": data.get("financials", {}).get("claim_amount"),
        "Cheque Bounce Count": len(data.get("financials", {}).get("cheque_bounces", [])),
        
        # --- Events ---
        "Repo Date": data.get("events", {}).get("repo_date"),
        "Sale Date": data.get("events", {}).get("sale_date"),
        "Sale Amount": data.get("events", {}).get("sale_amount"),
    }
    return flat

def export_to_excel():
    print("📊 STARTING EXCEL EXPORT...")
    
    if not os.path.exists(JSON_PATH):
        print(f"❌ Error: {JSON_PATH} not found. Run the pipeline first!")
        return

    try:
        # 1. Load Data
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 2. Flatten Data
        # (If you had a list of cases, you would loop here. 
        # For now, we wrap the single dict in a list: [flat_data])
        flat_data = flatten_case_data(data)
        df = pd.DataFrame([flat_data])
        
        # 3. Save to Excel
        df.to_excel(EXCEL_PATH, index=False)
        print(f"✅ EXCEL SAVED: {os.path.basename(EXCEL_PATH)}")
        print(f"   Rows: {len(df)}")
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Export Failed: {e}")

if __name__ == "__main__":
    export_to_excel()