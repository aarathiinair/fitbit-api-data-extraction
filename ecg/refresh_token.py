import base64
import requests
import json
import os
from urllib.parse import urlencode

# Define constants
CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
TOKEN_FILE = 'fitbit_tokens.json'

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

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
    print("Refresh Token Response:", tokens)
    return tokens['access_token']

if __name__ == '__main__':
    tokens = load_tokens()
    if tokens:
        refresh_access_token(tokens['refresh_token'])
    else:
        print("No tokens found. Please run get_tokens.py first.")
