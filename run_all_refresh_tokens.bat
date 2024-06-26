@echo off

cd "C:\Users\91813\Downloads\fitbit\ecg"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > ecg_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\hrv"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > hrv_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\steps (interval)"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > steps_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\heart rate (interval)"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > heart_rate_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\body temp"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > body_temp_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\spo2"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > spo2_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\rr"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > rr_log.txt 2>&1

cd "C:\Users\91813\Downloads\fitbit\sleep"
"C:\Users\91813\AppData\Local\Programs\Python\Python38\python.exe" refresh_token.py > sleep_log.txt 2>&1
