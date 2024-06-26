import base64
import requests
import json
from urllib.parse import urlencode

# Define constants
CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'
TOKEN_URL = 'https://api.fitbit.com/oauth2/token'

# Step 1: Get the access token
def get_access_token():
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
    
    print("Requesting access token with the following headers and data:")
    print(headers)
    print(data)
    
    response = requests.post(TOKEN_URL, headers=headers, data=urlencode(data))
    
    print("Response status code:", response.status_code)
    print("Response content:", response.content)
    
    response.raise_for_status()
    return response.json()['access_token'], response.json()['refresh_token']

# Main function
def main():
    access_token, refresh_token = get_access_token()
    print(f'Access Token: {access_token}')
    print(f'Refresh Token: {refresh_token}')
    
    # Save the tokens to the token file
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    with open('fitbit_tokens.json', 'w') as token_file:
        json.dump(tokens, token_file)
    print('Tokens saved to fitbit_tokens.json')

if __name__ == '__main__':
    main()
