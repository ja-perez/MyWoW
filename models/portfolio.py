from coinbase.rest import RESTClient

class Portfolio:
    def __init__(self, client: RESTClient):
        self.client = client