import json
import os
import yfinance as yf
import pandas as pd

CACHE_FILE = "saved_portfolio.json"


def load_cached_portfolio(broker_name):
    """Reads the saved portfolio from the local JSON file for a specific broker."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as file:
                data = json.load(file)

                # Backward compatibility: If the file is still the old flat list
                if isinstance(data, list):
                    return data if broker_name == "Zerodha" else None

                # Return the specific broker's data, or None if they haven't synced yet
                return data.get(broker_name)
        except json.JSONDecodeError:
            return None
    return None


def save_portfolio(broker_name, broker_data):
    """Saves the normalized broker data into the specific broker's bucket."""
    all_data = {}

    # First, load existing data so we don't overwrite the other broker
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as file:
                existing_data = json.load(file)
                if isinstance(existing_data, dict):
                    all_data = existing_data
        except json.JSONDecodeError:
            pass

    # Inject the new data for the active broker
    all_data[broker_name] = broker_data

    # Save the entire dictionary back to the file
    with open(CACHE_FILE, "w") as file:
        json.dump(all_data, file)


def process_live_data(raw_stocks):
    """Takes raw holdings, fetches live prices/sectors with BSE fallback, and returns a DataFrame."""
    portfolio_data = []

    for stock in raw_stocks:
        base_ticker = stock['ticker']

        # --- THE FALLBACK ENGINE ---
        # 1. Try NSE First
        yf_ticker = f"{base_ticker}.NS"
        info = yf.Ticker(yf_ticker).info

        # yfinance often leaves 'currentPrice' out if the ticker is invalid
        if 'currentPrice' not in info and 'previousClose' not in info:
            # 2. Fallback to BSE
            yf_ticker = f"{base_ticker}.BO"
            info = yf.Ticker(yf_ticker).info

        # Extract data (falling back to avg_price if both APIs fail completely)
        current_price = info.get('currentPrice', info.get('previousClose', stock['avg_price']))
        sector = info.get('sector', 'Unknown')
        # ---------------------------

        invested = stock['qty'] * stock['avg_price']
        current_value = stock['qty'] * current_price

        portfolio_data.append({
            "Stock": base_ticker,
            "Yahoo Ticker": yf_ticker,  # Saving this for the chart later!
            "Sector": sector,
            "Qty": stock['qty'],
            "Avg Price": stock['avg_price'],
            "Current Price": current_price,
            "Invested": invested,
            "Current Value": current_value,
            "Return (%)": ((current_value - invested) / invested) * 100 if invested > 0 else 0
        })

    return pd.DataFrame(portfolio_data)