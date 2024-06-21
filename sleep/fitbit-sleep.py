import base64
import requests
import pandas as pd
import json
import os
from urllib.parse import urlencode
from datetime import datetime


CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
API_URL = 'https://api.fitbit.com/1.2/user/-/sleep/date/'
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
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=urlencode(data))
    print("Refresh Token Response Status Code:", response.status_code)
    print("Refresh Token Response Content:", response.content)
    
    if response.status_code != 200:
        raise Exception(f"Failed to refresh token: {response.status_code}, {response.content}")
    
    response.raise_for_status()
    tokens = response.json()
    save_tokens(tokens)
    return tokens['access_token']

def fetch_sleep_data(access_token, date):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    response = requests.get(API_URL + f'{date}.json', headers=headers)
    print("Initial Sleep Data Response Status Code:", response.status_code)
    if response.status_code == 401:  # Unauthorized, likely need to refresh token
        tokens = load_tokens()
        if not tokens or 'refresh_token' not in tokens:
            raise Exception("No refresh token available.")
        access_token = refresh_access_token(tokens['refresh_token'])
        headers['Authorization'] = f'Bearer {access_token}'
        response = requests.get(API_URL + f'{date}.json', headers=headers)
    
    print("Final Sleep Data Response Status Code:", response.status_code)
    response.raise_for_status()
    return response.json()

def save_sleep_data_to_csv(data, date):
    if not data.get('sleep'):
        print(f"No sleep data found for {date}.")
        return

    sleep = data['sleep'][0]
    sleep_levels = sleep['levels']['summary']
    start_time = datetime.strptime(sleep['startTime'], '%Y-%m-%dT%H:%M:%S.%f')
    end_time = datetime.strptime(sleep['endTime'], '%Y-%m-%dT%H:%M:%S.%f')
    
    df = pd.DataFrame({
        'Date': [date],
        'Deep (minutes)': [sleep_levels['deep']['minutes']],
        'REM (minutes)': [sleep_levels['rem']['minutes']],
        'Light (minutes)': [sleep_levels['light']['minutes']],
        'Awake (minutes)': [sleep_levels['wake']['minutes']],
        'Sleep Start Time': [start_time.strftime('%H:%M')],
        'Sleep End Time': [end_time.strftime('%H:%M')],
    })
    df.to_csv(f'sleep_data_{date}.csv', index=False)
    print(f'Sleep data for {date} saved to sleep_data_{date}.csv')

def main():
    date = input("Enter the date in format yyyy-MM-dd: ")
    access_token = get_access_token()
    sleep_data = fetch_sleep_data(access_token, date)
    save_sleep_data_to_csv(sleep_data, date)

if __name__ == '__main__':
    main()

