from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import numpy as np
import time

app = Flask(__name__)
CORS(app)

STOCKS = [
    {"symbol":"RELIANCE","name":"Reliance Industries","sector":"Oil & Gas"},
    {"symbol":"TCS","name":"Tata Consultancy Services","sector":"IT"},
    {"symbol":"HDFCBANK","name":"HDFC Bank","sector":"Banking"},
    {"symbol":"INFY","name":"Infosys","sector":"IT"},
    {"symbol":"ICICIBANK","name":"ICICI Bank","sector":"Banking"},
    {"symbol":"ITC","name":"ITC Ltd","sector":"FMCG"},
    {"symbol":"SBIN","name":"State Bank of India","sector":"Banking"},
    {"symbol":"BHARTIARTL","name":"Bharti Airtel","sector":"Telecom"},
    {"symbol":"LT","name":"Larsen & Toubro","sector":"Infrastructure"},
    {"symbol":"TATAMOTORS","name":"Tata Motors","sector":"Automobile"},
    {"symbol":"MARUTI","name":"Maruti Suzuki","sector":"Automobile"},
    {"symbol":"WIPRO","name":"Wipro","sector":"IT"},
    {"symbol":"SUNPHARMA","name":"Sun Pharma","sector":"Pharma"},
    {"symbol":"BAJFINANCE","name":"Bajaj Finance","sector":"Financial"},
    {"symbol":"NTPC","name":"NTPC","sector":"Energy"},
    {"symbol":"ONGC","name":"ONGC","sector":"Oil & Gas"},
    {"symbol":"TITAN","name":"Titan Company","sector":"Consumer"},
    {"symbol":"HINDUNILVR","name":"Hindustan Unilever","sector":"FMCG"},
    {"symbol":"KOTAKBANK","name":"Kotak Mahindra Bank","sector":"Banking"},
    {"symbol":"AXISBANK","name":"Axis Bank","sector":"Banking"},
]

cache = {}

@app.route('/stocks')
def get_stocks():
    return jsonify(STOCKS)

@app.route('/quote/<symbol>')
def get_quote(symbol):
    symbol = symbol.upper()
    if symbol in cache and time.time() - cache[symbol].get('_t',0) < 30:
        return jsonify(cache[symbol])
    
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        hist = ticker.history(period="1d")
        if hist.empty:
            return jsonify({"error":"No data"}), 404
        
        price = hist['Close'].iloc[-1]
        prev = info.get('previousClose', price)
        change = price - prev
        cp = (change/prev)*100 if prev else 0
        
        stock = next((s for s in STOCKS if s['symbol']==symbol), None)
        result = {
            "symbol":symbol,
            "name":stock['name'] if stock else symbol,
            "sector":stock['sector'] if stock else '',
            "price":round(price,2),
            "open":round(hist['Open'].iloc[-1],2),
            "high":round(hist['High'].iloc[-1],2),
            "low":round(hist['Low'].iloc[-1],2),
            "close":round(price,2),
            "previousClose":round(prev,2),
            "change":round(change,2),
            "changePercent":round(cp,2),
            "volume":int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
            "source":"Yahoo Finance (NSE)",
            "_t":time.time()
        }
        cache[symbol] = result
        return jsonify(result)
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/history/<symbol>/<period>')
def get_history(symbol, period):
    symbol = symbol.upper()
    
    period_map = {
        'daily':('max','1d'),
        'weekly':('max','1wk'),
        'monthly':('max','1mo')
    }
    
    if period not in period_map:
        return jsonify({"error":"Invalid period. Use: daily, weekly, monthly"}), 400
    
    yf_period, yf_interval = period_map[period]
    
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=yf_period, interval=yf_interval)
        
        if hist.empty:
            return jsonify({"error":"No data"}), 404
        
        candles = []
        for index, row in hist.iterrows():
            candles.append({
                "time": int(index.timestamp()),
                "date": index.strftime("%Y-%m-%d"),
                "datetime": index.strftime("%Y-%m-%d %H:%M"),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume']) if 'Volume' in row else 0
            })
        
        return jsonify({
            "symbol":symbol,
            "period":period,
            "candles":candles,
            "from":candles[0]['date'],
            "to":candles[-1]['date'],
            "count":len(candles)
        })
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/indicators/<symbol>/<period>')
def get_indicators(symbol, period):
    symbol = symbol.upper()
    
    period_map = {
        'daily':('max','1d'),
        'weekly':('max','1wk'),
        'monthly':('max','1mo')
    }
    
    if period not in period_map:
        return jsonify({"error":"Invalid period"}), 400
    
    yf_period, yf_interval = period_map[period]
    
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=yf_period, interval=yf_interval)
        
        if hist.empty or len(hist) < 50:
            return jsonify({"error":"Not enough data for indicators"}), 404
        
        closes = hist['Close'].values
        highs = hist['High'].values
        lows = hist['Low'].values
        volumes = hist['Volume'].values
        
        # RSI (14)
        rsi = calculate_rsi(closes, 14)
        
        # ADX (14)
        adx = calculate_adx(highs, lows, closes, 14)
        
        # ATR (14)
        atr = calculate_atr(highs, lows, closes, 14)
        
        # Moving Averages
        ma20 = moving_average(closes, 20)
        ma50 = moving_average(closes, 50)
        ma200 = moving_average(closes, 200)
        
        # Bollinger Bands (20, 2)
        bb_upper, bb_middle, bb_lower = bollinger_bands(closes, 20, 2)
        
        # MACD (12, 26, 9)
        macd_line, signal_line, macd_histogram = calculate_macd(closes)
        
        timestamps = [int(index.timestamp()) for index in hist.index]
        
        return jsonify({
            "symbol":symbol,
            "period":period,
            "timestamps":timestamps,
            "rsi":rsi,
            "adx":adx,
            "atr":atr,
            "ma20":ma20,
            "ma50":ma50,
            "ma200":ma200,
            "bb_upper":bb_upper,
            "bb_middle":bb_middle,
            "bb_lower":bb_lower,
            "macd_line":macd_line,
            "signal_line":signal_line,
            "macd_histogram":macd_histogram
        })
    except Exception as e:
        return jsonify({"error":str(e)}), 500

