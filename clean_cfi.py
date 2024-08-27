import pandas as pd
import shutil
from datetime import datetime, timedelta
import os

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
    try:
        df = pd.read_csv(file_path, encoding='latin-1', skiprows=2)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='utf-8', skiprows=2)
    
    credible_fear_data = df.iloc[:8]
    
    # Extract dates from the first two rows
    from_dates = credible_fear_data.iloc[0, 2:].values
    to_dates = credible_fear_data.iloc[1, 2:].values
    
    # Combine from and to dates
    date_ranges = [f"{start}-{end}" for start, end in zip(from_dates, to_dates)]
    
    # Extract data for each category
    categories = ['Case Receipts', 'All Decisions', 'Fear Established_Persecution (Y)', 
                  'Fear Established_Torture (Y)', 'Fear Not Established (N)', 'Administratively Closed']
    
    data = {}
    for i, category in enumerate(categories, start=2):
        data[category] = credible_fear_data.iloc[i, 2:].values
    
    # Create a new dataframe with the extracted data
    new_df = pd.DataFrame({
        'Date Range': date_ranges,
        **data
    })
    
    # Convert date range to start date
    new_df['Date Range'] = pd.to_datetime(new_df['Date Range'].str.split('-').str[0].str.strip(), format='%m/%d/%Y')
    
    # Convert string numbers to numeric, handling commas
    for col in categories:
        new_df[col] = pd.to_numeric(new_df[col].str.replace(',', ''), errors='coerce')

    new_df['Fear Established (Y)'] = new_df['Fear Established_Persecution (Y)'] + new_df['Fear Established_Torture (Y)']
    new_df = new_df.rename(columns={'Administratively Closed': 'Closings'})
    
    # Select and order the required columns
    final_columns = ['Date Range', 'Case Receipts', 'All Decisions', 'Fear Established (Y)', 'Fear Not Established (N)', 'Closings']
    new_df = new_df[final_columns]
    return new_df
def update_bimonthly_data(bimonthly_file, new_data):
    """Update bimonthly data with new data from government file."""
    df_bimonthly = pd.read_csv(bimonthly_file)
    df_bimonthly['Date Range'] = pd.to_datetime(df_bimonthly['Date Range'].str.split('-').str[0])
    
    # Determine the cutoff date (one year before the latest date in new_data)
    cutoff_date = new_data['Date Range'].max() - timedelta(days=365)
    
    # Remove data from the past year and append new data
    df_bimonthly = df_bimonthly[df_bimonthly['Date Range'] < cutoff_date]
    df_bimonthly = pd.concat([df_bimonthly, new_data]).sort_values('Date Range', ascending=False).reset_index(drop=True)
    
    # Convert 'Date Range' back to string format
    df_bimonthly['Date Range'] = df_bimonthly['Date Range'].dt.strftime('%Y-%m-%d') + '-' + (df_bimonthly['Date Range'] + pd.Timedelta(days=14)).dt.strftime('%Y-%m-%d')
    
    return df_bimonthly

def generate_monthly_data(bimonthly_data):
    """Generate monthly data from bimonthly data."""
    df = bimonthly_data.copy()
    df['Date Range'] = pd.to_datetime(df['Date Range'].str.split('-').str[0])
    df['Month'] = df['Date Range'].dt.to_period('M')
    
    monthly_data = df.groupby('Month').agg({
        'Case Receipts': 'sum',
        'All Decisions': 'sum',
        'Fear Established_Persecution (Y)': 'sum',
        'Fear Established_Torture (Y)': 'sum',
        'Fear Not Established (N)': 'sum',
        'Administratively Closed': 'sum'
    }).reset_index()
    
    monthly_data['Fear Established (Y)'] = monthly_data['Fear Established_Persecution (Y)'] + monthly_data['Fear Established_Torture (Y)']
    monthly_data = monthly_data.drop(['Fear Established_Persecution (Y)', 'Fear Established_Torture (Y)'], axis=1)
    
    monthly_data['Month'] = monthly_data['Month'].dt.strftime('%Y-%m')
    
    return monthly_data

def main():
    # Backup existing files
    backup_file('bimonthly.csv')
    backup_file('monthly.csv')
    
    # Get the most recent government file
    gov_files = [f for f in os.listdir() if f.startswith('Congressional-Semi-Monthly')]
    latest_gov_file = max(gov_files, key=os.path.getctime)
    
    # Extract new data from the most recent government file
    new_data = extract_credible_fear_data(latest_gov_file)
    
    # Update bimonthly data
    updated_bimonthly = update_bimonthly_data('bimonthly.csv', new_data)
    updated_bimonthly.to_csv('bimonthly.csv', index=False)
    print("Bimonthly data updated and saved.")
    
    # Generate and save monthly data
    monthly_data = generate_monthly_data(updated_bimonthly)
    monthly_data.to_csv('monthly.csv', index=False)
    print("Monthly data generated and saved.")

if __name__ == "__main__":
    main()
