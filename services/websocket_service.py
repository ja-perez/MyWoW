from coinbase import jwt_generator # type: ignore
from dotenv import dotenv_values
from typing import Optional
from contextlib import closing
import datetime
import threading
import websocket
import json
import time
import os

class WebsocketService:
    WS_URL = "wss://advanced-trade-ws.coinbase.com"
    ALGORITHM = 'ES256'
    MAX_JWT_DURATION = 120          # 2 mins | 120 secs
    MAX_WS_CONN_DURATION = 300      # 5 mins | 300 secs
    class Channel:
        level2 = 'level2'
        user = 'user'
        tickers = 'tickers'
        ticker_batch = 'ticker_batch'
        status = 'status'
        market_trades = 'market_trades'
        candles = 'candles'
        heartbeats = 'heartbeats'

    class MessageTypes:
        subscribe = 'subscribe'
        unsubscribe = 'unsubscribe'

    def __init__(self, api_key: str, api_secret: str):
        self.KEY = api_key 
        self.SECRET = api_secret

        self.curr_jwt: str = ""
        self.last_jwt_update: datetime.datetime = datetime.datetime.now()
        self.opened_connections: list[dict[str, str | list]] = []

    def gen_jwt(self) -> str:
        return jwt_generator.build_ws_jwt(self.KEY, self.SECRET)

    def get_jwt(self) -> str:
        if not self.curr_jwt or (datetime.datetime.now() - self.last_jwt_update).seconds >= self.MAX_JWT_DURATION:
            self.curr_jwt = self.gen_jwt()
            self.last_jwt_update = datetime.datetime.now()

        return self.curr_jwt

    def on_open(self, ws):
        self.subscribe(ws=ws, channel=self.Channel.heartbeats)

    def on_message(self, ws, message):
        data = json.loads(message)
        data_path = os.path.join(os.getcwd(), 'data', 'websockets', 'level2', f'{datetime.datetime.now().strftime('%H_%M_%S')}.json')
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=4)

    def on_error(self, ws, e):
        print(f"Error: {e}")

    def on_close(self, ws):
        print("Connection closed")

    def create_socket(self):
        ws = websocket.WebSocketApp(
            self.WS_URL,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            )
        return ws

    def subscribe(self, ws: websocket.WebSocketApp, channel: str, products_ids: Optional[list[str]] = None, jwt: Optional[str] = None):
        msg: dict[str, str | list[str]] = {
            'type' : self.MessageTypes.subscribe,
            'channel': channel,
        }

        if products_ids:
            msg['product_ids'] = products_ids
        if jwt: 
            msg['jwt'] = jwt
        else:
            msg['jwt'] = self.gen_jwt()

        ws = self.create_socket()
        ws.send(json.dumps(msg))
        self.opened_connections.append(msg)
    
    def unsubscribe(self, ws: websocket.WebSocketApp, channel: str, products_ids: Optional[list[str]] = None, jwt: Optional[str] = None):
        msg: dict[str, str | list[str]] = {
            'type' : self.MessageTypes.unsubscribe,
            'channel': channel,
        }

        if products_ids:
            msg['product_ids'] = products_ids
        if jwt:
            msg['jwt'] = jwt

        ws.send(json.dumps(msg))

        removed_connection = { key: msg[key] for key in msg if key != 'type'}
        for oc in self.opened_connections:
            if oc == removed_connection:
                self.opened_connections.remove(oc)
                break

    def close_all(self):
        while self.opened_connections:
            oc = self.opened_connections.pop()
            self.unsubscribe(channel=oc['channel'], products_ids=oc.get('products_ids', None), jwt=oc.get('jwt', None))

def test_on_open(ws):
    msg = {
        'type': 'subscribe',
        'product_ids': ['BTC-USD'],
        'channel': 'ticker'
    }
    ws.send(json.dumps(msg))

count = 0
still_subbed = True 
def test_on_message(ws, msg):
    global count, still_subbed
    data = json.loads(msg)
    if data['channel']:
        data = json.loads(msg)
    else:
        data = 'No data'
        ws.close()
    print('Still alive...' + ' ' + str(count))
    print(data)
    count += 1

def test_on_error(ws, e):
    print(e)

def test_on_close(ws, status_code, msg):
    print(f"closing w/ status code:{status_code}\nmsg:{msg}")

def main():
    config = dotenv_values('.env')
    key = config['COINBASE_API_KEY']
    secret = config['COINBASE_API_SECRET']

    wservice = WebsocketService(key, secret)
    # Creates thread and websocket then sends the subscription request to the server
    #   - Messages are 
    wservice.subscribe(channel=WebsocketService.Channel.candles, products_ids=['BTC-USD'])


    # ws = websocket.WebSocketApp(WebsocketService.WS_URL, on_open=test_on_open, on_message=test_on_message, on_close=test_on_close, on_error=test_on_error)

if __name__=='__main__':
    main()