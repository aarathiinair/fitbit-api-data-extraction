import requests
import json
import datetime
import csv
import os
from refresh_token import check_and_refresh_tokens

def get_breathing_rate_intraday_data(access_token, start_date, end_date):
    url = f"https://api.fitbit.com/1/user/-/br/date/{start_date}/{end_date}/all.json"
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
def save_combined_data_to_csv(breathing_data, start_date, end_date, filename):
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

        # Fetch Breathing Rate Intraday data for the specified date and time range
        breathing_data = []

        if start_date_input == end_date_input:
            breathing_data_response = get_breathing_rate_intraday_data(access_token, start_date_input, start_date_input)
            if breathing_data_response and 'br' in breathing_data_response:
                breathing_data = breathing_data_response['br']
        else:
            breathing_data_response_start = get_breathing_rate_intraday_data(access_token, start_date_input, start_date_input)
            if breathing_data_response_start and 'br' in breathing_data_response_start:
                breathing_data.extend(breathing_data_response_start['br'])
            
            # Fetch full days in between
            current_date = (datetime.datetime.strptime(start_date_input, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            while current_date < end_date_input:
                full_day_data = get_breathing_rate_intraday_data(access_token, current_date, current_date)
                if full_day_data and 'br' in full_day_data:
                    breathing_data.extend(full_day_data['br'])
                current_date = (datetime.datetime.strptime(current_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

            # Fetch data for the end date
            breathing_data_response_end = get_breathing_rate_intraday_data(access_token, end_date_input, end_date_input)
            if breathing_data_response_end and 'br' in breathing_data_response_end:
                breathing_data.extend(breathing_data_response_end['br'])

        if breathing_data:
            print("Combined Breathing Rate Intraday Data:", breathing_data)
        else:
            print("No Breathing Rate Intraday data found for the specified date and time range.")

        # Sanitize the filename
        sanitized_filename = sanitize_filename(f"breathing_data_{start_date_input}_{start_time_input}_to_{end_date_input}_{end_time_input}.csv")

        # Save the combined data to a CSV file
        csv_filename = os.path.join(current_directory, sanitized_filename)
        print(f"Saving combined data to {csv_filename}")
        save_combined_data_to_csv(breathing_data, start_date_input, end_date_input, csv_filename)
    
    except ValueError:
        print("Invalid date or time format. Please enter the date in YYYY-MM-DD format and time in HH:mm format.")
