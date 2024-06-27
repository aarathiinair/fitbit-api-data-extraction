import requests
import base64
import json
import datetime
import csv
import os
from urllib.parse import urlencode

# Fitbit API credentials
CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'
TOKEN_FILE = 'fitbit_tokens.json'

# Save tokens to a file
def save_tokens(access_token, refresh_token):
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    with open(TOKEN_FILE, 'w') as token_file:
        json.dump(tokens, token_file)
    print(f"Tokens saved to {TOKEN_FILE}")

# Load tokens from a file
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token_file:
            tokens = json.load(token_file)
            return tokens.get("access_token"), tokens.get("refresh_token")
    return None, None

# Refresh the access token using the refresh token
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

# Check and refresh tokens if necessary
def check_and_refresh_tokens():
    access_token, refresh_token = load_tokens()
    if not access_token or not refresh_token:
        print("No tokens found. Please run the initial authorization process.")
        return None, None

    return refresh_access_token(CLIENT_ID, CLIENT_SECRET, refresh_token)

# Obtain new tokens using authorization code
def get_new_tokens():
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
    response = requests.post(token_url, headers=headers, data=urlencode(body))
    response_json = response.json()
    print("Token Response:", response_json)

    if "access_token" in response_json and "refresh_token" in response_json:
        save_tokens(response_json["access_token"], response_json["refresh_token"])
        return response_json["access_token"], response_json["refresh_token"]
    else:
        print("Error: Unable to retrieve tokens.")
        return None, None

# Function to get SpO2 data
def get_spo2_data(access_token, date):
    url = f"https://api.fitbit.com/1/user/-/spo2/date/{date}/{date}.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"SpO2 Data Response Status Code: {response.status_code}")
    print(f"SpO2 Data Response: {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to save SpO2 data to a CSV file
def save_spo2_data_to_csv(spo2_data, date, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['date', 'avg_spo2_percentage', 'min_spo2_percentage', 'max_spo2_percentage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for entry in spo2_data:
                writer.writerow({
                    'date': entry['dateTime'],
                    'avg_spo2_percentage': entry['value']['avg'],
                    'min_spo2_percentage': entry['value']['min'],
                    'max_spo2_percentage': entry['value']['max']
                })
            print(f"SpO2 data saved to {filename}")
    except PermissionError as e:
        print(f"Permission denied error: {e}")
    except Exception as e:
        print(f"Failed to save SpO2 data: {e}")

# Function to sanitize filename
def sanitize_filename(filename):
    return filename.replace(':', '-')

# Main function to run the script
if __name__ == "__main__":
    ACCESS_TOKEN, REFRESH_TOKEN = load_tokens()
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        ACCESS_TOKEN, REFRESH_TOKEN = get_new_tokens()
        if not ACCESS_TOKEN or not REFRESH_TOKEN:
            print("Failed to obtain new tokens. Exiting.")
            exit(1)

    ACCESS_TOKEN, REFRESH_TOKEN = check_and_refresh_tokens()
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        ACCESS_TOKEN, REFRESH_TOKEN = get_new_tokens()
        if not ACCESS_TOKEN or not REFRESH_TOKEN:
            print("Failed to refresh or obtain new tokens. Exiting.")
            exit(1)

    # Take user input for the date
    date_input = input("Enter the date (YYYY-MM-DD): ")
    
    try:
        # Validate the date format
        datetime.datetime.strptime(date_input, "%Y-%m-%d")
        
        # Define a file path where the script is being run
        current_directory = os.getcwd()

        # Fetch SpO2 data for the specified date
        spo2_data_response = get_spo2_data(ACCESS_TOKEN, date_input)
        if spo2_data_response:
            print(f"Received SpO2 Data: {json.dumps(spo2_data_response, indent=2)}")
            if isinstance(spo2_data_response, list) and len(spo2_data_response) > 0:
                spo2_data = spo2_data_response
            else:
                spo2_data = []
        else:
            spo2_data = []

        if spo2_data:
            print("SpO2 Data:", spo2_data)
        else:
            print("No SpO2 data found for the specified date.")

        # Sanitize the filename
        sanitized_filename = sanitize_filename(f"spo2_data_{date_input}.csv")

        # Save the SpO2 data to a CSV file
        csv_filename = os.path.join(current_directory, sanitized_filename)
        print(f"Saving SpO2 data to {csv_filename}")
        save_spo2_data_to_csv(spo2_data, date_input, csv_filename)
        
    except ValueError:
        print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
    
    ACCESS_TOKEN, REFRESH_TOKEN = check_and_refresh_tokens()
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        ACCESS_TOKEN, REFRESH_TOKEN = get_new_tokens()
        if not ACCESS_TOKEN or not REFRESH_TOKEN:
            print("Failed to refresh or obtain new tokens. Exiting.")
            exit(1)
    save_tokens(ACCESS_TOKEN, REFRESH_TOKEN)
