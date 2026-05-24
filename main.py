import time
import json
import hmac
import hashlib
import requests
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# סודות Tuya - נמשכים מ-GitHub Secrets
# =========================
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_KEY = os.getenv("TUYA_ACCESS_KEY")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
BASE_URL = "https://openapi.tuyaeu.com"

# =========================
# סודות Email - נמשכים מ-GitHub Secrets
# =========================
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
    is_low = battery_level < 20
    theme_color = "#d32f2f" if is_low else "#1f8b4c"
    icon = "⚠️" if is_low else "✅"
    status_title = "סטטוס סוללה: נמוך מאוד!" if is_low else "סטטוס סוללה: תקין"
    subject = f"{icon} עדכון מערכת השקיה: סוללה ב-{battery_level}%"
    
    message_text = (
        "<strong>שימו לב!</strong> רמת הסוללה בברז הגינה נמוכה קריטית. מומלץ להחליף סוללות <u>בהקדם</u> כדי להבטיח רצף השקיה ותקינות הצמחים."
        if is_low else
        "הבדיקה היומית בוצעה בהצלחה. הברז פועל כשורה, רמת הסוללה טובה ואין צורך בנקיטת פעולה."
    )

    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; margin: 0; padding: 30px 15px; }}
        .email-container {{ max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.08); border: 1px solid #e1e4e8; }}
        .header {{ background-color: #ffffff; color: #333333; padding: 20px; text-align: center; border-bottom: 1px solid #eeeeee; }}
        .header h2 {{ margin: 0; font-size: 20px; font-weight: 700; color: #2c3e50; }}
        .content {{ padding: 40px 25px; text-align: center; }}
        .status-title {{ font-size: 18px; font-weight: 600; margin-top: 0; margin-bottom: 25px; color: #555555; }}
        .battery-banner {{ background-color: {theme_color}; color: #ffffff !important; display: inline-block; padding: 15px 40px; border-radius: 50px; font-size: 64px; font-weight: 800; margin: 10px 0 30px 0; line-height: 1; box-shadow: 0 5px 15px rgba(0,0,0,0.15); letter-spacing: -2px; }}
        .message {{ font-size: 16px; line-height: 1.6; color: #444444; margin-bottom: 0; border-top: 1px solid #f0f0f0; padding-top: 25px; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eeeeee; font-size: 13px; color: #777777; }}
        .footer p {{ margin: 4px 0; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h2>🌿 בקרה: ברז השקיה חכם</h2>
        </div>
        <div class="content">
            <div class="status-title">{status_title}</div>
            <div class="battery-banner">{battery_level}%</div>
            <div class="message">{message_text}</div>
        </div>
        <div class="footer">
            <p>הסחלבים, הפטוניות והאמנון ותמר שלך בידיים טובות 🌿💧</p>
            <p class="small-text">נשלח אוטומטית באמצעות GitHub Actions</p>
        </div>
    </div>
</body>
</html>"""
    
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("[EMAIL] הדיווח המעוצב נשלח למייל בהצלחה!")
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
        print("שולח את הדיווח המעוצב למייל...")
        send_email_report(battery_level)
    else:
        print("❌ לא נמצאו נתוני סוללה בתשובת השרת.")

# =========================
# סוף הקובץ - ודא שהעתקת עד לכאן!
# =========================
