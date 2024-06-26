import requests
import base64
import json
import os

CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
TOKEN_FILE = 'fitbit_tokens.json'

def save_tokens(access_token, refresh_token):
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    with open(TOKEN_FILE, 'w') as token_file:
        json.dump(tokens, token_file)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token_file:
            tokens = json.load(token_file)
            return tokens.get("access_token"), tokens.get("refresh_token")
    return None, None

def refresh_access_token(client_id, client_secret, refresh_token):
    token_url = "https://api.fitbit.com/oauth2/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    response = requests.post(token_url, headers=headers, data=body)
    response_json = response.json()
    print("Refresh Token Response:", response_json)
    if "access_token" in response_json and "refresh_token" in response_json:
        save_tokens(response_json["access_token"], response_json["refresh_token"])
        return response_json["access_token"], response_json["refresh_token"]
    else:
        print("Error: No access token or refresh token found in the response.")
        return None, None

def check_and_refresh_tokens():
    access_token, refresh_token = load_tokens()
    if not access_token or not refresh_token:
        print("No tokens found. Please run the initial authorization process.")
        exit(1)

    return refresh_access_token(CLIENT_ID, CLIENT_SECRET, refresh_token)

if __name__ == "__main__":
    check_and_refresh_tokens()