def calculate_rsi(closes, period=14):
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')
    rs = avg_gain / np.where(avg_loss == 0, 1, avg_loss)
    rsi = 100 - (100 / (1 + rs))
    return [None]*period + rsi.tolist()

def calculate_adx(highs, lows, closes, period=14):
    tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1]))
    plus_dm = np.where((highs[1:] - highs[:-1]) > (lows[:-1] - lows[1:]), np.maximum(highs[1:] - highs[:-1], 0), 0)
    minus_dm = np.where((lows[:-1] - lows[1:]) > (highs[1:] - highs[:-1]), np.maximum(lows[:-1] - lows[1:], 0), 0)
    atr = np.convolve(tr, np.ones(period)/period, mode='valid')
    plus_di = 100 * np.convolve(plus_dm, np.ones(period)/period, mode='valid') / atr
    minus_di = 100 * np.convolve(minus_dm, np.ones(period)/period, mode='valid') / atr
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
    adx = np.convolve(dx, np.ones(period)/period, mode='valid')
    return [None]*(period*2-1) + adx.tolist()

def calculate_atr(highs, lows, closes, period=14):
    tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1]))
    atr = np.convolve(tr, np.ones(period)/period, mode='valid')
    return [None]*(period) + atr.tolist()

def moving_average(data, period):
    ma = np.convolve(data, np.ones(period)/period, mode='valid')
    return [None]*(period-1) + ma.tolist()

def bollinger_bands(closes, period=20, std=2):
    ma = np.convolve(closes, np.ones(period)/period, mode='valid')
    rolling_std = np.array([np.std(closes[i-period+1:i+1]) for i in range(period-1, len(closes))])
    upper = ma + std * rolling_std
    lower = ma - std * rolling_std
    return (
        [None]*(period-1) + upper.tolist(),
        [None]*(period-1) + ma.tolist(),
        [None]*(period-1) + lower.tolist()
    )

def calculate_macd(closes, fast=12, slow=26, signal=9):
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line[slow-1:], signal)
    macd_line = macd_line.tolist()
    signal_line_full = [None]*(slow-1) + signal_line.tolist()
    macd_hist = (np.array(macd_line[slow+signal-2:]) - np.array(signal_line[signal-1:])).tolist()
    return macd_line, signal_line_full, [None]*(slow+signal-2) + macd_hist

def ema(data, period):
    ema_values = np.zeros_like(data)
    ema_values[period-1] = np.mean(data[:period])
    multiplier = 2 / (period + 1)
    for i in range(period, len(data)):
        ema_values[i] = (data[i] - ema_values[i-1]) * multiplier + ema_values[i-1]
    return ema_values

@app.route('/health')
def health():
    return jsonify({"status":"ok","stocks":len(STOCKS)})

if __name__ == '__main__':
    print("\n==============================================")
    print("  ChartPro Backend with Indicators")
    print("  Endpoints: /stocks /quote /history /indicators")
    print("==============================================\n")
    app.run(host='0.0.0.0', port=5000)