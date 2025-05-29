import streamlit as st
import base64
import io

MAX_FILE_SIZE_MB = 200

def create_download_link(content, filename, text):
    """Create a download link for file content"""
    try:
        b64 = base64.b64encode(content.encode('utf-8')).decode()
        href = f'data:file/csv;base64,{b64}'
        return f'<a href="{href}" download="{filename}">{text}</a>'
    except Exception as e:
        st.error(f"Error creating download link: {str(e)}")
        return ""

def split_csv_simple(uploaded_file, chunk_size=49999):
    """Simple CSV splitter that works reliably"""
    try:
        # Read file content
        content = uploaded_file.read()
        
        # Handle different encodings
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except:
                try:
                    content = content.decode('latin1')
                except:
                    content = content.decode('cp1252', errors='ignore')
        
        # Split into lines and clean
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if len(lines) < 2:
            st.error("File must have at least a header and one data row")
            return []
        
        header = lines[0]
        data_rows = lines[1:]
        total_rows = len(data_rows)
        
        if total_rows == 0:
            st.error("No data rows found")
            return []
        
        # Calculate number of files needed
        num_files = (total_rows + chunk_size - 1) // chunk_size
        
        st.info(f"Splitting {total_rows:,} rows into {num_files} files")
        
        # Create progress bar
        progress_bar = st.progress(0)
        
        chunks = []
        
        # Split data into chunks
        for i in range(num_files):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_rows)
            
            # Get chunk data
            chunk_data = data_rows[start_idx:end_idx]
            
            # Create CSV content
            csv_content = header + '\n' + '\n'.join(chunk_data)
            
            chunks.append({
                'content': csv_content,
                'filename': f'split_{i + 1}.csv',
                'rows': len(chunk_data)
            })
            
            # Update progress
            progress_bar.progress((i + 1) / num_files)
        
        st.success(f"Successfully created {len(chunks)} files!")
        return chunks
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return []

def main():
    st.set_page_config(
        page_title="CSV Splitter",
        page_icon="📊"
    )
    
    st.title("📊 CSV Splitter")
    st.write("Split your CSV file into chunks of 49,999 rows each")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=['csv'],
        help="Maximum file size: 200 MB"
    )
    
    if uploaded_file is not None:
        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"File size: {file_size_mb:.1f} MB")
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(f"File too large! Maximum size is {MAX_FILE_SIZE_MB} MB")
            return
        
        # Split button
        if st.button("Split CSV File", type="primary"):
            with st.spinner("Processing..."):
                chunks = split_csv_simple(uploaded_file)
                
                if chunks:
                    # Show results
                    total_rows = sum(chunk['rows'] for chunk in chunks)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Rows", f"{total_rows:,}")
                    with col2:
                        st.metric("Files Created", len(chunks))
                    
                    # Download section
                    st.subheader("Download Files")
                    
                    for chunk in chunks:
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(
                                create_download_link(
                                    chunk['content'],
                                    chunk['filename'],
                                    f"📥 {chunk['filename']}"
                                ),
                                unsafe_allow_html=True
                            )
                        
                        with col2:
                            st.write(f"{chunk['rows']:,} rows")

if __name__ == "__main__":
    main() 