# fitbit_rr.py
import base64
import requests
import json
import datetime
import csv
import os
from urllib.parse import urlencode

CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
REDIRECT_URI = 'http://127.0.0.1:8080/'
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

def refresh_access_token():
    tokens = load_tokens()
    if not tokens:
        print("No tokens found.")
        return None, None

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
    return new_tokens['access_token'], new_tokens['refresh_token']

def check_and_refresh_tokens():
    tokens = load_tokens()
    if not tokens:
        print("No tokens found.")
        return None, None

    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    # Check if the token needs refreshing (e.g., if the access token is expired)
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        # Make a test request to check if the access token is valid
        test_url = 'https://api.fitbit.com/1/user/-/profile.json'
        response = requests.get(test_url, headers=headers)
        if response.status_code == 401:  # Unauthorized, token might be expired
            access_token, refresh_token = refresh_access_token()
        return access_token, refresh_token
    except requests.exceptions.RequestException as e:
        print(f"Error checking tokens: {e}")
        return None, None

def get_breathing_rate_intraday_data(access_token, date):
    url = f"https://api.fitbit.com/1/user/-/br/date/{date}/{date}/all.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Breathing Rate Intraday Data Response Status Code: {response.status_code}")
    if response.status_code == 401:  # Token expired, refresh it
        access_token, refresh_token = check_and_refresh_tokens()
        headers["Authorization"] = f"Bearer {access_token}"
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        print(f"Breathing Rate Intraday Data Response: {json.dumps(response_json, indent=2)}")
        return response_json
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to save combined data to a CSV file
def save_combined_data_to_csv(breathing_data, date, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'date', 'light_sleep_breathing_rate (breaths per minute)', 
                'deep_sleep_breathing_rate (breaths per minute)', 
                'rem_sleep_breathing_rate (breaths per minute)', 
                'full_sleep_breathing_rate (breaths per minute)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in breathing_data:
                writer.writerow({
                    'date': entry['dateTime'],
                    'light_sleep_breathing_rate (breaths per minute)': entry['value']['lightSleepSummary']['breathingRate'],
                    'deep_sleep_breathing_rate (breaths per minute)': entry['value']['deepSleepSummary']['breathingRate'],
                    'rem_sleep_breathing_rate (breaths per minute)': entry['value']['remSleepSummary']['breathingRate'],
                    'full_sleep_breathing_rate (breaths per minute)': entry['value']['fullSleepSummary']['breathingRate']
                })
            print(f"Combined data saved to {filename}")
    except Exception as e:
        print(f"Failed to save combined data: {e}")

# Function to sanitize filename
def sanitize_filename(filename):
    return filename.replace(':', '-')

# Main function to run the script
if __name__ == "__main__":
    # Ensure we have valid tokens
    access_token, refresh_token = check_and_refresh_tokens()

    # Take user input for the date
    date_input = input("Enter the date (YYYY-MM-DD): ")
    
    try:
        # Validate the date format
        datetime.datetime.strptime(date_input, "%Y-%m-%d")
        
        # Define a file path where the script is being run
        current_directory = os.getcwd()

        # Fetch Breathing Rate Intraday data for the specified date
        breathing_data_response = get_breathing_rate_intraday_data(access_token, date_input)
        breathing_data = breathing_data_response['br'] if breathing_data_response and 'br' in breathing_data_response else []

        if breathing_data:
            print("Breathing Rate Intraday Data:", breathing_data)
        else:
            print("No Breathing Rate Intraday data found for the specified date.")

        # Sanitize the filename
        sanitized_filename = sanitize_filename(f"breathing_data_{date_input}.csv")

        # Save the combined data to a CSV file
        csv_filename = os.path.join(current_directory, sanitized_filename)
        print(f"Saving combined data to {csv_filename}")
        save_combined_data_to_csv(breathing_data, date_input, csv_filename)
    
    except ValueError:
        print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
