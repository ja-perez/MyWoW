from coinbase import jwt_generator # type: ignore
import threading
import websocket
import json
import jwt
import hashlib

from dotenv import dotenv_values
import datetime
import time
import os

config = dotenv_values('.env')
api_key = config['COINBASE_API_KEY']
api_secret = config['COINBASE_API_SECRET']

WS_API_URL = 'wss://advanced-trade-ws.coinbase.com'
ALGORITHM = 'ES256'

jwt_token = jwt_generator.build_ws_jwt(api_key, api_secret)
jwt_expiration = 120 # 2 minutes : 120 seconds

candle_subscription = {
    'type': 'subscribe',
    'product_ids': ['BTC-USD', 'ETH-USD'],
    'channel': 'level2',
    'jwt': jwt_token
}

candle_unsubscription = {
    'type': 'unsubscribe',
    'channel': 'level2',
    'jwt': jwt_token
}

def sign_with_jwt(message, channel, product_ids):
    payload = {
        'iss': 'coinbase-cloud',
        'nbf': int(time.time()),
        'exp': int(time.time()) + jwt_expiration,
        'sub': api_key
    }
    headers = {
        'kid': api_key,
        'nonce': hashlib.sha256(os.urandom(16)).hexdigest()
    }
    token = jwt.encode(payload, api_secret, algorithm=ALGORITHM, headers=headers)
    message['jwt'] = token
    return message

def subscribe_to_products(ws, product_ids, channel_name):
    message = {
        'type': 'subscribe',
        'channel': channel_name,
        'product_ids': product_ids
    }
    signed_message = sign_with_jwt(message, channel_name, product_ids)
    ws.send(json.dumps(signed_message))

def unsubscribe_to_products(ws, product_ids, channel_name):
    message = {
        'type': 'unsubscribe',
        'channel': channel_name,
        'product_ids': product_ids
    }
    signed_message = sign_with_jwt(message, channel_name, product_ids)
    ws.send(json.dumps(signed_message))

def on_message(ws, message):
    data = json.loads(message)
    data_path = os.path.join(os.getcwd(), 'data', 'websockets', 'level2', f'{datetime.datetime.now().strftime('%H_%M_%S')}.json')
    with open(data_path, 'w') as f:
        json.dump(data, f, indent=4)

def on_open(ws):
    product_ids = ['BTC-USD']
    subscribe_to_products(ws, product_ids, 'level2')

def start_websocket():
    ws = websocket.WebSocketApp(WS_API_URL, on_open=on_open, on_message=on_message)
    ws.run_forever()

def main():
    ws_thread = threading.Thread(target=start_websocket)
    ws_thread.start()

    sent_unsub = False
    start_time = datetime.datetime.now(datetime.timezone.utc)

    try:
        while True:
            seconds_passed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
            if seconds_passed > 2 and not sent_unsub:
                ws = websocket.create_connection(WS_API_URL)
                unsubscribe_to_products(ws, ['BTC-USD'], 'level2')
                ws.close()
                sent_unsub = True
            time.sleep(1)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    main()