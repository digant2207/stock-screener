import re
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import io

def get_robust_session():
    """
    Creates a requests Session with automatic retries for transient network glitches.
    """
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def parse_spreadsheet_id_and_gid(url):
    """
    Extract spreadsheet ID and gid from Google Sheet URL.
    """
    spreadsheet_id = None
    gid = "0"
    
    pub_match = re.search(r'/d/e/([a-zA-Z0-9-_]+)', url)
    if pub_match:
        return f"e/{pub_match.group(1)}", gid
        
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        spreadsheet_id = match.group(1)
        
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
    
    if not ticker or ticker in ['TICKER', 'SYMBOL', 'STOCKS', 'STOCK', 'CODE', 'COMPANY', 'NSE CODE', 'BSE CODE', 'NAME', 'SR NO', 'S.NO', 'NAN', 'NONE', 'NULL']:
        return None
        
    if ticker.endswith('.0') and ticker[:-2].isdigit():
        ticker = ticker[:-2]
        
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        return ticker
        
    # Numeric 6-digit BSE code
    if ticker.isdigit() and len(ticker) == 6:
        return f"{ticker}.BO"
        
    # Standard string ticker (e.g. RELIANCE -> RELIANCE.NS)
    ticker = re.sub(r'[^A-Z0-9&\-]', '', ticker)
    if ticker:
        return f"{ticker}.NS"
        
    return None

def fetch_tickers_from_google_sheet(sheet_url, col_identifier="A"):
    """
    Downloads CSV from Google Sheet URL and extracts formatted stock tickers from the specified column.
    Uses automatic retries and multiple export endpoints for maximum reliability.
    """
    spreadsheet_id, gid = parse_spreadsheet_id_and_gid(sheet_url)
    if not spreadsheet_id:
        raise ValueError("Invalid Google Sheet URL. Could not find Spreadsheet ID.")
        
    session = get_robust_session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    export_urls = [
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}",
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/pub?output=csv&gid={gid}"
    ]
    
    response = None
    for url in export_urls:
        try:
            r = session.get(url, headers=headers, timeout=15)
            if r.status_code == 200 and len(r.text.strip()) > 0:
                response = r
                break
        except Exception:
            continue
            
    if not response or response.status_code != 200:
        raise ValueError(
            "Failed to access Google Sheet. Ensure General Access is set to 'Anyone with the link'."
        )
        
    df = pd.read_csv(io.StringIO(response.text), header=None)
    if df.empty:
        return []
        
    col_idx = 0
    if str(col_identifier).isalpha() and len(str(col_identifier)) == 1:
        col_idx = ord(str(col_identifier).upper()) - ord('A')
    elif str(col_identifier).isdigit():
        col_idx = int(col_identifier)
    else:
        first_row = df.iloc[0].astype(str).str.strip().str.upper().tolist()
        if str(col_identifier).upper() in first_row:
            col_idx = first_row.index(str(col_identifier).upper())
            
    if col_idx >= len(df.columns):
        col_idx = 0
        
    raw_list = df.iloc[:, col_idx].dropna().tolist()
    
    formatted_tickers = []
    seen = set()
    
    for item in raw_list:
        symbol = format_ticker_symbol(item)
        if symbol and symbol not in seen:
            seen.add(symbol)
            formatted_tickers.append(symbol)
            
    return formatted_tickers
