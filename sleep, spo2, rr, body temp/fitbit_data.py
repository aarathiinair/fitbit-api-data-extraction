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

# Function to get Breathing Rate data
def get_breathing_rate_data(access_token, date):
    url = f"https://api.fitbit.com/1/user/-/br/date/{date}/all.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Breathing Rate Data Response Status Code: {response.status_code}")
    print(f"Breathing Rate Data Response: {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to get Sleep data
def get_sleep_data(access_token, date):
    url = f"https://api.fitbit.com/1.2/user/-/sleep/date/{date}.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Sleep Data Response Status Code: {response.status_code}")
    print(f"Sleep Data Response: {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to get Temperature data
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

# Function to save combined data to a CSV file
def save_combined_data_to_csv(date, spo2_data, breathing_rate_data, sleep_data, temperature_data, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'date', 'avg_spo2 (%)', 'min_spo2 (%)', 'max_spo2 (%)',
                'deep_sleep_breathing_rate (bpm)', 'rem_sleep_breathing_rate (bpm)',
                'light_sleep_breathing_rate (bpm)', 'full_sleep_breathing_rate (bpm)',
                'temperature_skin (°C or °F)', 'sleep_start_time', 'sleep_end_time',
                'sleep_duration', 'sleep_efficiency'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            combined_data = {'date': date}
            if spo2_data:
                spo2_entry = spo2_data[0]
                combined_data.update({
                    'avg_spo2 (%)': spo2_entry['value']['avg'],
                    'min_spo2 (%)': spo2_entry['value']['min'],
                    'max_spo2 (%)': spo2_entry['value']['max']
                })
            if breathing_rate_data and 'br' in breathing_rate_data:
                br_entry = breathing_rate_data['br'][0]
                combined_data.update({
                    'deep_sleep_breathing_rate (bpm)': br_entry['value']['deepSleepSummary']['breathingRate'],
                    'rem_sleep_breathing_rate (bpm)': br_entry['value']['remSleepSummary']['breathingRate'],
                    'light_sleep_breathing_rate (bpm)': br_entry['value']['lightSleepSummary']['breathingRate'],
                    'full_sleep_breathing_rate (bpm)': br_entry['value']['fullSleepSummary']['breathingRate']
                })
            if sleep_data and 'sleep' in sleep_data:
                sleep_entry = sleep_data['sleep'][0]
                combined_data.update({
                    'sleep_start_time': sleep_entry['startTime'],
                    'sleep_end_time': sleep_entry['endTime'],
                    'sleep_duration': sleep_entry['duration'] / 60000,  # convert to minutes
                    'sleep_efficiency': sleep_entry['efficiency']
                })
            if temperature_data and 'tempSkin' in temperature_data:
                temp_entry = temperature_data['tempSkin'][0]
                combined_data.update({
                    'temperature_skin (°C or °F)': temp_entry['value']['nightlyRelative']
                })
            
            writer.writerow(combined_data)
            print(f"Combined data saved to {filename}")
    except Exception as e:
        print(f"Failed to save combined data: {e}")

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

            # Fetch SpO2 data for the specified date
            spo2_data = get_spo2_data(ACCESS_TOKEN, date_input)
            if spo2_data:
                print("SpO2 Data:", spo2_data)
            else:
                print("No SpO2 data found for the specified date.")

            # Fetch Breathing Rate data for the specified date
            breathing_rate_data = get_breathing_rate_data(ACCESS_TOKEN, date_input)
            if breathing_rate_data:
                print("Breathing Rate Data:", breathing_rate_data)
            else:
                print("No Breathing Rate data found for the specified date.")
            
            # Fetch Sleep data for the specified date
            sleep_data = get_sleep_data(ACCESS_TOKEN, date_input)
            if sleep_data:
                print("Sleep Data:", sleep_data)
            else:
                print("No Sleep data found for the specified date.")
            
            # Fetch Temperature data for the specified date
            temperature_data = get_temperature_data(ACCESS_TOKEN, date_input)
            if temperature_data:
                print("Temperature Data:", temperature_data)
            else:
                print("No Temperature data found for the specified date.")

            # Save the combined data to a CSV file
            csv_filename = os.path.join(current_directory, f"combined_data_{date_input}.csv")
            print(f"Saving combined data to {csv_filename}")
            save_combined_data_to_csv(date_input, spo2_data, breathing_rate_data, sleep_data, temperature_data, csv_filename)
            
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
        
        # Refresh the access token if it has expired or about to expire
        ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    else:
        print("Failed to obtain access token.")
