import os
import time
import json
import asyncio
from http.server import BaseHTTPRequestHandler
import httpx

import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase (only once)
if not firebase_admin._apps:
    FIREBASE_CONFIG = json.loads(os.environ.get("FIREBASE_CONFIG", "{}"))
    cred = credentials.Certificate(FIREBASE_CONFIG)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://number-bot-9a5bd-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8871803888:AAEOV3_UI1_7dEc4oFhwA2mgY2bkN8cO84Y")
SMS_BOWER_API_KEY = os.environ.get("SMS_BOWER_API_KEY", "88J8QPh2vPkrzJZuP7GS6Xh8OfTdWzCJ")


def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        httpx.post(url, json=payload, timeout=5.0)
    except Exception as e:
        print(f"Error sending telegram msg: {e}")

def send_telegram_message_with_keyboard(chat_id, text, keyboard):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    try:
        httpx.post(url, json=payload, timeout=5.0)
    except Exception as e:
        print(f"Error sending telegram msg with keyboard: {e}")

def confirm_api(activation_id):
    url = "https://smsbower.app/stubs/handler_api.php"
    params = {
        'api_key': SMS_BOWER_API_KEY,
        'action': 'setStatus',
        'status': 6,
        'id': activation_id
    }
    try:
        httpx.get(url, params=params, timeout=5.0)
    except Exception as e:
        print(f"API confirm error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            payload = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad Request")
            return

        activation_id = str(payload.get('activationId', '')).strip()
        code = str(payload.get('code', '')).strip()

        if not activation_id or not code:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            return

        print(f"Received webhook for {activation_id}, code {code}")

        # Always return 200 OK immediately so SMSBower doesn't retry
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
        
        # Now process the logic
        try:
            # 1. Fetch activation data
            ref = db.reference(f'active_activations/{activation_id}')
            data = ref.get()
            
            if not data:
                print(f"Activation {activation_id} not found.")
                return

            user_id = data.get('user_id')
            price = data.get('price', 0)
            phone = data.get('phone', '')
            service = data.get('service', '')
            country = data.get('country', '')

            if not user_id:
                return

            # 2. Deduct balance
            user_ref = db.reference(f'users/{user_id}')
            user = user_ref.get()
            if user:
                user_ref.update({
                    'balance': user['balance'] - price,
                    'total_otps': user['total_otps'] + 1,
                    'total_cost': user['total_cost'] + price
                })

            # 3. Confirm with SMSBower API
            confirm_api(activation_id)

            # 4. Delete activation from Firebase
            ref.delete()

            # 5. Send Telegram Messages
            masked_phone = '*' * (len(phone) - 3) + phone[-3:] if len(phone) > 3 else phone

            msg_user = (f"🌍 Country: {country}\n"
                        f"⚙ Service: `{service}`\n"
                        f"☎ Number: `{phone}`\n\n"
                        f"🔐 Code: `{code}`\n\n"
                        f"`{code} is your {service} code. Don't share it.`")

            msg_group = (f"🌍 Country: {country}\n"
                         f"⚙ Service: `{service}`\n"
                         f"☎ Number: `{masked_phone}`\n\n"
                         f"🔐 Code: `{code}`\n\n"
                         f"`{code} is your {service} code. Don't share it.`")

            # Send to user
            send_telegram_message(user_id, msg_user)

            # Send to group
            group_kb = [[
                {"text": "⚡ Get Number", "url": "https://t.me/Active_Number_robot"},
                {"text": "📢 Join Channel", "url": "https://t.me/Active_Number_Update"}
            ]]
            send_telegram_message_with_keyboard("@Active_Number_Otp", msg_group, group_kb)

        except Exception as e:
            print(f"Error processing webhook: {e}")
