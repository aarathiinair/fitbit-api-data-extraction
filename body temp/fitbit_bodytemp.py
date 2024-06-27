import base64
import requests
import json
import os
import datetime
import csv

CLIENT_ID = '23PHMD'
CLIENT_SECRET = '0ce3a7d7167a733fd9a3b5c23a3438f6'
TOKEN_FILE = 'fitbit_tokens.json'

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token_file:
            tokens = json.load(token_file)
            return tokens.get("access_token"), tokens.get("refresh_token")
    return None, None

def save_tokens(access_token, refresh_token):
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    with open(TOKEN_FILE, 'w') as token_file:
        json.dump(tokens, token_file)
    print(f"Tokens saved to {TOKEN_FILE}")

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
    if "access_token" in response_json:
        new_access_token = response_json["access_token"]
        save_tokens(new_access_token, refresh_token)
        return new_access_token
    else:
        print("Error: No access token found in the response.")
        return None

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

def main():
    access_token, refresh_token = load_tokens()
    if not access_token:
        if refresh_token:
            access_token = refresh_access_token(CLIENT_ID, CLIENT_SECRET, refresh_token)
            if not access_token:
                print("Failed to refresh access token. Exiting.")
                exit(1)
        else:
            print("No existing tokens found. Please run the token generation script to get new tokens.")
            exit(1)

    date_input = input("Enter the date (YYYY-MM-DD): ")
    
    try:
        datetime.datetime.strptime(date_input, "%Y-%m-%d")
        
        temperature_data = get_temperature_data(access_token, date_input)
        if temperature_data:
            print("Temperature Data:", json.dumps(temperature_data, indent=2))
        else:
            print("No Temperature data found for the specified date.")

        csv_filename = f"temperature_data_{date_input}.csv"
        print(f"Saving temperature data to {csv_filename}")
        save_temperature_data_to_csv(date_input, temperature_data, csv_filename)
        
    except ValueError:
        print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

if __name__ == "__main__":
    main()
