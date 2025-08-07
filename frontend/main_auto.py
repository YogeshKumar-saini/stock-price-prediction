# main_auto.py

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# --- 1. INITIALIZE APP AND LOAD ALL ASSETS ---
app = FastAPI(
    title="Automated Stock Predictor API",
    description="API to automatically predict next day and next week stock prices.",
    version="2.0"
)

# Load the model, scaler, and the dataset when the application starts
try:
    # Using absolute paths as provided by the user
    model = joblib.load('/home/yogesh/genai/stock price prediction/notebook/stock_price_model.joblib')
    scaler = joblib.load('/home/yogesh/genai/stock price prediction/notebook/scaler.joblib')
    df = pd.read_csv('/home/yogesh/genai/stock price prediction/notebook/preprocessed_stock_data.csv') 
    print("✅ Model, scaler, and data loaded successfully!")
except FileNotFoundError as e:
    print(f"🔴 Error loading files: {e}. Make sure all files are in the directory.")
    model, scaler, df = None, None, None

# Define the feature columns in the order the model expects them
FEATURE_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']

# --- ENDPOINT TO SERVE THE HTML FRONTEND ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serves the index.html file as the main page.
    """
    try:
        with open("index.html") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1><p>Make sure the frontend file is in the same directory as this script.</p>", status_code=404)

# --- ENDPOINT TO PREDICT THE NEXT SINGLE DAY ---
@app.get("/predict_next_day/")
def get_next_day_prediction():
    """
    Fetches the latest data from the dataset and predicts the next day's closing price.
    """
    if df is None:
        return {"error": "Data not loaded. Cannot make predictions."}

    # 1. Get the last row of data from the dataframe
    last_known_data = df[FEATURE_COLUMNS].iloc[-1:].values
    
    # 2. Scale the data
    scaled_data = scaler.transform(last_known_data)
    
    # 3. Make prediction
    prediction = model.predict(scaled_data)
    
    return {"predicted_next_day_price": prediction[0]/10}


# --- ENDPOINT TO PREDICT THE NEXT WEEK (CORRECTED) ---
@app.get("/predict_next_week/")
def get_next_week_prediction():
    """
    Performs a recursive forecast to predict closing prices for the next 5 trading days.
    """
    if df is None:
        return {"error": "Data not loaded. Cannot make predictions."}
        
    weekly_predictions = []
    # Start with the last known data from our real dataset
    current_input = df[FEATURE_COLUMNS].iloc[-1:].values

    for day_num in range(1, 16): # Loop 5 times for 5 days
        # Scale the current input
        scaled_input = scaler.transform(current_input)
        
        # Make a prediction for the next day
        next_day_pred = model.predict(scaled_input)[0]/10
        
        # Store the prediction
        weekly_predictions.append({
            "day": day_num,
            "predicted_price": next_day_pred
        })
        
        # Update ALL price features (Open, High, Low, Close) with the new prediction.
        # This creates a more stable and realistic input for the next loop.
        current_input[0, 0] = next_day_pred # Open
        current_input[0, 1] = next_day_pred # High
        current_input[0, 2] = next_day_pred # Low
        current_input[0, 3] = next_day_pred # Close
        # The Volume (index 4) remains the same
        
    return {"next_week_predictions": weekly_predictions}
