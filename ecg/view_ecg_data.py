import pandas as pd

# Specify the path to your CSV file
file_path = 'ecg_data_2024-06-27.csv'  # Replace this with the actual path

# Load the CSV file
ecg_data = pd.read_csv(file_path)

# Display the first few rows of the DataFrame
print(ecg_data.head(10))

# Save the DataFrame to a new CSV file (optional)
ecg_data.to_csv('new_ecg_data.csv', index=False)
