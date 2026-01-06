import os
import csv
import shutil

# --- CONFIGURATION ---
# Path to the folder containing the PDF files
source_folder = r"C:\WebF\24-12-2025 SIM SOA"

# Path to the CSV file
csv_path = r"C:\WebF\Temp25.csv"
# ---------------------

def main():
    # 1. Read the CSV data
    agreement_data = {}
    print("Reading CSV file...")
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Verify headers match expected columns
            # Expected: AGREEMENTNO, Case No, Agreement Type
            headers = reader.fieldnames
            print(f"Columns found: {headers}")
            
            for row in reader:
                # Store data in a dictionary for fast lookup
                # Key: Agreement No, Value: {Case No, Case Type}
                ag_no = row.get('AGREEMENTNO', '').strip()
                case_no = row.get('Case No', '').strip()
                case_type = row.get('Agreement Type', '').strip()
                
                if ag_no:
                    agreement_data[ag_no] = {
                        'Case No': case_no,
                        'Case Type': case_type
                    }
                    
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Sort agreement numbers by length (descending) to ensure we match the longest possible agreement number first
    sorted_agreements = sorted(agreement_data.keys(), key=len, reverse=True)

    print(f"Loaded {len(agreement_data)} agreements from CSV.")

    # 2. Process the files
    if not os.path.exists(source_folder):
        print(f"Error: Source folder not found at {source_folder}")
        return

    files_moved = 0
    files_skipped = 0

    print("\nProcessing files...")
    
    for filename in os.listdir(source_folder):
        file_path = os.path.join(source_folder, filename)
        
        # Skip if it's a directory
        if not os.path.isfile(file_path):
            continue
            
        # Only process PDF files (or you can remove this check to process all types)
        if not filename.lower().endswith('.pdf'):
            continue

        # Get the filename without extension
        name_stem, ext = os.path.splitext(filename)
        
        # 2a. Identify Document Type (SIM or SOA)
        doc_type = ""
        if name_stem.upper().endswith("SIM"):
            doc_type = "SIM"
        elif name_stem.upper().endswith("SOA"):
            doc_type = "SOA"
        
        if not doc_type:
            print(f"Skipping (Unknown Type): {filename}")
            files_skipped += 1
            continue
            
        # 2b. Identify Agreement Number
        matched_agreement = ""
        for ag_no in sorted_agreements:
            if name_stem.startswith(ag_no):
                matched_agreement = ag_no
                break
        
        if matched_agreement:
            details = agreement_data[matched_agreement]
            
            # 3. Construct new filename
            # Format: Case No_Agreement No_Case Type_Document Type.pdf
            new_filename = f"{details['Case No']}_{matched_agreement}_{details['Case Type']}_{doc_type}{ext}"
            
            # 4. Move to subfolder (SIM or SOA)
            target_folder = os.path.join(source_folder, doc_type)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            
            target_path = os.path.join(target_folder, new_filename)
            
            try:
                shutil.move(file_path, target_path)
                print(f"Moved: {filename} -> {doc_type}\\{new_filename}")
                files_moved += 1
            except Exception as e:
                print(f"Error moving {filename}: {e}")
        else:
            print(f"Skipping (No Agreement Match): {filename}")
            files_skipped += 1

    print(f"\nOperation Complete.")
    print(f"Files Moved: {files_moved}")
    print(f"Files Skipped: {files_skipped}")

if __name__ == "__main__":
    main()