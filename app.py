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
            try:
                # Show processing message
                processing_msg = st.empty()
                processing_msg.info("🔄 Reading and processing file...")
                
                # Read and decode file
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    try:
                        content = content.decode('utf-8')
                    except:
                        content = content.decode('latin1', errors='ignore')
                
                # Process lines
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                if len(lines) < 2:
                    st.error("File must have at least a header and one data row")
                    return
                
                header = lines[0]
                data_rows = lines[1:]
                total_rows = len(data_rows)
                
                chunk_size = 49999
                num_files = (total_rows + chunk_size - 1) // chunk_size
                
                processing_msg.success(f"✅ File processed! Creating {num_files} download files...")
                
                # Create download links container
                st.subheader("📥 Download Your Split Files")
                
                # Process all chunks and create download links
                for i in range(num_files):
                    start_idx = i * chunk_size
                    end_idx = min((i + 1) * chunk_size, total_rows)
                    
                    # Create chunk
                    chunk_data = data_rows[start_idx:end_idx]
                    csv_content = header + '\n' + '\n'.join(chunk_data)
                    
                    # Create download link
                    b64 = base64.b64encode(csv_content.encode('utf-8')).decode()
                    href = f'data:file/csv;base64,{b64}'
                    filename = f'split_{i + 1}.csv'
                    
                    # Display download link
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(
                            f'<a href="{href}" download="{filename}" style="text-decoration: none; color: #0066cc;">📥 Download {filename}</a>',
                            unsafe_allow_html=True
                        )
                    with col2:
                        st.write(f"{len(chunk_data):,} rows")
                
                # Summary
                st.success(f"🎉 Successfully created {num_files} files with {total_rows:,} total rows!")
                st.info("💡 Click the download links above to save each file to your computer.")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.write("Please try with a smaller file or check that your CSV is properly formatted.")

if __name__ == "__main__":
    main() 