import base64
import requests
import pandas as pd
import json
import os
from urllib.parse import urlencode
from datetime import datetime, timedelta
import pytz

# Define constants
CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
API_URL = 'https://api.fitbit.com/1/user/-/ecg/list.json'
TOKEN_FILE = 'fitbit_tokens.json'

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def get_access_token():
    tokens = load_tokens()
    if tokens:
        return tokens['access_token']
    
    authorization_code = input("Enter the authorization code: ")
    data = {
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': authorization_code,
    }
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode(),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=urlencode(data))
    response.raise_for_status()
    tokens = response.json()
    save_tokens(tokens)
    return tokens['access_token']

def refresh_access_token(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=urlencode(data))
    response.raise_for_status()
    tokens = response.json()
    save_tokens(tokens)
    return tokens['access_token']

def fetch_ecg_data(access_token, date, sort='asc', limit=10, offset=0):
    all_readings = []
    # Define the timezone for the date (e.g., Fitbit might use UTC)
    fitbit_timezone = pytz.utc
    local_timezone = pytz.timezone('Asia/Kolkata')  # Change to your local timezone if necessary

    # Convert the date to the correct timezone
    start_date = local_timezone.localize(datetime.strptime(date, '%Y-%m-%d')).astimezone(fitbit_timezone)
    end_date = start_date + timedelta(days=1)

    while True:
        params = {
            'afterDate': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'sort': sort,
            'limit': limit,
            'offset': offset
        }
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }

        response = requests.get(API_URL, headers=headers, params=params)
        
        if response.status_code == 401:  # Unauthorized, likely need to refresh token
            tokens = load_tokens()
            access_token = refresh_access_token(tokens['refresh_token'])
            headers['Authorization'] = f'Bearer {access_token}'
            response = requests.get(API_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            break

        data = response.json()
        print(f"Raw API Response: {json.dumps(data, indent=2)}")  # Debugging line
        ecg_readings = data.get('ecgReadings', [])
        if not ecg_readings:
            print(f"No ECG data found for {date}")
            break
        
        # Filter the readings to only include those from the specified date
        ecg_readings = [reading for reading in ecg_readings if start_date <= datetime.strptime(reading['startTime'], '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.utc) < end_date]
        all_readings.extend(ecg_readings)
        
        if len(ecg_readings) < limit:
            break
        
        offset += limit

    return all_readings

def save_ecg_data_to_csv(readings, date):
    if not readings:
        print(f"No ECG data found for {date}")
        return

    data = []
    for reading in readings:
        start_time = datetime.strptime(reading['startTime'], '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=pytz.utc)
        scaling_factor = reading['scalingFactor']
        sampling_frequency = reading['samplingFrequencyHz']
        for i, sample in enumerate(reading['waveformSamples']):
            timestamp = start_time + timedelta(seconds=i / sampling_frequency)
            data.append({
                'Timestamp': timestamp.strftime('%H:%M'),  # Format to HH:mm
                'ECG Voltage (mV)': sample / scaling_factor
            })
    
    df = pd.DataFrame(data)
    output_path = f'ecg_data_{date}.csv'
    df.to_csv(output_path, index=False)
    print(f"ECG data for {date} saved to {output_path}")

def main():
    date = input("Enter the date in format yyyy-MM-dd: ")
    access_token = get_access_token()
    ecg_data = fetch_ecg_data(access_token, date)
    save_ecg_data_to_csv(ecg_data, date)

if __name__ == '__main__':
    main()
