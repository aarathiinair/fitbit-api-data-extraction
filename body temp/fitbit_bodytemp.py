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

# Function to get Body Temperature data
def get_temperature_data(access_token, date):
    url = f"https://api.fitbit.com/1/user/-/temp/skin/date/{date}.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Temperature Data Response Status Code: {response.status_code}")
    print(f"Temperature Data Response: {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to save temperature data to a CSV file
def save_temperature_data_to_csv(date, temperature_data, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['date', 'nightly_relative_temperature_change']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            combined_data = {'date': date}
            if temperature_data and 'tempSkin' in temperature_data:
                temp_entry = temperature_data['tempSkin'][0]
                relative_temp = temp_entry['value']['nightlyRelative']
                combined_data.update({
                    'nightly_relative_temperature_change': relative_temp,
                })
            
            writer.writerow(combined_data)
            print(f"Temperature data saved to {filename}")
    except Exception as e:
        print(f"Failed to save temperature data: {e}")

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

            # Fetch Temperature data for the specified date
            temperature_data = get_temperature_data(ACCESS_TOKEN, date_input)
            if temperature_data:
                print("Temperature Data:", json.dumps(temperature_data, indent=2))
            else:
                print("No Temperature data found for the specified date.")

            # Save the temperature data to a CSV file
            csv_filename = os.path.join(current_directory, f"temperature_data_{date_input}.csv")
            print(f"Saving temperature data to {csv_filename}")
            save_temperature_data_to_csv(date_input, temperature_data, csv_filename)
            
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
        
        # Refresh the access token if it has expired or about to expire
        ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    else:
        print("Failed to obtain access token.")
