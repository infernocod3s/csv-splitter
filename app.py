import streamlit as st
import pandas as pd
from pathlib import Path
import io
import base64
import gc

MAX_FILE_SIZE_MB = 200  # Set a safe file size limit

def get_download_link(df, filename, text):
    """Generate a download link for a dataframe"""
    try:
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'data:file/csv;base64,{b64}'
        return f'<a href="{href}" download="{filename}">{text}</a>'
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return ""

def count_csv_rows(uploaded_file):
    """Count total rows in CSV without loading entire file into memory"""
    try:
        uploaded_file.seek(0)  # Reset file pointer
        total_rows = sum(1 for line in uploaded_file) - 1  # Subtract header
        uploaded_file.seek(0)  # Reset file pointer again
        return total_rows
    except Exception as e:
        st.error(f"Error counting rows: {e}")
        return 0

def split_csv_chunked(uploaded_file, chunk_size=49999):
    """Split CSV file into chunks using chunked reading for memory efficiency"""
    try:
        uploaded_file.seek(0)  # Reset file pointer
        
        # Count total rows first
        total_rows = count_csv_rows(uploaded_file)
        if total_rows == 0:
            return [], 0
            
        # Calculate number of output chunks
        num_output_chunks = (total_rows + chunk_size - 1) // chunk_size
        
        st.info(f"Processing {total_rows:,} rows into {num_output_chunks} files...")
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        chunks = []
        rows_processed = 0
        
        # Read CSV in smaller chunks to manage memory
        read_chunk_size = min(chunk_size, 10000)  # Read smaller chunks to manage memory
        
        current_chunk = []
        chunk_number = 0
        
        try:
            for i, df_chunk in enumerate(pd.read_csv(uploaded_file, chunksize=read_chunk_size)):
                current_chunk.append(df_chunk)
                rows_processed += len(df_chunk)
                
                # Update progress
                progress = min(rows_processed / total_rows, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Processing: {rows_processed:,} / {total_rows:,} rows")
                
                # Check if we have enough rows for a full output chunk
                current_total_rows = sum(len(chunk) for chunk in current_chunk)
                
                if current_total_rows >= chunk_size or rows_processed >= total_rows:
                    # Combine current chunks
                    combined_chunk = pd.concat(current_chunk, ignore_index=True)
                    
                    # If we have more than chunk_size rows, split it
                    while len(combined_chunk) >= chunk_size:
                        chunk_to_save = combined_chunk.iloc[:chunk_size].copy()
                        chunks.append(chunk_to_save)
                        combined_chunk = combined_chunk.iloc[chunk_size:].reset_index(drop=True)
                        
                        # Force garbage collection
                        del chunk_to_save
                        gc.collect()
                    
                    # Keep remaining rows for next iteration
                    current_chunk = [combined_chunk] if len(combined_chunk) > 0 else []
                
                # Force garbage collection periodically
                if i % 5 == 0:
                    gc.collect()
                    
        except Exception as e:
            st.error(f"Error during chunked reading: {e}")
            return [], 0
        
        # Handle any remaining rows
        if current_chunk:
            remaining_chunk = pd.concat(current_chunk, ignore_index=True)
            if len(remaining_chunk) > 0:
                chunks.append(remaining_chunk)
        
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")
        
        # Force final garbage collection
        gc.collect()
        
        return chunks, total_rows
        
    except Exception as e:
        st.error(f"Error processing CSV: {e}")
        return [], 0

def main():
    st.set_page_config(
        page_title="CSV Splitter", 
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 CSV Splitter")
    st.write("Upload a CSV file to split it into smaller chunks of 49,999 records each.")
    st.write("**Maximum file size:** 200 MB")
    
    # Add some tips
    with st.expander("💡 Tips for best results"):
        st.write("""
        - Ensure your CSV file is properly formatted
        - Larger files may take longer to process
        - Each split file will contain up to 49,999 rows
        - Original data structure and content will be preserved
        """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file", 
        type="csv",
        help="Upload a CSV file to split into smaller chunks"
    )
    
    if uploaded_file is not None:
        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        st.info(f"📁 File size: {file_size_mb:.2f} MB")
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"❌ File is too large ({file_size_mb:.2f} MB). Please upload a file smaller than {MAX_FILE_SIZE_MB} MB.")
            return
        
        # Process button
        if st.button("🔄 Split CSV File", type="primary"):
            with st.spinner("Processing your file..."):
                try:
                    # Split the CSV using chunked processing
                    chunks, total_rows = split_csv_chunked(uploaded_file)
                    
                    if total_rows == 0 or len(chunks) == 0:
                        st.error("❌ No data found or error processing file.")
                        return
                    
                    # Display summary
                    st.success("✅ File successfully processed!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Records", f"{total_rows:,}")
                    with col2:
                        st.metric("Split Files", len(chunks))
                    with col3:
                        avg_records = total_rows // len(chunks) if len(chunks) > 0 else 0
                        st.metric("Avg Records/File", f"{avg_records:,}")
                    
                    # Display download section
                    st.subheader("📥 Download Split Files")
                    st.write("Click the links below to download each split file:")
                    
                    # Create download buttons in columns for better layout
                    cols = st.columns(3)
                    for i, chunk in enumerate(chunks):
                        col_idx = i % 3
                        with cols[col_idx]:
                            filename = f"split_{i+1}.csv"
                            records_count = len(chunk)
                            st.markdown(
                                get_download_link(
                                    chunk, 
                                    filename, 
                                    f"📄 Split {i+1}<br>({records_count:,} records)"
                                ), 
                                unsafe_allow_html=True
                            )
                            st.write("")  # Add some spacing
                    
                    # Cleanup
                    del chunks
                    gc.collect()
                    
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {e}")
                    st.write("Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    main() 