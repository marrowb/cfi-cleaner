import csv
import io
from datetime import datetime
from collections import defaultdict
from fuzzywuzzy import fuzz

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

def read_csv_file(file):
    """Read CSV file and return rows."""
    try:
        # Try reading with latin-1 encoding first
        csv_reader = csv.reader(io.StringIO(file.getvalue().decode('latin-1')))
        return [row for row in csv_reader]
    except UnicodeDecodeError:
        # If latin-1 fails, fall back to utf-8
        csv_reader = csv.reader(io.StringIO(file.getvalue().decode('utf-8')))
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

def extract_credible_fear_data(file):
    """Extract All Credible Fear Cases data from raw government file."""
    categories = ['Case Receipts', 'All Decisions', 'Fear Established_Persecution (Y)', 
                  'Fear Established_Torture (Y)', 'Fear Not Established (N)', 'Administratively Closed']
    
    rows = read_csv_file(file)
    cfi_table = extract_cfi_table(rows)
    
    if not cfi_table:
        return {}

    date_ranges = extract_date_ranges(cfi_table)
    data = extract_category_data(cfi_table, categories)
    combined_data = combine_data(data, date_ranges)
    result = reformat_data(combined_data)
    
    return result

def load_truth(truth_file):
    csv_reader = csv.reader(io.StringIO(truth_file.getvalue().decode('utf-8')))
    rows = [row for row in csv_reader]
    row_dict = {}
    headers = []
    for i, row in enumerate(rows):
        if i == 0:
            headers = row
        else:
            date_range = row.pop(0)
            row_dict[date_range] = dict(zip(headers[1:], row))
    return row_dict
