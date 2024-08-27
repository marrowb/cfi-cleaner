import streamlit as st
import pandas as pd
from clean_cfi import extract_credible_fear_data, load_truth, sort_date_range_dict

def update_truth_with_new_data(truth_data, new_data):
    updated_data = truth_data.copy()
    for date_range, values in new_data.items():
        if date_range in updated_data:
            updated_data[date_range].update(values)
        else:
            updated_data[date_range] = values
    return updated_data

def main():
    st.title("CFI Data Update Tool")

    # File upload for new government CFI table
    gov_file = st.file_uploader(
        "Upload new government CFI table (CSV)",
        type="csv",
        help="Upload the latest CFI Data file from the government. These are available at: https://www.uscis.gov/tools/reports-and-studies/semi-monthly-credible-fear-and-reasonable-fear-receipts-and-decisions"
    )

    # File upload for CFI truth file
    truth_file = st.file_uploader(
        "Upload CFI truth file (CSV)",
        type="csv",
        help="Upload the CFI truth file. This file contains the data you know is correct and want to update with the new government data."
    )

    if gov_file and truth_file:
        # Process the uploaded files
        new_data = extract_credible_fear_data(gov_file)
        truth_data = load_truth(truth_file)

        # Update truth data with new data
        updated_data = update_truth_with_new_data(truth_data, new_data)

        # Sort the updated data
        sorted_data = sort_date_range_dict(updated_data)

        # Convert to DataFrame for display
        df = pd.DataFrame.from_dict(sorted_data, orient='index')
        df.reset_index(inplace=True)
        df.columns = ['Date Range'] + list(df.columns[1:])

        st.subheader("Updated CFI Data")
        st.dataframe(df)

        # Option to download updated data
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download updated CFI data as CSV",
            data=csv,
            file_name="updated_cfi_data.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
