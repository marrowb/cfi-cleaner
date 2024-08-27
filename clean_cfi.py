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

def is_table_header(row):
    """Check if the given row is a table header."""
    if not row:
        return False
    return row[0].strip() and all(cell.strip() == '' for cell in row[1:])

def id_all_cfi_table(rows):
    """Identify the 'All Credible Fear Cases' table."""
    for i, row in enumerate(rows):
        if is_table_header(row):
            target = "All Credible Fear Cases"
            similarity = fuzz.partial_ratio(row[0].lower(), target.lower())
            if similarity > 80:
                return i
    return None

def convert_to_int(value):
    """Convert a string to an integer, return None if not possible."""
    try:
        return int(value.replace(',', '').strip())
    except ValueError:
        return None

def read_csv_file(file_path):
    """Read CSV file and return rows."""
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            csv_reader = csv.reader(f)
            return [row for row in csv_reader]
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            return [row for row in csv_reader]

def extract_cfi_table(rows):
    """Extract the CFI table from rows."""
    begin_cfi = id_all_cfi_table(rows)
    if begin_cfi is None:
        print("Could not find the 'All Credible Fear Cases' table.")
        return []
    
    cfi_to_end = rows[begin_cfi+1:]
    cfi_table = []
    for row in cfi_to_end:
        if not is_table_header(row):
            cfi_table.append(row)
        else:
            break
    return cfi_table

def extract_date_ranges(cfi_table):
    """Extract date ranges from CFI table."""
    _from = [row for row in cfi_table if row[0].strip().upper() == 'FROM'][0]
    _to = [row for row in cfi_table if row[0].strip().upper() == 'TO'][0]
    return [f"{start.strip()}-{end.strip()}" for start, end in zip(_from, _to)]

def extract_category_data(cfi_table, categories):
    """Extract data for each category."""
    data = defaultdict(list)
    for row in cfi_table:
        if row[0].strip() in categories:
            data[row[0].strip()] = [convert_to_int(value) for value in row]
    return data

def combine_data(data, date_ranges):
    """Combine data with date ranges."""
    for key, value in data.items():
        data[key] = dict(zip(date_ranges, value))
    return data

def format_date(date_str):
    """Format date string."""
    return datetime.strptime(date_str.strip(), '%m/%d/%Y').strftime('%Y-%m-%d')

def reformat_data(data):
    """Reformat the data."""
    result = {}
    for date_range in data['Case Receipts'].keys():
        if date_range not in ['From-To', '-']:
            try:
                fear_established = data['Fear Established_Persecution (Y)'][date_range] + data['Fear Established_Torture (Y)'][date_range]
                start_date, end_date = date_range.split('-')
                str_date_range = f"{format_date(start_date)}-{format_date(end_date)}"
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
    return result

def extract_credible_fear_data(file_path):
    """Extract All Credible Fear Cases data from raw government file."""
    categories = ['Case Receipts', 'All Decisions', 'Fear Established_Persecution (Y)', 
                  'Fear Established_Torture (Y)', 'Fear Not Established (N)', 'Administratively Closed']
    
    rows = read_csv_file(file_path)
    cfi_table = extract_cfi_table(rows)
    
    if not cfi_table:
        return []

    print("Loaded cfi table...")
    
    date_ranges = extract_date_ranges(cfi_table)
    print("Extracted dates...")
    
    data = extract_category_data(cfi_table, categories)
    print("Extracted for each category...")
    
    combined_data = combine_data(data, date_ranges)
    print("Combined...")
    
    result = reformat_data(combined_data)
    
    return result

def load_truth(truth_file):
    with open(truth_file, 'r') as f:
        r = csv.reader(f)
        rows = [row for row in r]
        row_dict = {}
        headers = []
        for i, row in enumerate(rows):
            if i == 0:
                headers = row
            date_range = row.pop(0)
            row_dict[date_range] = dict(zip(headers[0:],row))
    return row_dict



def main():
    # Backup existing files
    #backup_file('bimonthly.csv')
    
    
    # Process files in order from oldest to newest
    data = load_truth()


    if data.get('Date Range'):
        header = ['Date Range'] + list(data.pop('Date Range').keys())
    
    sorted_data = sort_date_range_dict(data)

    # Write this data to a csv
    output_file = 'bimonthly.csv'

    flat = []
    for k,v in sorted_data.items():
        row = [k]
        row.extend(val for val in v.values())
        flat.append(row)


    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for row in flat:
            writer.writerow(row)

    print(f"Data has been written to {output_file}")

    
if __name__ == "__main__":
    main()
