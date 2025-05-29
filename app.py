import streamlit as st
import pandas as pd
from pathlib import Path
import io
import base64
import gc
import tempfile
import os

MAX_FILE_SIZE_MB = 200  # Set a safe file size limit

@st.cache_data
def get_download_link(csv_content, filename, text):
    """Generate a download link for CSV content"""
    try:
        b64 = base64.b64encode(csv_content.encode()).decode()
        href = f'data:file/csv;base64,{b64}'
        return f'<a href="{href}" download="{filename}">{text}</a>'
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return ""

def count_csv_rows(uploaded_file):
    """Count total rows in CSV without loading entire file into memory"""
    try:
        uploaded_file.seek(0)
        total_rows = sum(1 for line in uploaded_file) - 1  # Subtract header
        uploaded_file.seek(0)
        return total_rows
    except Exception as e:
        st.error(f"Error counting rows: {e}")
        return 0

def split_csv_memory_efficient(uploaded_file, chunk_size=49999):
    """Split CSV file using ultra-memory-efficient processing"""
    try:
        uploaded_file.seek(0)
        
        # Count total rows first
        total_rows = count_csv_rows(uploaded_file)
        if total_rows == 0:
            return [], 0
            
        num_output_files = (total_rows + chunk_size - 1) // chunk_size
        st.info(f"Processing {total_rows:,} rows into {num_output_files} files...")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Use very small read chunks to minimize memory usage
        read_chunk_size = min(5000, chunk_size // 10)  # Much smaller chunks
        
        output_chunks = []
        current_output_buffer = []
        current_output_size = 0
        rows_processed = 0
        output_file_number = 1
        
        # Get header first
        uploaded_file.seek(0)
        header = uploaded_file.readline().strip()
        
        try:
            # Process file in very small chunks
            for chunk_df in pd.read_csv(uploaded_file, chunksize=read_chunk_size):
                
                # Add rows to current output buffer
                chunk_rows = chunk_df.to_csv(index=False, header=False).strip().split('\n')
                
                for row in chunk_rows:
                    if row.strip():  # Skip empty rows
                        current_output_buffer.append(row)
                        current_output_size += 1
                        rows_processed += 1
                        
                        # When we reach the chunk size, save this output file
                        if current_output_size >= chunk_size:
                            # Create complete CSV content
                            csv_content = header + '\n' + '\n'.join(current_output_buffer)
                            output_chunks.append({
                                'content': csv_content,
                                'filename': f'split_{output_file_number}.csv',
                                'row_count': current_output_size
                            })
                            
                            # Reset for next file
                            current_output_buffer = []
                            current_output_size = 0
                            output_file_number += 1
                            
                            # Force garbage collection after each file
                            del csv_content
                            gc.collect()
                
                # Update progress
                progress = min(rows_processed / total_rows, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Processing: {rows_processed:,} / {total_rows:,} rows | Files created: {len(output_chunks)}")
                
                # Force garbage collection every few chunks
                del chunk_df
                gc.collect()
                
        except Exception as e:
            st.error(f"Error during processing: {e}")
            return [], 0
        
        # Handle remaining rows
        if current_output_buffer:
            csv_content = header + '\n' + '\n'.join(current_output_buffer)
            output_chunks.append({
                'content': csv_content,
                'filename': f'split_{output_file_number}.csv',
                'row_count': current_output_size
            })
            del csv_content
            gc.collect()
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ Processing complete! Created {len(output_chunks)} files.")
        
        return output_chunks, total_rows
        
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
        - The app uses memory-efficient processing to handle large files
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
                    # Split the CSV using memory-efficient processing
                    output_files, total_rows = split_csv_memory_efficient(uploaded_file)
                    
                    if total_rows == 0 or len(output_files) == 0:
                        st.error("❌ No data found or error processing file.")
                        return
                    
                    # Display summary
                    st.success("✅ File successfully processed!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Records", f"{total_rows:,}")
                    with col2:
                        st.metric("Split Files", len(output_files))
                    with col3:
                        avg_records = total_rows // len(output_files) if len(output_files) > 0 else 0
                        st.metric("Avg Records/File", f"{avg_records:,}")
                    
                    # Display download section
                    st.subheader("📥 Download All Split Files")
                    st.write("Click the links below to download each split file:")
                    
                    # Create download buttons for each file
                    for i, file_info in enumerate(output_files):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(
                                get_download_link(
                                    file_info['content'], 
                                    file_info['filename'], 
                                    f"📄 Download {file_info['filename']}"
                                ), 
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.write(f"({file_info['row_count']:,} records)")
                        
                        # Clean up this file's content from memory immediately
                        if i % 3 == 0:  # Garbage collect every few files
                            gc.collect()
                    
                    # Final cleanup
                    del output_files
                    gc.collect()
                    
                    st.success(f"✅ All {len(output_files)} files are ready for download!")
                    
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {e}")
                    st.write("Please try again with a smaller file or contact support if the issue persists.")
                    # Force cleanup on error
                    gc.collect()

if __name__ == "__main__":
    main() 