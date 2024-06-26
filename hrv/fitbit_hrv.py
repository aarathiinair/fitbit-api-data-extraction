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

# Function to get HRV Intraday data
def get_hrv_intraday_data(access_token, start_date, end_date):
    url = f"https://api.fitbit.com/1/user/-/hrv/date/{start_date}/{end_date}/all.json"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"HRV Intraday Data Response Status Code: {response.status_code}")
    if response.status_code == 200:
        response_json = response.json()
        print(f"HRV Intraday Data Response: {json.dumps(response_json, indent=2)}")
        return response_json
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Interpolate data to get one-minute variations
def interpolate_data(minute_data, start_datetime, end_datetime):
    interpolated_data = []
    current_datetime = start_datetime
    while current_datetime <= end_datetime:
        closest_entry_before = None
        closest_entry_after = None
        for entry in minute_data:
            entry_datetime = datetime.datetime.strptime(entry['minute'], "%Y-%m-%dT%H:%M:%S.%f")
            if entry_datetime <= current_datetime:
                closest_entry_before = entry
            if entry_datetime > current_datetime and closest_entry_after is None:
                closest_entry_after = entry
                break
        if closest_entry_before and closest_entry_after:
            before_time = datetime.datetime.strptime(closest_entry_before['minute'], "%Y-%m-%dT%H:%M:%S.%f")
            after_time = datetime.datetime.strptime(closest_entry_after['minute'], "%Y-%m-%dT%H:%M:%S.%f")
            time_diff = (after_time - before_time).total_seconds() / 60
            weight_before = (after_time - current_datetime).total_seconds() / 60 / time_diff
            weight_after = (current_datetime - before_time).total_seconds() / 60 / time_diff

            interpolated_entry = {
                'minute': current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                'value': {
                    'rmssd': closest_entry_before['value']['rmssd'] * weight_before + closest_entry_after['value']['rmssd'] * weight_after,
                    'coverage': closest_entry_before['value']['coverage'] * weight_before + closest_entry_after['value']['coverage'] * weight_after,
                    'hf': closest_entry_before['value']['hf'] * weight_before + closest_entry_after['value']['hf'] * weight_after,
                    'lf': closest_entry_before['value']['lf'] * weight_before + closest_entry_after['value']['lf'] * weight_after
                }
            }
            interpolated_data.append(interpolated_entry)
        current_datetime += datetime.timedelta(minutes=1)
    return interpolated_data

# Function to save combined data to a CSV file
def save_combined_data_to_csv(hrv_data, start_date, end_date, start_time, end_time, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Date', 'Time (HH:mm)', 'RMSSD (ms)', 'Data Coverage', 'High Frequency Power', 'Low Frequency Power']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            start_datetime = datetime.datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

            for entry in hrv_data:
                date = entry['dateTime']
                minute_data = entry.get('minutes', [])
                interpolated_data = interpolate_data(minute_data, start_datetime, end_datetime)
                for minute_entry in interpolated_data:
                    minute_datetime = datetime.datetime.strptime(minute_entry['minute'], "%Y-%m-%dT%H:%M:%S.%f")
                    if start_datetime <= minute_datetime <= end_datetime:
                        time = minute_datetime.strftime("%H:%M")
                        writer.writerow({
                            'Date': date,
                            'Time (HH:mm)': time,
                            'RMSSD (ms)': minute_entry['value']['rmssd'],
                            'Data Coverage': minute_entry['value']['coverage'],
                            'High Frequency Power': minute_entry['value']['hf'],
                            'Low Frequency Power': minute_entry['value']['lf']
                        })
            print(f"Combined data saved to {filename}")
    except Exception as e:
        print(f"Failed to save combined data: {e}")

# Function to sanitize filename
def sanitize_filename(filename):
    return filename.replace(':', '-')

# Main function to run the script
if __name__ == "__main__":
    ACCESS_TOKEN, REFRESH_TOKEN = load_tokens()
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        print("No existing tokens found. Please run the token generation script to get new tokens.")
        exit(1)

    if ACCESS_TOKEN:
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

            if start_date_input == end_date_input:
                hrv_data_response = get_hrv_intraday_data(ACCESS_TOKEN, start_date_input, end_date_input)
                if hrv_data_response and 'hrv' in hrv_data_response:
                    hrv_data = hrv_data_response['hrv']
            else:
                hrv_data_start_date = get_hrv_intraday_data(ACCESS_TOKEN, start_date_input, start_date_input)
                if hrv_data_start_date and 'hrv' in hrv_data_start_date:
                    hrv_data.extend(hrv_data_start_date['hrv'])

                # Fetch full days in between
                current_date = (datetime.datetime.strptime(start_date_input, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                while current_date < end_date_input:
                    full_day_data = get_hrv_intraday_data(ACCESS_TOKEN, current_date, current_date)
                    if full_day_data and 'hrv' in full_day_data:
                        hrv_data.extend(full_day_data['hrv'])
                    current_date = (datetime.datetime.strptime(current_date, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

                # Fetch data for the end date
                hrv_data_end_date = get_hrv_intraday_data(ACCESS_TOKEN, end_date_input, end_date_input)
                if hrv_data_end_date and 'hrv' in hrv_data_end_date:
                    hrv_data.extend(hrv_data_end_date['hrv'])

            if hrv_data:
                print("Combined HRV Intraday Data:", hrv_data)
            else:
                print("No HRV Intraday data found for the specified date and time range.")

            # Sanitize the filename
            sanitized_filename = sanitize_filename(f"hrv_data_{start_date_input}_{start_time_input}_to_{end_date_input}_{end_time_input}.csv")

            # Save the combined data to a CSV file
            csv_filename = os.path.join(current_directory, sanitized_filename)
            print(f"Saving combined data to {csv_filename}")
            save_combined_data_to_csv(hrv_data, start_date_input, end_date_input, start_time_input, end_time_input, csv_filename)
            
        except ValueError:
            print("Invalid date or time format. Please enter the date in YYYY-MM-DD format and time in HH:mm format.")
        
        # Refresh the access token if it has expired or about to expire
        ACCESS_TOKEN, REFRESH_TOKEN = refresh_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    else:
        print("Failed to obtain access token.")
