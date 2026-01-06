import requests
import os

# Define URL and Files
url = "http://localhost:8000/api/extract"

# Use the test PDF we know exists
pdf_path = r"C:\Users\SaibaskarP\HLF_Arbitration_Core\input_docs\PJJLAM00344_agreement.pdf"

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found")
    exit(1)

files = {
    "agreement_file": ("test_agreement.pdf", open(pdf_path, "rb"), "application/pdf"),
    "soa_file": ("test_soa.pdf", open(pdf_path, "rb"), "application/pdf"),
    # claim_path is optional
}

print("Suspending...")
try:
    resp = requests.post(url, files=files)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Request Failed: {e}")
