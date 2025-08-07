from flask import Flask, render_template, request, send_file, jsonify
import yfinance as yf
import pandas as pd
import os
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
@app.route('/download', methods=['POST', 'GET'])
def download():
    ticker = request.form.get('ticker', '').upper()
    period = request.form.get('period', '5y')

    if not ticker:
        return "Error: No ticker provided."

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval='1d')

        if hist.empty or len(hist) < 30:
            return f"No sufficient data for {ticker} with period {period} and interval 1d."

        hist.reset_index(inplace=True)

        # Fetch fundamental info
        info = stock.info
        metrics = {
            'longName': info.get('longName'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'country': info.get('country'),
            'marketCap': info.get('marketCap'),
            'beta': info.get('beta'),
            'trailingPE': info.get('trailingPE'),
            'forwardPE': info.get('forwardPE'),
            'dividendYield': info.get('dividendYield'),
            'returnOnEquity': info.get('returnOnEquity'),
            'trailingEps': info.get('trailingEps'),
            'totalRevenue': info.get('totalRevenue'),
        }

        for key, value in metrics.items():
            hist[key] = value

        file_path = os.path.join(DOWNLOAD_FOLDER, "data.csv")
        hist.to_csv(file_path, index=False)

        return render_template('index.html', success=True, ticker=ticker, file="data.csv")

    except Exception as e:
        return f"Error fetching data for {ticker}: {str(e)}"

@app.route('/get_csv/<ticker>')
def get_csv(ticker):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"_full.csv")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found."

if __name__ == '__main__':
    app.run(debug=True)
