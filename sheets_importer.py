import re
import pandas as pd
import requests
import io

def parse_spreadsheet_id_and_gid(url):
    """
    Extract spreadsheet ID and gid from Google Sheet URL.
    """
    spreadsheet_id = None
    gid = "0"
    
    # Extract Spreadsheet ID
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        spreadsheet_id = match.group(1)
        
    # Extract gid
    gid_match = re.search(r'[#&?]gid=([0-9]+)', url)
    if gid_match:
        gid = gid_match.group(1)
        
    return spreadsheet_id, gid

def format_ticker_symbol(raw_ticker):
    """
    Formats raw ticker symbol to Yahoo Finance compatible ticker (.NS or .BO).
    - Already has .NS or .BO -> preserve
    - 6-digit numeric code -> append .BO (BSE)
    - Alphabetic symbol -> append .NS (NSE)
    """
    ticker = str(raw_ticker).strip().upper()
    
    # Remove headers or invalid entries
    if not ticker or ticker in ['TICKER', 'SYMBOL', 'STOCKS', 'STOCK', 'CODE', 'COMPANY', 'NSE CODE', 'BSE CODE', 'NAME', 'SR NO', 'S.NO']:
        return None
        
    # Remove trailing .0 if pandas parsed integer as float string (e.g. "500325.0")
    if ticker.endswith('.0') and ticker[:-2].isdigit():
        ticker = ticker[:-2]
        
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        return ticker
        
    # Numeric 6-digit BSE code
    if ticker.isdigit() and len(ticker) == 6:
        return f"{ticker}.BO"
        
    # Standard string ticker (e.g. RELIANCE -> RELIANCE.NS)
    # Sanitize invalid symbols
    ticker = re.sub(r'[^A-Z0-9&\-]', '', ticker)
    if ticker:
        return f"{ticker}.NS"
        
    return None

def fetch_tickers_from_google_sheet(sheet_url, col_identifier="A"):
    """
    Downloads CSV from Google Sheet URL and extracts formatted stock tickers from the specified column.
    `col_identifier` can be column letter ('A', 'B', etc.) or column index (0, 1) or header name.
    """
    spreadsheet_id, gid = parse_spreadsheet_id_and_gid(sheet_url)
    if not spreadsheet_id:
        raise ValueError("Invalid Google Sheet URL. Could not find Spreadsheet ID.")
        
    # Construct export URL
    export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(export_url, headers=headers, timeout=15)
    if response.status_code != 200:
        # Fallback to gviz URL
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
        response = requests.get(export_url, headers=headers, timeout=15)
        if response.status_code != 200:
            raise ValueError(f"Failed to access Google Sheet (HTTP {response.status_code}). Ensure sheet permissions are set to 'Anyone with link can view'.")
            
    # Read CSV
    df = pd.read_csv(io.StringIO(response.text), header=None)
    if df.empty:
        return []
        
    # Determine column index
    col_idx = 0
    if str(col_identifier).isalpha() and len(str(col_identifier)) == 1:
        col_idx = ord(str(col_identifier).upper()) - ord('A')
    elif str(col_identifier).isdigit():
        col_idx = int(col_identifier)
    else:
        # Check if first row contains matching header
        first_row = df.iloc[0].astype(str).str.strip().str.upper().tolist()
        if str(col_identifier).upper() in first_row:
            col_idx = first_row.index(str(col_identifier).upper())
            
    if col_idx >= len(df.columns):
        col_idx = 0 # Default fallback to Column A
        
    raw_list = df.iloc[:, col_idx].dropna().tolist()
    
    formatted_tickers = []
    seen = set()
    
    for item in raw_list:
        symbol = format_ticker_symbol(item)
        if symbol and symbol not in seen:
            seen.add(symbol)
            formatted_tickers.append(symbol)
            
    return formatted_tickers

if __name__ == "__main__":
    test_url = "https://docs.google.com/spreadsheets/d/1B__Wam6da-nD7ReSg2JlHwu5pH7xDHlkQkBjSzF9YdA/edit?gid=0#gid=0"
    tickers = fetch_tickers_from_google_sheet(test_url, col_identifier="A")
    print(f"Extracted {len(tickers)} tickers from test sheet. Sample:", tickers[:10])
