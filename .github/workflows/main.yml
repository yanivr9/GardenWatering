import time
import json
import hmac
import hashlib
import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# סודות Tuya
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_KEY = os.getenv("TUYA_ACCESS_KEY")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
BASE_URL = "https://openapi.tuyaeu.com"

# סודות Email
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") 
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def sign(msg: str) -> str:
    return hmac.new(ACCESS_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest().upper()

def get_token() -> str:
    t = str(int(time.time() * 1000))
    path = "/v1.0/token?grant_type=1"
    empty_body_hash = hashlib.sha256(b"").hexdigest()
    sign_str = ACCESS_ID + t + "GET\n" + empty_body_hash + "\n\n" + path
    headers = {"client_id": ACCESS_ID, "sign": sign(sign_str), "t": t, "sign_method": "HMAC-SHA256"}
    
    r = requests.get(BASE_URL + path, headers=headers)
    return r.json()["result"]["access_token"]

def get_device_status():
    token = get_token()
    t = str(int(time.time() * 1000))
    path = f"/v1.0/iot-03/devices/{DEVICE_ID}/status"
    sign_str = ACCESS_ID + token + t + "GET\n" + hashlib.sha256(b"").hexdigest() + "\n\n" + path
    headers = {"client_id": ACCESS_ID, "access_token": token, "sign": sign(sign_str), "t": t, "sign_method": "HMAC-SHA256"}
    
    r = requests.get(BASE_URL + path, headers=headers)
    return r.json()

def send_email_report(battery_level):
    # הגדרת נושא ותוכן המייל בהתאם לרמת הסוללה
    if battery_level < 20:
        subject = f"⚠️ התראת מערכת השקיה: סוללה נמוכה בברז! ({battery_level}%)"
        body = f"רמת הסוללה בברז הגינה ירדה ל-{battery_level}%.\nנא להחליף סוללות בהקדם כדי שההשקיה לא תיעצר."
    else:
        subject = f"✅ עדכון מערכת השקיה יומית: סוללה תקינה ({battery_level}%)"
        body = f"הבדיקה היומית בוצעה בהצלחה.\nרמת הסוללה בברז הגינה היא כעת {battery_level}% והכל תקין."
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        # התחברות לשרת ה-SMTP של Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[EMAIL] הדיווח היומי נשלח למייל בהצלחה!")
    except Exception as e:
        print(f"[EMAIL] ❌ שגיאה בשליחת אימייל: {e}")

if __name__ == "__main__":
    print("בודק סטטוס סוללה מול השרת של Tuya...")
    data = get_device_status()
    
    battery_level = None
    for item in data.get("result", []):
        if "battery" in item["code"].lower():
            battery_level = int(item["value"])
            break
            
    if battery_level is not None:
        print(f"רמת סוללה נוכחית שחולצה: {battery_level}%")
        print("שולח את הדיווח למייל...")
        send_email_report(battery_level)
    else:
        print("❌ לא נמצאו נתוני סוללה בתשובת השרת.")
