import requests
import base64
import json

# Replace these with your actual details
CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'  # Ensure the trailing slash is included
TOKEN_FILE = 'fitbit_tokens.json'  # File to store tokens

def get_access_token(client_id, client_secret, redirect_uri, authorization_code):
    token_url = "https://api.fitbit.com/oauth2/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": authorization_code
    }
    response = requests.post(token_url, headers=headers, data=body)
    response_json = response.json()
    print("Access Token Response:", response_json)  # Print the response for debugging
    if "access_token" in response_json and "refresh_token" in response_json:
        save_tokens(response_json["access_token"], response_json["refresh_token"])
    else:
        print("Error: No access token or refresh token found in the response.")

def save_tokens(access_token, refresh_token):
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    with open(TOKEN_FILE, 'w') as token_file:
        json.dump(tokens, token_file)
    print(f"Tokens saved to {TOKEN_FILE}")

if __name__ == "__main__":
    authorization_code = input("Enter the new authorization code: ")
    get_access_token(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, authorization_code)
