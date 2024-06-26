# get_initial_tokens.py

import base64
import requests
import json
from urllib.parse import urlencode

CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
TOKEN_FILE = 'fitbit_tokens.json'

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def get_initial_tokens(authorization_code):
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
    print("Initial tokens obtained and saved.")
    return tokens

if __name__ == "__main__":
    authorization_code = input("Enter the authorization code: ")
    get_initial_tokens(authorization_code)
