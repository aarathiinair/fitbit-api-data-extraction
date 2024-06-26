import requests
import base64
import json

CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'

# Prompt the user to enter the authorization code
AUTHORIZATION_CODE = input("Enter the authorization code: ")

token_url = "https://api.fitbit.com/oauth2/token"
headers = {
    "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
    "Content-Type": "application/x-www-form-urlencoded"
}
body = {
    "client_id": CLIENT_ID,
    "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI,
    "code": AUTHORIZATION_CODE
}

response = requests.post(token_url, headers=headers, data=body)
response_json = response.json()
print("Token Response:", response_json)

# Save tokens to a file
with open('fitbit_tokens.json', 'w') as token_file:
    json.dump(response_json, token_file)
print("Tokens saved to fitbit_tokens.json")
