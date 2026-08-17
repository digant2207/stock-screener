from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import yfinance as yf
import os
from sheets_importer import fetch_tickers_from_google_sheet, format_ticker_symbol
from scanner import advanced_stock_scanner, export_results, process_single_stock

app = Flask(__name__)

# Pre-loaded default stock list from original Colab script
DEFAULT_STOCKS = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ABCAPITAL.NS',
    'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS',
    'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS',
    'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS',
    'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS',
    'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS',
    'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS',
    'COCHINSHIP.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS',
    'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS',
    'DELHIVERY.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS',
    'EICHERMOT.NS', 'EXIDEIND.NS', 'FORCEMOT.NS', 'NYKAA.NS', 'FORTIS.NS',
    'GAIL.NS', 'GVT&D.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODFRYPHLP.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS',
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS',
    'HYUNDAI.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS',
    'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRFC.NS', 'IREDA.NS',
    'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS',
    'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS',
    'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS',
    'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTM.NS',
    'LT.NS', 'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS',
    'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS',
    'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS', 'MOTILALOFS.NS', 'MPHASIS.NS',
    'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS',
    'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NAM-INDIA.NS', 'NUVAMA.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS',
    'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'POLYCAB.NS',
    'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS', 'PNB.NS',
    'RBLBANK.NS', 'RECLTD.NS', 'RADICO.NS', 'RVNL.NS', 'RELIANCE.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'MOTHERSON.NS',
    'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS',
    'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS',
    'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS',
    'TATAPOWER.NS', 'TATASTEEL.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS',
    'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS',
    'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS',
    'VBL.NS', 'VEDL.NS', 'VMM.NS', 'IDEA.NS', 'VOLTAS.NS',
    'WAAREEENER.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# Cache last scan dataframe
LAST_SCAN_DF = pd.DataFrame()

@app.route('/')
def home():
    return render_template('index.html', default_count=len(DEFAULT_STOCKS))

@app.route('/api/load-sheet', methods=['POST'])
def load_sheet():
    data = request.json or {}
    sheet_url = data.get('sheet_url', '').strip()
    column = data.get('column', 'A').strip()
    
    if not sheet_url:
        return jsonify({'success': False, 'error': 'Google Sheet URL is required.'}), 400
        
    try:
        tickers = fetch_tickers_from_google_sheet(sheet_url, col_identifier=column)
        if not tickers:
            return jsonify({'success': False, 'error': 'No valid tickers found in specified column.'}), 400
            
        return jsonify({
            'success': True,
            'count': len(tickers),
            'tickers': tickers,
            'sample': tickers[:10]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/parse-pasted', methods=['POST'])
def parse_pasted():
    data = request.json or {}
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'success': False, 'error': 'Please paste stock symbols.'}), 400
        
    raw_list = [line.strip() for line in text.replace(',', '\n').split('\n') if line.strip()]
    formatted_tickers = []
    seen = set()
    
    for item in raw_list:
        sym = format_ticker_symbol(item)
        if sym and sym not in seen:
            seen.add(sym)
            formatted_tickers.append(sym)
            
    return jsonify({
        'success': True,
        'count': len(formatted_tickers),
        'tickers': formatted_tickers,
        'sample': formatted_tickers[:10]
    })

@app.route('/api/scan', methods=['POST'])
def scan():
    global LAST_SCAN_DF
    data = request.json or {}
    tickers = data.get('tickers', [])
    
    if not tickers:
        tickers = DEFAULT_STOCKS
        
    workers = int(data.get('max_workers', 12))
    
    # Run scan
    df_breakout = advanced_stock_scanner(tickers, max_workers=workers)
    LAST_SCAN_DF = df_breakout.copy()
    
    # Export files locally
    export_results(df_breakout)
    
    records = []
    if not df_breakout.empty:
        records = df_breakout.to_dict(orient='records')
        
    return jsonify({
        'success': True,
        'total_scanned': len(tickers),
        'breakouts_found': len(records),
        'results': records
    })

@app.route('/api/chart/<ticker>')
def get_chart_data(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if data.empty:
            return jsonify({'success': False, 'error': f'No historical data for {ticker}'}), 404
            
        if isinstance(data.columns, pd.MultiIndex):
            close_prices = data['Close'][ticker] if ticker in data['Close'].columns else data['Close'].iloc[:, 0]
            high_prices = data['High'][ticker] if ticker in data['High'].columns else data['High'].iloc[:, 0]
        else:
            close_prices = data['Close']
            high_prices = data['High']
            
        close_prices = close_prices.squeeze().dropna()
        high_prices = high_prices.squeeze().dropna()
        
        # DMAs
        dma_30 = close_prices.rolling(30).mean()
        dma_50 = close_prices.rolling(50).mean()
        dma_200 = close_prices.rolling(200).mean()
        
        # 52w high date
        high_date = high_prices.idxmax()
        car_data = close_prices.loc[high_date:]
        car_values = car_data.expanding().mean() if len(car_data) >= 10 else pd.Series(index=close_prices.index)
        
        dates = [d.strftime('%Y-%m-%d') for d in close_prices.index]
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'dates': dates,
            'close': close_prices.round(2).tolist(),
            'dma_30': dma_30.round(2).fillna(None).tolist(),
            'dma_50': dma_50.round(2).fillna(None).tolist(),
            'dma_200': dma_200.round(2).fillna(None).tolist(),
            'car': car_values.reindex(close_prices.index).round(2).fillna(None).tolist()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/excel')
def download_excel():
    path = "Final_Breakout_List.xlsx"
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="Final_Breakout_List.xlsx")
    return "File not generated yet. Run scan first.", 404

@app.route('/api/download/csv')
def download_csv():
    path = "Final_Breakout_List.csv"
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="Final_Breakout_List.csv")
    return "File not generated yet. Run scan first.", 404

if __name__ == '__main__':
    print("Starting Stock Screener Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
