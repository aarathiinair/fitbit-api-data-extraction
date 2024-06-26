import requests
import base64
import json
import datetime
import csv
import os

# Replace these with your actual details
CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
TOKEN_FILE = 'fitbit_tokens.json'  # File to store tokens

# Load Tokens
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token_file:
            tokens = json.load(token_file)
            return tokens.get("access_token"), tokens.get("refresh_token")
    return None, None

# Refresh Access Token
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
    print("Refresh Token Response:", response_json)  # Print the response for debugging
    if "access_token" in response_json and "refresh_token" in response_json:
        save_tokens(response_json["access_token"], response_json["refresh_token"])
        return response_json["access_token"], response_json["refresh_token"]
    else:
        print("Error: No access token or refresh token found in the response.")
        return None, None

# Save Tokens
def save_tokens(access_token, refresh_token):
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    with open(TOKEN_FILE, 'w') as token_file:
        json.dump(tokens, token_file)
    print(f"Tokens saved to {TOKEN_FILE}")

# Function to get Accelerometer data
def get_accelerometer_data(access_token, date):
    url = f"https://api.fitbit.com/1/user/-/activities/accelerometer/date/{date}/1d.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Accelerometer Data Response Status Code: {response.status_code}")
    if response.status_code == 200:
        response_json = response.json()
        print(f"Accelerometer Data Response: {json.dumps(response_json, indent=2)}")
        return response_json
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to save accelerometer data to a CSV file
def save_accelerometer_data_to_csv(accelerometer_data, date, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'x', 'y', 'z']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in accelerometer_data['activities-accelerometer-intraday']['dataset']:
                writer.writerow({
                    'timestamp': entry['time'],
                    'x': entry['value']['x'],
                    'y': entry['value']['y'],
                    'z': entry['value']['z']
                })
            print(f"Accelerometer data saved to {filename}")
    except Exception as e:
        print(f"Failed to save accelerometer data: {e}")

# Main function to run the script
if __name__ == "__main__":
    ACCESS_TOKEN, REFRESH_TOKEN = load_tokens()
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        print("No existing tokens found. Please run the token generation script to get new tokens.")
        exit(1)

    if ACCESS_TOKEN:
        # Take user input for the date
        date_input = input("Enter the date (YYYY-MM-DD): ")
        
        try:
            # Validate the date format
            datetime.datetime.strptime(date_input, "%Y-%m-%d")
            
            # Define a file path where the script is being run
            current_directory = os.getcwd()

            # Fetch Accelerometer data for the specified date
            accelerometer_data = get_accelerometer_data(ACCESS_TOKEN, date_input)

            if accelerometer_data and 'activities-accelerometer-intraday' in accelerometer_data:
                print("Accelerometer Data:", accelerometer_data['activities-accelerometer-intraday']['dataset'])
            else:
                print("No Accelerometer data found for the specified date.")

            # Sanitize the filename
            sanitized_filename = f"accelerometer_data_{date_input}.csv"

            # Save the accelerometer data to a CSV file
            csv_filename = os.path.join(current_directory, sanitized_filename)
            print(f"Saving accelerometer data to {csv_filename}")
            save_accelerometer_data_to_csv(accelerometer_data, date_input, csv_filename)
            
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
        
        # Refresh the access token if it has expired or about to expire
        ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    else:
        print("Failed to obtain access token.")
