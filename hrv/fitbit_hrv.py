# fitbit_hrv.py
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
    if response.status_code != 200:
        print(f"Error obtaining initial tokens: {response.status_code} - {response.text}")
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
    if response.status_code != 200:
        print(f"Error refreshing tokens: {response.status_code} - {response.text}")
        response.raise_for_status()
    new_tokens = response.json()
    save_tokens(new_tokens)
    print("Tokens refreshed successfully.")
    return new_tokens['access_token'], new_tokens['refresh_token']

def check_and_refresh_tokens():
    tokens = load_tokens()
    if not tokens:
        print("No tokens found. Please authorize the application.")
        authorization_code = input("Enter the authorization code: ")
        tokens = get_initial_tokens(authorization_code)
        return tokens['access_token'], tokens['refresh_token']

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
        # Prompt for a new authorization code if refresh token is invalid
        authorization_code = input("Access token invalid or refresh token expired. Please enter a new authorization code: ")
        tokens = get_initial_tokens(authorization_code)
        return tokens['access_token'], tokens['refresh_token']

def get_hrv_intraday_data(access_token, start_date, end_date):
    url = f"https://api.fitbit.com/1/user/-/hrv/date/{start_date}/{end_date}/all.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"HRV Intraday Data Response Status Code: {response.status_code}")
    if response.status_code == 401:  # Token expired, refresh it
        access_token, refresh_token = check_and_refresh_tokens()
        headers["Authorization"] = f"Bearer {access_token}"
        response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        print(f"HRV Intraday Data Response: {json.dumps(response_json, indent=2)}")
        return response_json
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to save combined data to a CSV file
def save_combined_data_to_csv(hrv_data, start_date, end_date, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'date', 'time', 'rmssd (ms)', 'coverage', 'hf', 'lf'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in hrv_data:
                date_time = entry['dateTime']
                for minute_data in entry['minutes']:
                    # Convert time to HH:mm format
                    time = datetime.datetime.strptime(minute_data['minute'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%H:%M')
                    writer.writerow({
                        'date': date_time,
                        'time': time,
                        'rmssd (ms)': minute_data['value']['rmssd'],
                        'coverage': minute_data['value']['coverage'],
                        'hf': minute_data['value']['hf'],
                        'lf': minute_data['value']['lf']
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

    if access_token is None:
        print("Failed to obtain access token. Exiting.")
        exit(1)

    # Take user input for the date and time range
    start_date_input = input("Enter the start date (YYYY-MM-DD): ")
    start_time_input = input("Enter the start time (HH:mm): ")
    end_date_input = input("Enter the end date (YYYY-MM-DD): ")
    end_time_input = input("Enter the end time (HH:mm): ")
    
    try:
        # Validate the date and time format
        datetime.datetime.strptime(start_date_input, "%Y-%m-%d")
        datetime.datetime.strptime(start_time_input, "%H:%M")
        datetime.datetime.strptime(end_date_input, "%Y-%m-%d")
        datetime.datetime.strptime(end_time_input, "%H:%M")
        
        # Define a file path where the script is being run
        current_directory = os.getcwd()

        # Fetch HRV Intraday data for the specified date and time range
        hrv_data = []

        hrv_data_response = get_hrv_intraday_data(access_token, start_date_input, end_date_input)
        if hrv_data_response and 'hrv' in hrv_data_response:
            hrv_data = hrv_data_response['hrv']
        
        if hrv_data:
            print("HRV Intraday Data:", hrv_data)
        else:
            print("No HRV Intraday data found for the specified date and time range.")

        # Sanitize the filename
        sanitized_filename = sanitize_filename(f"hrv_data_{start_date_input}_{start_time_input}_to_{end_date_input}_{end_time_input}.csv")

        # Save the combined data to a CSV file
        csv_filename = os.path.join(current_directory, sanitized_filename)
        print(f"Saving combined data to {csv_filename}")
        save_combined_data_to_csv(hrv_data, start_date_input, end_date_input, csv_filename)
    
    except ValueError:
        print("Invalid date or time format. Please enter the date in YYYY-MM-DD format and time in HH:mm format.")
