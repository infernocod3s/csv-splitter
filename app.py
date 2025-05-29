import streamlit as st
import pandas as pd
from pathlib import Path
import io
import base64

MAX_FILE_SIZE_MB = 200  # Set a safe file size limit

def get_download_link(df, filename, text):
    """Generate a download link for a dataframe"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'data:file/csv;base64,{b64}'
    return f'<a href="{href}" download="{filename}">{text}</a>'

def split_csv(uploaded_file, chunk_size=49999):
    """Split CSV file into chunks and return list of dataframes"""
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return [], 0
    total_rows = len(df)
    
    # Calculate number of chunks
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    
    # Split into chunks
    chunks = []
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        chunk = df.iloc[start_idx:end_idx]
        chunks.append(chunk)
    
    return chunks, total_rows

def main():
    st.set_page_config(page_title="CSV Splitter", page_icon="📊")
    
    st.title("CSV Splitter")
    st.write("Upload a CSV file to split it into smaller chunks of 49,999 records each.")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"File is too large ({file_size_mb:.2f} MB). Please upload a file smaller than {MAX_FILE_SIZE_MB} MB.")
            return
        try:
            # Split the CSV
            chunks, total_rows = split_csv(uploaded_file)
            
            if total_rows == 0:
                return
            
            # Display summary
            st.success(f"File successfully processed!")
            st.write(f"Total records: {total_rows}")
            st.write(f"Number of chunks: {len(chunks)}")
            
            # Display download buttons for each chunk
            st.subheader("Download Split Files")
            for i, chunk in enumerate(chunks, 1):
                filename = f"split_{i}.csv"
                st.markdown(get_download_link(chunk, filename, f"Download Split {i} ({len(chunk)} records)"), unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 