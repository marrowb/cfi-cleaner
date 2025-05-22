# CFI Data Update Tool

This Streamlit application provides a user-friendly interface to update a curated "truth" dataset of Credible Fear Interview (CFI) statistics with the latest data published by U.S. Citizenship and Immigration Services (USCIS). It intelligently parses the often inconsistently formatted government CSV files, extracts the relevant information, and merges it with your existing data.

## Overview

The USCIS publishes semi-monthly reports on Credible Fear and Reasonable Fear receipts and decisions. These reports are typically in CSV format but can have formatting inconsistencies, making direct use challenging for ongoing analysis. This tool aims to:

1.  **Load** a new government-provided CFI data CSV.
2.  **Load** an existing "truth file" CSV, which contains your curated and validated CFI data.
3.  **Process** the government CSV to extract data specifically from the "All Credible Fear Cases" table.
4.  **Clean** and **standardize** the extracted data, including date formats and combining relevant fear-established categories.
5.  **Update** your truth data with the new information from the government file. If date ranges overlap, the new government data for that period will be used.
6.  **Display** the updated, sorted dataset.
7.  Allow you to **download** the updated dataset as a new CSV file.

## Features

*   **User-friendly Interface:** Built with Streamlit for easy file uploads and interaction.
*   **Robust Parsing:** Handles variations in government CSV formatting using fuzzy matching to locate the correct data table.
*   **Data Cleaning:** Converts data to appropriate types and standardizes date range formats (e.g., `MM/DD/YYYY` to `YYYY-MM-DD`).
*   **Targeted Extraction:** Focuses on the "All Credible Fear Cases" section of the government report.
*   **Intelligent Merging:** Combines new data with existing truth data, updating existing entries and adding new ones.
*   **Data Aggregation:** Combines "Fear Established_Persecution (Y)" and "Fear Established_Torture (Y)" from the government report into a single "Fear Established (Y)" column for consistency with the truth file format.
*   **Sorted Output:** Presents the final merged data sorted by date range.
*   **Downloadable Results:** Allows users to download the updated CFI data as a CSV.

## How It Works

1.  **File Uploads (`app.py`):**
    *   The user uploads the latest government CFI data CSV.
    *   The user uploads their current "CFI truth file" CSV.

2.  **Government Data Processing (`clean_cfi.py`):**
    *   The `extract_credible_fear_data` function is called.
    *   It reads the government CSV (attempting `latin-1` encoding first, then `utf-8`).
    *   `id_all_cfi_table` uses `fuzzywuzzy` to find the header row for "All Credible Fear Cases", accommodating minor text variations.
    *   `extract_cfi_table` isolates the rows belonging to this specific table.
    *   `extract_date_ranges` and `extract_category_data` pull out the relevant date columns and data rows for categories like 'Case Receipts', 'All Decisions', 'Fear Established_Persecution (Y)', 'Fear Established_Torture (Y)', 'Fear Not Established (N)', and 'Administratively Closed'.
    *   `reformat_data` then transforms this extracted data:
        *   Converts date strings (e.g., `MM/DD/YYYY`) into a standard `YYYY-MM-DD - YYYY-MM-DD` format for the date range.
        *   Sums 'Fear Established_Persecution (Y)' and 'Fear Established_Torture (Y)' into a single 'Fear Established (Y)' value.
        *   Formats numerical values with commas.
        *   Returns a dictionary where keys are date ranges and values are dictionaries of the metrics.

3.  **Truth Data Loading (`clean_cfi.py`):**
    *   The `load_truth` function reads the user's truth file CSV into a similar dictionary structure.

4.  **Data Merging and Display (`app.py`):**
    *   `update_truth_with_new_data` merges the processed government data into the truth data. For any given date range, if it exists in the new government data, its values will update or replace those in the truth data. New date ranges from the government data are added.
    *   `sort_date_range_dict` sorts the combined data chronologically by the start date of each period.
    *   The sorted data is converted to a Pandas DataFrame and displayed in the Streamlit app.
    *   A download button is provided to save the updated DataFrame as `updated_cfi_data.csv`.

## Prerequisites

*   Python 3.7+
*   Streamlit
*   Pandas
*   fuzzywuzzy

## Installation

1.  **Clone the repository (if applicable) or download the project files.**
2.  **Navigate to the project directory:**
    ```bash
    cd path/to/your/project
    ```
3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    pip install streamlit pandas # If not already in requirements.txt
    ```
    (Note: `requirements.txt` provided only lists `fuzzywuzzy`. `streamlit` and `pandas` are essential imports in `app.py`.)

## Usage

1.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```
2.  **Open your web browser** and go to the local URL provided by Streamlit (usually `http://localhost:8501`).
3.  **Upload Files:**
    *   Use the first file uploader to upload the **new government CFI table CSV**. You can find these reports on the USCIS website: [Semi-Monthly Credible Fear and Reasonable Fear Receipts and Decisions](https://www.uscis.gov/tools/reports-and-studies/semi-monthly-credible-fear-and-reasonable-fear-receipts-and-decisions)
    *   Use the second file uploader to upload your current **CFI truth file CSV** (e.g., `cfi_truth.csv`).
4.  **View and Download:**
    *   Once both files are uploaded, the application will process them and display the "Updated CFI Data" table.
    *   Click the "Download updated CFI data as CSV" button to save the results. The default filename is `updated_cfi_data.csv`.

## Input File Formats

### 1. Government CFI Table (CSV)

*   This is the raw CSV file downloaded directly from the USCIS website.
*   The tool specifically looks for a table titled "All Credible Fear Cases" (or a close fuzzy match).
*   Example: `gov-data/Congressional-Semi-Monthly CF&RF -Report-6-16-23-to 6-30-24.csv`

### 2. CFI Truth File (CSV)

*   This is your master file containing curated CFI data.
*   It must be a CSV file with the following header row and data structure:
    `Date Range,Case Receipts,All Decisions,Fear Established (Y),Fear Not Established (N),Closings`
*   **Date Range Format:** `YYYY-MM-DD-YYYY-MM-DD` (e.g., `2023-01-01-2023-01-15`)
*   Numerical values should be plain integers (e.g., `4276`, not `"4,276"`).
*   Example: `cfi_truth.csv`

```csv
Date Range,Case Receipts,All Decisions,Fear Established (Y),Fear Not Established (N),Closings
2019-01-01-2019-01-15,4276,3105,2305,379,421
2019-01-16-2019-01-31,5582,4379,3501,393,485
...
```

## Output File

The application allows you to download an `updated_cfi_data.csv` file. This file will have the same format as the input "CFI Truth File", containing the merged and sorted data with numerical values formatted with commas for readability (though they are processed as integers).

## File Structure

```
.
├── app.py                        # Main Streamlit application script
├── clean_cfi.py                  # Module for cleaning and extracting CFI data
├── cfi_truth.csv                 # Example/template for your curated CFI data
├── requirements.txt              # Python dependencies
├── gov-data/                     # Recommended directory for storing downloaded government reports
│   └── ... (e.g., Congressional-Semi-Monthly CF&RF -Report-6-16-23-to 6-30-24.csv)
├── backups/                      # (As seen in provided files) Directory for backups
│   └── mpi_last_edit.csv
└── README.md                     # This file
```

## Contributing

Feel free to fork the project, make improvements, and submit pull requests. If you encounter any issues or have suggestions, please open an issue in the repository.
