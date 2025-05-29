import streamlit as st
import base64

st.title("CSV Splitter")
st.write("Split CSV files into 49,999 row chunks")

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'current_chunk' not in st.session_state:
    st.session_state.current_chunk = 0

uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file:
    file_size = uploaded_file.size / (1024 * 1024)
    st.info(f"File size: {file_size:.1f} MB")
    
    if file_size > 200:
        st.error("File too large (max 200MB)")
    elif st.button("Process File"):
        try:
            with st.spinner("Reading file..."):
                # Read file content
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                
                # Split into lines
                lines = [line for line in content.split('\n') if line.strip()]
                
                if len(lines) < 2:
                    st.error("Need header + data rows")
                else:
                    header = lines[0]
                    data = lines[1:]
                    total = len(data)
                    
                    # Store in session state
                    st.session_state.processed_data = {
                        'header': header,
                        'data': data,
                        'total': total,
                        'num_files': (total + 49999 - 1) // 49999
                    }
                    st.session_state.current_chunk = 0
                    
                    st.success(f"File processed! {total} rows will create {st.session_state.processed_data['num_files']} files")
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error reading file: {e}")

# Show download links if data is processed
if st.session_state.processed_data:
    data_info = st.session_state.processed_data
    
    st.subheader(f"Download Files ({data_info['num_files']} total)")
    
    # Show one download link at a time to avoid memory issues
    chunk_size = 49999
    
    for i in range(data_info['num_files']):
        if st.button(f"Generate Download Link for File {i+1}", key=f"gen_{i}"):
            try:
                start = i * chunk_size
                end = min((i + 1) * chunk_size, data_info['total'])
                chunk = data_info['data'][start:end]
                
                # Create CSV content
                csv_data = data_info['header'] + '\n' + '\n'.join(chunk)
                
                # Create download link
                b64 = base64.b64encode(csv_data.encode('utf-8')).decode()
                link = f'data:file/csv;base64,{b64}'
                name = f'split_{i+1}.csv'
                
                st.success(f"File {i+1} ready!")
                st.markdown(f'<a href="{link}" download="{name}">📥 Download {name} ({len(chunk)} rows)</a>', unsafe_allow_html=True)
                
                # Clear the CSV data immediately
                del csv_data, chunk
                
            except Exception as e:
                st.error(f"Error creating file {i+1}: {e}")
    
    if st.button("Clear Data"):
        st.session_state.processed_data = None
        st.session_state.current_chunk = 0
        st.rerun() 