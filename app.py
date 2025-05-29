import streamlit as st
import base64

st.title("CSV Splitter")
st.write("Split CSV files into 49,999 row chunks")

uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file:
    file_size = uploaded_file.size / (1024 * 1024)
    st.info(f"File size: {file_size:.1f} MB")
    
    if file_size > 200:
        st.error("File too large (max 200MB)")
    elif st.button("Split File"):
        try:
            # Read file
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Split lines
            lines = [line for line in content.split('\n') if line.strip()]
            
            if len(lines) < 2:
                st.error("Need header + data rows")
            else:
                header = lines[0]
                data = lines[1:]
                total = len(data)
                
                # Calculate files needed
                chunk_size = 49999
                num_files = (total + chunk_size - 1) // chunk_size
                
                st.success(f"Creating {num_files} files from {total} rows")
                
                # Create download links
                for i in range(num_files):
                    start = i * chunk_size
                    end = min((i + 1) * chunk_size, total)
                    chunk = data[start:end]
                    
                    # Make CSV content
                    csv_data = header + '\n' + '\n'.join(chunk)
                    
                    # Encode for download
                    b64 = base64.b64encode(csv_data.encode('utf-8')).decode()
                    link = f'data:file/csv;base64,{b64}'
                    name = f'split_{i+1}.csv'
                    
                    st.markdown(f'<a href="{link}" download="{name}">Download {name} ({len(chunk)} rows)</a>', unsafe_allow_html=True)
                
                st.balloons()
        
        except Exception as e:
            st.error(f"Error: {e}") 