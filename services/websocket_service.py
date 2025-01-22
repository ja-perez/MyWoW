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
    JWT_EXPIRATION = 120
    MAX_CONNECTION_DURATION = 5 * 120
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

        self.opened_connections: list[dict[str, str | list]] = []

    def gen_jwt(self) -> str:
        return jwt_generator.build_ws_jwt(self.KEY, self.SECRET)

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

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.WS_URL,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            )
        self.ws.run_forever()

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

def main():
    config = dotenv_values('.env')
    key = config['COINBASE_API_KEY']
    secret = config['COINBASE_API_SECRET']

    with closing(websocket.create_connection(WebsocketService.WS_URL)) as conn:
        sub_msg = {
            'type': 'subscribe',
            'product_ids': ['BTC-USD'],
            'channel': 'ticker',
        }
        conn.send(json.dumps(sub_msg))
        print("SUBSCRIBED", "*" * 50)
        print(conn.recv(), '\n')
        print(conn.recv(), '\n')
        print(conn.recv(), '\n')
        print(conn.recv(), '\n')
        un_msg = {
            'type': 'unsubscribe',
            'channel': 'ticker',
            'product_ids': ['BTC-USD'],
        }
        conn.send(json.dumps(un_msg))
        print("UNSUBSCRIBED", "*" * 50)
        print(conn.recv(), '\n')
        print(conn.recv(), '\n')
        #print(conn.recv(), '\n')

if __name__=='__main__':
    main()