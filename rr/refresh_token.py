# refresh_token.py

import base64
import requests
import json
import os
from urllib.parse import urlencode

CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
TOKEN_FILE = 'fitbit_tokens.json'
API_URL = 'https://api.fitbit.com/1/user/-/ecg/list.json'

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def refresh_access_token():
    tokens = load_tokens()
    if not tokens:
        print("No tokens found.")
        return

    refresh_token = tokens['refresh_token']
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
    response.raise_for_status()
    new_tokens = response.json()
    save_tokens(new_tokens)
    print("Tokens refreshed successfully.")
    return new_tokens

def fetch_data(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Data fetched successfully.")
    return data

if __name__ == "__main__":
    tokens = refresh_access_token()
    if tokens:
        fetch_data(tokens['access_token'])
