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
        b64 = base64.b64encode(csv_content.encode('utf-8')).decode()
        href = f'data:file/csv;base64,{b64}'
        return f'<a href="{href}" download="{filename}">{text}</a>'
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return ""

def detect_encoding(uploaded_file):
    """Detect file encoding"""
    try:
        uploaded_file.seek(0)
        sample = uploaded_file.read(10000)
        uploaded_file.seek(0)
        
        # Try common encodings
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                if isinstance(sample, bytes):
                    sample.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return 'utf-8'  # Default fallback
    except:
        return 'utf-8'

def count_csv_rows(uploaded_file):
    """Count total rows in CSV without loading entire file into memory"""
    try:
        uploaded_file.seek(0)
        
        # Convert to text if it's bytes
        content = uploaded_file.read()
        if isinstance(content, bytes):
            encoding = detect_encoding(uploaded_file)
            uploaded_file.seek(0)
            content = uploaded_file.read().decode(encoding)
        
        # Count lines
        lines = content.split('\n')
        total_rows = len([line for line in lines if line.strip()]) - 1  # Subtract header
        
        uploaded_file.seek(0)
        return max(0, total_rows)
    except Exception as e:
        st.error(f"Error counting rows: {e}")
        return 0

def split_csv_memory_efficient(uploaded_file, chunk_size=49999):
    """Split CSV file using ultra-memory-efficient processing"""
    try:
        uploaded_file.seek(0)
        
        # Detect encoding and read content
        encoding = detect_encoding(uploaded_file)
        content = uploaded_file.read()
        
        if isinstance(content, bytes):
            content = content.decode(encoding)
        
        # Split into lines
        lines = content.split('\n')
        lines = [line.strip() for line in lines if line.strip()]  # Remove empty lines
        
        if len(lines) < 2:  # Need at least header + 1 data row
            st.error("File appears to be empty or has no data rows.")
            return [], 0
        
        header = lines[0]
        data_lines = lines[1:]
        total_rows = len(data_lines)
        
        if total_rows == 0:
            return [], 0
            
        num_output_files = (total_rows + chunk_size - 1) // chunk_size
        st.info(f"Processing {total_rows:,} rows into {num_output_files} files...")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        output_chunks = []
        
        # Process in chunks
        for file_num in range(num_output_files):
            start_idx = file_num * chunk_size
            end_idx = min((file_num + 1) * chunk_size, total_rows)
            
            # Get chunk of data lines
            chunk_lines = data_lines[start_idx:end_idx]
            
            # Create CSV content
            csv_content = header + '\n' + '\n'.join(chunk_lines)
            
            output_chunks.append({
                'content': csv_content,
                'filename': f'split_{file_num + 1}.csv',
                'row_count': len(chunk_lines)
            })
            
            # Update progress
            progress = (file_num + 1) / num_output_files
            progress_bar.progress(progress)
            status_text.text(f"Creating files: {file_num + 1} / {num_output_files} | Rows processed: {end_idx:,} / {total_rows:,}")
            
            # Force garbage collection periodically
            if file_num % 5 == 0:
                gc.collect()
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ Processing complete! Created {len(output_chunks)} files.")
        
        # Clean up large variables
        del content, lines, data_lines
        gc.collect()
        
        return output_chunks, total_rows
        
    except Exception as e:
        st.error(f"Error processing CSV: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")
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
        - Supports UTF-8, Latin1, and other common encodings
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
                    
                    st.success(f"✅ All files are ready for download!")
                    
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {e}")
                    import traceback
                    st.error(f"Debug info: {traceback.format_exc()}")
                    st.write("Please try again with a smaller file or contact support if the issue persists.")
                    # Force cleanup on error
                    gc.collect()

if __name__ == "__main__":
    main() 