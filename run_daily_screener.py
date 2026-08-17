import os
import sys
from sheets_importer import fetch_tickers_from_google_sheet
from scanner import advanced_stock_scanner, export_results
from mailer import send_breakout_email
from app import DEFAULT_STOCKS

def main():
    print("=" * 60)
    print("🚀 Starting Daily Stock Screener Execution")
    print("=" * 60)
    
    sheet_url = os.environ.get('GOOGLE_SHEET_URL', 'https://docs.google.com/spreadsheets/d/1B__Wam6da-nD7ReSg2JlHwu5pH7xDHlkQkBjSzF9YdA/edit?gid=0#gid=0')
    column = os.environ.get('GOOGLE_SHEET_COLUMN', 'A')
    
    tickers = []
    if sheet_url:
        print(f"📥 Attempting to fetch tickers from Google Sheet: {sheet_url}")
        try:
            tickers = fetch_tickers_from_google_sheet(sheet_url, col_identifier=column)
            print(f"✅ Successfully fetched {len(tickers)} tickers from Google Sheet.")
        except Exception as e:
            print(f"⚠️ Could not fetch from Google Sheet ({e}). Falling back to default pre-loaded list.")
            tickers = DEFAULT_STOCKS
    else:
        tickers = DEFAULT_STOCKS
        
    if not tickers:
        print("❌ No tickers available to scan. Exiting.")
        sys.exit(1)
        
    print(f"\n⚡ Running Parallel Super Breakout Scanner on {len(tickers)} stocks...")
    df_breakout = advanced_stock_scanner(tickers, max_workers=12)
    
    breakout_count = len(df_breakout) if not df_breakout.empty else 0
    print(f"🎯 Scan Complete! Found {breakout_count} Positive Breakout stocks.")
    
    # Export results
    export_results(df_breakout)
    print("📁 Saved results to Final_Breakout_List.xlsx and Final_Breakout_List.csv")
    
    # Send Email
    print("\n📧 Sending Daily Email Report to Gmail...")
    email_sent = send_breakout_email(df_breakout)
    if email_sent:
        print("🎉 Daily Screener execution completed successfully!")
    else:
        print("⚠️ Screener completed, but email delivery failed (check GMAIL_USER and GMAIL_APP_PASSWORD).")

if __name__ == "__main__":
    main()
