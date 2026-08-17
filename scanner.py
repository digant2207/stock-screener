import yfinance as yf
import pandas as pd
import warnings
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

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

def process_single_stock(ticker):
    """
    Processes a single stock ticker applying the CAR + 30/50/200 DMA Breakout Strategy.
    """
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        
        if data is None or data.empty or len(data) < 200:
            return None
            
        if isinstance(data.columns, pd.MultiIndex):
            close_prices = data['Close'][ticker] if ticker in data['Close'].columns else data['Close'].iloc[:, 0]
            high_prices = data['High'][ticker] if ticker in data['High'].columns else data['High'].iloc[:, 0]
        else:
            close_prices = data['Close']
            high_prices = data['High']
            
        close_prices = close_prices.squeeze().dropna()
        high_prices = high_prices.squeeze().dropna()
        
        if len(close_prices) < 200:
            return None
            
        # 2. DMA Calculations
        dma_30 = float(close_prices.rolling(window=30).mean().iloc[-1])
        dma_50 = float(close_prices.rolling(window=50).mean().iloc[-1])
        dma_200 = float(close_prices.rolling(window=200).mean().iloc[-1])
        cmp = float(close_prices.iloc[-1])
        
        if pd.isna(cmp) or pd.isna(dma_200) or dma_200 == 0:
            return None
            
        # 3. Distance from 200 DMA
        dist_200_dma = float(((cmp - dma_200) / dma_200) * 100)
        
        # 4. 52-Week High
        last_252_high = high_prices.tail(252)
        if last_252_high.empty:
            return None
            
        high_date = last_252_high.idxmax()
        
        # 5. CAR Calculation
        car_data = close_prices.loc[high_date:]
        if len(car_data) < 10:
            return None
            
        car_values = car_data.expanding().mean()
        last_10_car = car_values.tail(10)
        
        if last_10_car.is_monotonic_increasing:
            car_status = 'Positive'
        else:
            car_status = 'Negative'
            
        # 6. Breakout Condition
        is_breakout = (cmp > dma_30) and (cmp > dma_50) and (cmp > dma_200) and (car_status == 'Positive')
        
        exchange = "BSE" if ticker.endswith('.BO') else "NSE"
        clean_stock_name = ticker.replace('.NS', '').replace('.BO', '')
        today_date = datetime.now().strftime("%d-%m-%Y")
        
        return {
            'Ticker': ticker,
            'Stock': clean_stock_name,
            'Exchange': exchange,
            'Date': today_date,
            'CMP': round(cmp, 2),
            '30 DMA': round(dma_30, 2),
            '50 DMA': round(dma_50, 2),
            '200 DMA': round(dma_200, 2),
            '200 DMA Dist %': round(dist_200_dma, 2),
            'CAR Status': car_status,
            'Action': '🟢 Positive Breakout' if is_breakout else '🔴 Avoid/Hold',
            'IsBreakout': is_breakout
        }
    except Exception as e:
        return None

def advanced_stock_scanner(ticker_list, max_workers=10, progress_callback=None):
    """
    Runs parallel stock scanner on ticker list. Returns DataFrame of Positive Breakouts and summary.
    """
    results = []
    total_count = len(ticker_list)
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {executor.submit(process_single_stock, ticker): ticker for ticker in ticker_list}
        
        for future in as_completed(future_to_ticker):
            completed_count += 1
            res = future.result()
            
            if res and res.get('IsBreakout'):
                results.append(res)
                
            if progress_callback:
                progress_callback(completed_count, total_count, res)
                
    df_positive = pd.DataFrame(results)
    
    if not df_positive.empty:
        df_positive = df_positive.sort_values(by='200 DMA Dist %', ascending=True)
        if 'IsBreakout' in df_positive.columns:
            df_positive = df_positive.drop(columns=['IsBreakout'])
            
    return df_positive

def export_results(df, excel_path="Final_Breakout_List.xlsx", csv_path="Final_Breakout_List.csv"):
    """
    Exports breakout dataframe to Excel and CSV.
    """
    if df is not None and not df.empty:
        df.to_excel(excel_path, index=False)
        df.to_csv(csv_path, index=False)
        return True
    return False
