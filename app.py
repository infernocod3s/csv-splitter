import streamlit as st
import base64

def main():
    st.title("📊 CSV Splitter")
    st.write("Split your CSV file into chunks of 49,999 rows each")
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"File size: {file_size_mb:.1f} MB")
        
        if file_size_mb > 200:
            st.error("File too large! Maximum size is 200 MB")
            return
        
        if st.button("Split CSV File", type="primary"):
            with st.spinner("Processing..."):
                try:
                    # Read file content
                    content = uploaded_file.read()
                    
                    # Handle encoding
                    if isinstance(content, bytes):
                        try:
                            content = content.decode('utf-8')
                        except:
                            content = content.decode('latin1', errors='ignore')
                    
                    # Split into lines
                    lines = [line for line in content.split('\n') if line.strip()]
                    
                    if len(lines) < 2:
                        st.error("File must have at least a header and one data row")
                        return
                    
                    header = lines[0]
                    data_rows = lines[1:]
                    total_rows = len(data_rows)
                    
                    if total_rows == 0:
                        st.error("No data rows found")
                        return
                    
                    # Calculate chunks
                    chunk_size = 49999
                    num_files = (total_rows + chunk_size - 1) // chunk_size
                    
                    st.info(f"Splitting {total_rows:,} rows into {num_files} files")
                    
                    progress_bar = st.progress(0)
                    
                    # Create chunks
                    for i in range(num_files):
                        start_idx = i * chunk_size
                        end_idx = min((i + 1) * chunk_size, total_rows)
                        
                        chunk_data = data_rows[start_idx:end_idx]
                        csv_content = header + '\n' + '\n'.join(chunk_data)
                        
                        # Create download link
                        b64 = base64.b64encode(csv_content.encode('utf-8')).decode()
                        href = f'data:file/csv;base64,{b64}'
                        filename = f'split_{i + 1}.csv'
                        
                        st.markdown(
                            f'<a href="{href}" download="{filename}">📥 Download {filename} ({len(chunk_data):,} rows)</a>',
                            unsafe_allow_html=True
                        )
                        
                        progress_bar.progress((i + 1) / num_files)
                    
                    st.success(f"✅ Created {num_files} files ready for download!")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 