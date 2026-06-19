"""
NSE ChartPro Backend - Real NSE Data via yfinance
Deployed on Render (free tier)
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Nifty stocks list
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

@app.route('/')
def home():
    return jsonify({"service":"ChartPro NSE API","status":"running"})

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
        '1d':('1d','1d'),
        'daily':('max','1d'),
        'monthly':('max','1mo'),
        'weekly':('max','1wk')
    }
    
    if period not in period_map:
        return jsonify({"error":"Invalid period"}), 400
    
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
            "symbol":symbol, "period":period,
            "candles":candles,
            "from":candles[0]['date'],
            "to":candles[-1]['date'],
            "count":len(candles)
        })
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status":"ok","time":datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)