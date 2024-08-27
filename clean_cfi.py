import csv
import shutil
from datetime import datetime, timedelta
import os
from collections import defaultdict
from fuzzywuzzy import fuzz

def backup_file(file_path):
    """Create a backup of the given file."""
    backup_path = file_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d")}.csv')
    shutil.copy2(file_path, backup_path)
    print(f"Backup created: {backup_path}")

def sort_date_range_dict(data):
    def get_start_date(date_range):
        start_date_str = date_range.split('-')[:3]
        return datetime.strptime('-'.join(start_date_str), '%Y-%m-%d')

    sorted_dict = dict(sorted(data.items(), key=lambda x: get_start_date(x[0])))
    return sorted_dict

def validate_old_data(file_path):
    """Confirm that data is in bimonthly format, with correct columns"""
    pass

def validate_new_data(file_path):
    """Confirm that data hasn't changed warn user if it has"""
    pass

def extract_credible_fear_csv(file_path):
    """We expect the raw government data to have credible fear data in a specific format. We want to take the same steps we always take to identify it, and if the format has changed we still want to try to extract it but warn the user."""
    pass

def is_table_header(row):
    """Check if the given row is a table header."""
    if not row:
        return False
    
    # Check if the first cell contains text and the rest are empty
    if row[0].strip() and all(cell.strip() == '' for cell in row[1:]):
        return True
    
    return False

def id_all_cfi_table(rows):
    for i, row in enumerate(rows):
        if is_table_header(row):
            target = "All Credible Fear Cases"
            # Use fuzzy matching to compare the first cell with the target string
            similarity = fuzz.partial_ratio(row[0].lower(), target.lower())
            # If the similarity is above 80%, consider it a match
            if similarity > 80:
                return i
    return None

def convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return None

def extract_credible_fear_data(file_path):
    """Extract All Credible Fear Cases data from raw government file."""
    data = defaultdict(list)
    categories = ['Case Receipts', 'All Decisions', 'Fear Established_Persecution (Y)', 
                  'Fear Established_Torture (Y)', 'Fear Not Established (N)', 'Administratively Closed']
    
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            csv_reader = csv.reader(f)
            # Skip the first two rows
            next(csv_reader)
            next(csv_reader)
            
            # Read the next 8 rows
            rows = [row for row in csv_reader]
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader)
            next(csv_reader)
            rows = [next(csv_reader) for _ in range(8)]
    

    begin_cfi = id_all_cfi_table(rows)
    
    if begin_cfi is not None:
        cfi_to_end = rows[begin_cfi+1:]
        cfi_table = []
        for row in cfi_to_end:
            if not is_table_header(row):  # We pass a single row as a list
                cfi_table.append(row)
            else:
                break
    else:
        print("Could not find the 'All Credible Fear Cases' table.")
        return []

    print("Loaded cfi table...")

    # Extract dates and combine them
    _from = [row for row in cfi_table if row[0].strip().upper() == 'FROM'][0]
    _to = [row for row in cfi_table if row[0].strip().upper() == 'TO'][0]
    date_ranges = [f"{start.strip()}-{end.strip()}" for start, end in zip(_from, _to)]

    print("Extracted dates...")

    # Extract data for each category
    for row in cfi_table:
        if row[0].strip() in categories:
            data[row[0].strip()] = [convert_to_int(value.replace(',', '').strip()) for value in row]

    print("Extracted for each category...")

    # Combine the data
    for key, value in data.items():
        data[key] = dict(zip(date_ranges, value))

    print("Combined...")
    
    # Reformat the data here
    result = {}
    for date_range in data['Case Receipts'].keys():
        if date_range not in ['From-To', '-']:
            try:
                fear_established = data['Fear Established_Persecution (Y)'][date_range] + data['Fear Established_Torture (Y)'][date_range]
                start_date, end_date = date_range.split('-')
                formatted_start = datetime.strptime(start_date.strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
                formatted_end = datetime.strptime(end_date.strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
                str_date_range = f"{formatted_start}-{formatted_end}"
                row = {
                    'Case Receipts': f"{data['Case Receipts'][date_range]:,}",
                    'All Decisions': f"{data['All Decisions'][date_range]:,}",
                    'Fear Established (Y)': f"{fear_established:,}",
                    'Fear Not Established (N)': f"{data['Fear Not Established (N)'][date_range]:,}",
                    'Closings': f"{data['Administratively Closed'][date_range]:,}"
                }
                result[str_date_range] = row
            except ValueError as e:
                print(f"Error processing date range: {date_range}. Error: {str(e)}")
                continue

    return result



def update_bimonthly_data(bimonthly_file, new_data):
    """Update bimonthly data with new data from government file."""
    with open(bimonthly_file, 'r') as f:
        reader = csv.DictReader(f)
        bimonthly_data = list(reader)

    bimonthly_dict = {}
    for row in bimonthly_data:
        date_range = row.pop('Date Range')
        bimonthly_dict[date_range] = row

    bimonthly_dict.update(new_data)
    bimonthly_data = sort_date_range_dict(bimonthly_dict)

def main():
    # Backup existing files
    backup_file('bimonthly.csv')
    
    # Get the most recent government file
    gov_files = [f for f in os.listdir('gov-data') if f.startswith('Congressional-Semi-Monthly')]
    latest_gov_file = os.path.join('gov-data', max(gov_files, key=lambda f: os.path.getctime(os.path.join('gov-data', f))))
    
    # Extract new data from the most recent government file
    new_data = extract_credible_fear_data(latest_gov_file)
    
    # Update bimonthly data
    updated_bimonthly = update_bimonthly_data('bimonthly.csv', new_data)
    
    # Save updated bimonthly data
    # with open('bimonthly.csv', 'w', newline='') as f:
    #     writer = csv.DictWriter(f, fieldnames=['Date Range', 'Case Receipts', 'All Decisions', 'Fear Established (Y)', 'Fear Not Established (N)', 'Closings'])
    #     writer.writeheader()
    #     writer.writerows(updated_bimonthly)
    # print("Bimonthly data updated and saved.")
    
    # Generate and save monthly data
    # monthly_data = generate_monthly_data(updated_bimonthly)
    # with open('monthly.csv', 'w', newline='') as f:
    #     writer = csv.DictWriter(f, fieldnames=['Month', 'Case Receipts', 'All Decisions', 'Fear Established (Y)', 'Fear Not Established (N)', 'Closings'])
    #     writer.writeheader()
    #     writer.writerows(monthly_data)
    # print("Monthly data generated and saved.")

if __name__ == "__main__":
    main()
