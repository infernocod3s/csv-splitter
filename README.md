# CSV Splitter Web Application

A web-based tool that splits large CSV files into smaller chunks of 49,999 records each while preserving the original data structure.

## Features

- Simple web interface
- Upload CSV files directly in the browser
- Automatic splitting into chunks of 49,999 records
- Download individual split files
- No data modification - preserves original CSV structure
- Free to host on Streamlit Cloud

## Requirements

- Python 3.6 or higher
- pandas
- streamlit

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running Locally

To run the application locally:

```bash
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Create a GitHub repository and push this code
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Sign up/Login with your GitHub account
4. Click "New app"
5. Select your repository and set the main file path to `app.py`
6. Click "Deploy"

## Usage

1. Open the web application
2. Click "Browse files" to upload your CSV file
3. The application will automatically process the file
4. Download the split files using the provided download links

Each split file will contain up to 49,999 records from the original CSV file. 