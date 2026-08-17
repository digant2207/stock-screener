import yfinance as yf
import pandas as pd
import warnings
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

def process_single_stock(ticker):
    """
    Processes a single stock ticker applying the CAR + 30/50/200 DMA Breakout Strategy.
    """
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        
        if data is None or data.empty or len(data) < 200:
            return None
            
        # Handle single vs multi-index columns in modern yfinance
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
        # Drop internal boolean flag
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

if __name__ == "__main__":
    sample = ['RELIANCE.NS', 'TCS.NS', '500325.BO', 'INFY.NS', 'BEL.NS']
    print("Testing scanner on sample stocks...")
    res_df = advanced_stock_scanner(sample)
    print("Results:\n", res_df)
