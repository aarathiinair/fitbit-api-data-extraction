import requests
import json
import datetime
import csv
import os
from refresh_token import check_and_refresh_tokens, load_tokens, save_tokens

def get_heart_rate_intraday_data(access_token, date, start_time=None, end_time=None, detail_level='1min'):
    base_url = f"https://api.fitbit.com/1/user/-/activities/heart/date/{date}/1d/{detail_level}"
    if start_time and end_time:
        url = f"{base_url}/time/{start_time}/{end_time}.json"
    else:
        url = f"{base_url}.json"
        
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Heart Rate Intraday Data Response Status Code: {response.status_code}")
    if response.status_code == 200:
        response_json = response.json()
        print(f"Heart Rate Intraday Data Response: {json.dumps(response_json, indent=2)}")
        return response_json
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def save_combined_data_to_csv(heart_rate_data, start_date, end_date, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'date', 'time', 'heart_rate'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            current_date = start_date
            for entry in heart_rate_data:
                try:
                    if 'T' in entry['time']:
                        date, time = entry['time'].split('T')
                    else:
                        date = current_date
                        time = entry['time']
                    time_without_seconds = time[:5]  # Remove seconds part
                    writer.writerow({
                        'date': date,
                        'time': time_without_seconds,
                        'heart_rate': entry['value']
                    })
                    if time == '23:59:00':
                        current_date = (datetime.datetime.strptime(current_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                except ValueError:
                    print(f"Skipping entry due to unexpected format: {entry}")
            print(f"Combined data saved to {filename}")
    except PermissionError as e:
        print(f"Failed to save combined data due to permission error: {e}")
        alternate_filename = os.path.join(os.path.expanduser('~'), 'Downloads', os.path.basename(filename))
        print(f"Attempting to save the data to an alternate location: {alternate_filename}")
        try:
            with open(alternate_filename, 'w', newline='') as csvfile:
                fieldnames = [
                    'date', 'time', 'heart_rate'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                current_date = start_date
                for entry in heart_rate_data:
                    try:
                        if 'T' in entry['time']:
                            date, time = entry['time'].split('T')
                        else:
                            date = current_date
                            time = entry['time']
                        time_without_seconds = time[:5]  # Remove seconds part
                        writer.writerow({
                            'date': date,
                            'time': time_without_seconds,
                            'heart_rate': entry['value']
                        })
                        if time == '23:59:00':
                            current_date = (datetime.datetime.strptime(current_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    except ValueError:
                        print(f"Skipping entry due to unexpected format: {entry}")
                print(f"Combined data saved to {alternate_filename}")
        except Exception as e:
            print(f"Failed to save combined data to alternate location: {e}")
    except Exception as e:
        print(f"Failed to save combined data due to an unexpected error: {e}")

def sanitize_filename(filename):
    return filename.replace(':', '-')

if __name__ == "__main__":
    ACCESS_TOKEN, REFRESH_TOKEN = load_tokens()
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        print("No tokens found. Please run get_tokens.py first.")
        exit(1)

    ACCESS_TOKEN, REFRESH_TOKEN = check_and_refresh_tokens()

    start_date_input = input("Enter the start date (YYYY-MM-DD): ")
    start_time_input = input("Enter the start time (HH:mm): ")
    end_date_input = input("Enter the end date (YYYY-MM-DD): ")
    end_time_input = input("Enter the end time (HH:mm): ")
    
    try:
        datetime.datetime.strptime(start_date_input, "%Y-%m-%d")
        datetime.datetime.strptime(start_time_input, "%H:%M")
        datetime.datetime.strptime(end_date_input, "%Y-%m-%d")
        datetime.datetime.strptime(end_time_input, "%H:%M")
        
        current_directory = os.getcwd()
        heart_rate_data = []
        heart_rate_data_start_date = get_heart_rate_intraday_data(ACCESS_TOKEN, start_date_input, start_time_input, "23:59")
        if heart_rate_data_start_date and 'activities-heart-intraday' in heart_rate_data_start_date:
            heart_rate_data.extend(heart_rate_data_start_date['activities-heart-intraday']['dataset'])
        heart_rate_data_end_date = get_heart_rate_intraday_data(ACCESS_TOKEN, end_date_input, "00:00", end_time_input)
        if heart_rate_data_end_date and 'activities-heart-intraday' in heart_rate_data_end_date:
            heart_rate_data.extend(heart_rate_data_end_date['activities-heart-intraday']['dataset'])

        if heart_rate_data:
            print("Combined Heart Rate Intraday Data:", heart_rate_data)
        else:
            print("No Heart Rate Intraday data found for the specified date and time range.")

        sanitized_filename = sanitize_filename(f"heart_rate_data_{start_date_input}_{start_time_input}_to_{end_date_input}_{end_time_input}.csv")
        csv_filename = os.path.join(current_directory, sanitized_filename)
        print(f"Saving combined data to {csv_filename}")
        save_combined_data_to_csv(heart_rate_data, start_date_input, end_date_input, csv_filename)
        
    except ValueError:
        print("Invalid date or time format. Please enter the date in YYYY-MM-DD format and time in HH:mm format.")
    
    ACCESS_TOKEN, REFRESH_TOKEN = check_and_refresh_tokens()
    save_tokens(ACCESS_TOKEN, REFRESH_TOKEN)
