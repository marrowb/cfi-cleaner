import csv
import shutil
from datetime import datetime, timedelta
import os
from collections import defaultdict

def backup_file(file_path):
    """Create a backup of the given file."""
    backup_path = file_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d")}.csv')
    shutil.copy2(file_path, backup_path)
    print(f"Backup created: {backup_path}")

def validate_old_data(file_path):
    """Confirm that data is in bimonthly format, with correct columns"""
    pass

def validate_new_data(file_path):
    """Confirm that data hasn't changed warn user if it has"""
    pass

def extract_credible_fear_csv(file_path):
    """We expect the raw government data to have credible fear data in a specific format. We want to take the same steps we always take to identify it, and if the format has changed we still want to try to extract it but warn the user."""
    pass

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
            rows = [next(csv_reader) for _ in range(8)]
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader)
            next(csv_reader)
            rows = [next(csv_reader) for _ in range(8)]

    # Extract dates and combine them
    from_dates = rows[0][2:]
    to_dates = rows[1][2:]
    date_ranges = [f"{start.strip()}-{end.strip()}" for start, end in zip(from_dates, to_dates)]

    # Extract data for each category
    for i, category in enumerate(categories, start=2):
        data[category] = [value.replace(',', '') for value in rows[i][2:]]

    # Combine the data
    result = []
    for i in range(len(date_ranges)):
        row = {'Date Range': datetime.strptime(date_ranges[i].split('-')[0].strip(), '%m/%d/%Y')}
        for category in categories:
            row[category] = int(data[category][i]) if data[category][i] else 0
        row['Fear Established (Y)'] = row['Fear Established_Persecution (Y)'] + row['Fear Established_Torture (Y)']
        row['Closings'] = row.pop('Administratively Closed')
        result.append(row)

    # Sort the result by date in descending order
    result.sort(key=lambda x: x['Date Range'], reverse=True)

    # Select and order the required columns
    final_columns = ['Date Range', 'Case Receipts', 'All Decisions', 'Fear Established (Y)', 'Fear Not Established (N)', 'Closings']
    return [{col: row[col] for col in final_columns} for row in result]
def update_bimonthly_data(bimonthly_file, new_data):
    """Update bimonthly data with new data from government file."""
    with open(bimonthly_file, 'r') as f:
        reader = csv.DictReader(f)
        bimonthly_data = list(reader)

    for row in bimonthly_data:
        row['Date Range'] = datetime.strptime(row['Date Range'].split('-')[0], '%Y-%m-%d')
        for key in row:
            if key != 'Date Range':
                row[key] = int(row[key])

    # Determine the cutoff date (one year before the latest date in new_data)
    cutoff_date = max(row['Date Range'] for row in new_data) - timedelta(days=365)

    # Remove data from the past year and append new data
    bimonthly_data = [row for row in bimonthly_data if row['Date Range'] < cutoff_date]
    bimonthly_data.extend(new_data)

    # Sort the combined data
    bimonthly_data.sort(key=lambda x: x['Date Range'], reverse=True)

    # Convert 'Date Range' back to string format
    for row in bimonthly_data:
        start_date = row['Date Range']
        end_date = start_date + timedelta(days=14)
        row['Date Range'] = f"{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"

    return bimonthly_data

def generate_monthly_data(bimonthly_data):
    """Generate monthly data from bimonthly data."""
    monthly_data = defaultdict(lambda: defaultdict(int))

    for row in bimonthly_data:
        date = datetime.strptime(row['Date Range'].split('-')[0], '%Y-%m-%d')
        month = date.strftime('%Y-%m')
        
        for key in row:
            if key != 'Date Range':
                monthly_data[month][key] += int(row[key])

    result = []
    for month, data in sorted(monthly_data.items(), reverse=True):
        result.append({
            'Month': month,
            'Case Receipts': data['Case Receipts'],
            'All Decisions': data['All Decisions'],
            'Fear Established (Y)': data['Fear Established (Y)'],
            'Fear Not Established (N)': data['Fear Not Established (N)'],
            'Closings': data['Closings']
        })

    return result

def main():
    # Backup existing files
    backup_file('bimonthly.csv')
    backup_file('monthly.csv')
    
    # Get the most recent government file
    gov_files = [f for f in os.listdir('gov-data') if f.startswith('Congressional-Semi-Monthly')]
    latest_gov_file = os.path.join('gov-data', max(gov_files, key=lambda f: os.path.getctime(os.path.join('gov-data', f))))
    
    # Extract new data from the most recent government file
    new_data = extract_credible_fear_data(latest_gov_file)
    
    # Update bimonthly data
    updated_bimonthly = update_bimonthly_data('bimonthly.csv', new_data)
    
    # Save updated bimonthly data
    with open('bimonthly.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Date Range', 'Case Receipts', 'All Decisions', 'Fear Established (Y)', 'Fear Not Established (N)', 'Closings'])
        writer.writeheader()
        writer.writerows(updated_bimonthly)
    print("Bimonthly data updated and saved.")
    
    # Generate and save monthly data
    monthly_data = generate_monthly_data(updated_bimonthly)
    with open('monthly.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Month', 'Case Receipts', 'All Decisions', 'Fear Established (Y)', 'Fear Not Established (N)', 'Closings'])
        writer.writeheader()
        writer.writerows(monthly_data)
    print("Monthly data generated and saved.")

if __name__ == "__main__":
    main()
