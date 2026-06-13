import json
import time
import urllib.parse

import requests
from cryptography.hazmat.primitives.asymmetric import ed25519


class Address:
    address = ""
    flag = ""

    def __init__(self, address: str, flag=""):
        self.address = address
        self.flag = flag

    def json(self):
        return self.__dict__


class ApiResponse:
    source_data = None

    def __init__(self, text_response: str = None, json_response: json = None):
        if text_response is not None and isinstance(text_response, str):
            self.source_data = json.loads(text_response)
        elif json_response is not None and isinstance(json_response, dict):
            self.source_data = json_response

    def is_success(self):
        if self.source_data is None:
            return False
        if 'success' in self.source_data:
            return self.source_data['success']
        return 'data' in self.source_data

    def code(self):
        return str(self.source_data.get('code', "")) if self.source_data is not None else ""

    def data(self):
        return self.source_data.get('data', "") if self.source_data is not None else ""

    def message(self):
        if self.source_data is None:
            return ""
        return self.source_data.get('msg', self.source_data.get('error', ""))

    def __str__(self):
        return str(self.source_data)


class ApiResponseV2(ApiResponse):
    def __init__(self, text_response: str = None, json_response: json = None):
        super().__init__(text_response=text_response, json_response=json_response)


def _to_futures_symbol(from_coin: str, to_coin: str) -> str:
    return f"{from_coin.upper()}{to_coin.upper()}"


def _to_spot_symbol(from_coin: str, to_coin: str) -> str:
    return f"{from_coin.upper()}/{to_coin.upper()}"


class CoinSwitchClient:
    def __init__(self, api_key="", secret_key="", ip="1.1.1.1"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.ip = ip

    @classmethod
    def get_base_url(cls):
        return "https://coinswitch.co"

    @classmethod
    def get_api_url(cls):
        return cls.get_base_url() + "/trade/api/v2/futures"

    def sign_request(self, method, path, params=None):
        if params:
            sep = "&" if "?" in path else "?"
            path = path + sep + urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
        decoded_path = urllib.parse.unquote_plus(path)
        epoch = str(int(time.time() * 1000))
        message = method + decoded_path + epoch
        secret = ed25519.Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(self.secret_key)
        )
        signature = secret.sign(message.encode("utf-8")).hex()
        headers = {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "X-AUTH-EPOCH": epoch,
        }
        return headers, decoded_path

    def _request(self, method, endpoint, params=None, data=None):
        path = "/trade/api/v2/futures" + endpoint
        headers, signed_path = self.sign_request(method, path, params=params)
        url = self.get_base_url() + signed_path
        r = requests.request(method, url, headers=headers, json=data)
        return ApiResponseV2(json_response=r.json())

    def _spot_request(self, method, endpoint, params=None, data=None):
        path = "/trade/api/v2" + endpoint
        headers, signed_path = self.sign_request(method, path, params=params)
        url = self.get_base_url() + signed_path
        r = requests.request(method, url, headers=headers, json=data)
        return ApiResponseV2(json_response=r.json())

    @classmethod
    def v2_fixed(cls, api_key="", secret_key="", ip="1.1.1.1"):
        return CoinSwitchV2FixedClient(api_key=api_key, secret_key=secret_key, ip=ip)

    @classmethod
    def v2_instant(cls, api_key="", secret_key="", ip="1.1.1.1"):
        return CoinSwitchV2InstantClient(api_key=api_key, secret_key=secret_key, ip=ip)

    @classmethod
    def v1(cls, api_key="", secret_key="", ip="1.1.1.1"):
        return CoinSwitchV1Client(api_key=api_key, secret_key=secret_key, ip=ip)


class CoinSwitchV1Client(CoinSwitchClient):
    def __init__(self, api_key="", secret_key="", ip="1.1.1.1"):
        super().__init__(api_key=api_key, secret_key=secret_key, ip=ip)

    def coins(self):
        return self._spot_request("GET", "/coins", params={"exchange": "c2c1"})

    def from_coin(self, coin: str):
        r = self.coins()
        if r.is_success():
            data = r.data()
            pairs = []
            for exchange, symbols in data.items():
                for sym in symbols:
                    if sym.lower().startswith(coin.lower()):
                        pairs.append(sym)
            return ApiResponseV2(json_response={"success": True, "data": pairs})
        return r

    def to_coin(self, coin: str):
        r = self.coins()
        if r.is_success():
            data = r.data()
            pairs = []
            for exchange, symbols in data.items():
                for sym in symbols:
                    if "/" in sym and sym.split("/")[1].lower() == coin.lower():
                        pairs.append(sym)
            return ApiResponseV2(json_response={"success": True, "data": pairs})
        return r

    def retrieve_limit_for(self, from_coin: str, to_coin: str):
        return self._request("GET", "/ticker", params={
            "symbol": _to_futures_symbol(from_coin, to_coin),
            "exchange": "EXCHANGE_2",
        })

    def place_offer_for(self, from_coin: str, to_coin: str, quantity: float, **kwargs):
        symbol = kwargs.get('symbol', _to_futures_symbol(from_coin, to_coin))
        side = kwargs.get('side', 'BUY')
        price = kwargs.get('price')
        data = {
            "symbol": symbol,
            "side": side,
            "order_type": "LIMIT" if price else "MARKET",
            "quantity": quantity,
            "exchange": kwargs.get('exchange', "EXCHANGE_2"),
        }
        if price:
            data["price"] = price
        r = self._request("POST", "/order", data=data)
        if r.is_success():
            order_data = r.data()
            order_data['offerReferenceId'] = order_data.get('orderId')
            return ApiResponseV2(json_response={"success": True, "data": order_data})
        return r

    def place_order_for(self, from_coin: str, to_coin: str, quantity: float,
                        offer_id: str, user_id: str,
                        to_adress=None, refund_address=None, **kwargs):
        symbol = kwargs.get('symbol', _to_futures_symbol(from_coin, to_coin))
        side = kwargs.get('side', 'BUY')
        data = {
            "symbol": symbol,
            "side": side,
            "order_type": "MARKET",
            "quantity": quantity,
            "exchange": kwargs.get('exchange', "EXCHANGE_2"),
        }
        r = self._request("POST", "/order", data=data)
        if r.is_success():
            order_data = r.data()
            order_data['orderId'] = order_data.get('orderId')
            return ApiResponseV2(json_response={"success": True, "data": order_data})
        return r

    def order_status(self, order_id: str):
        return self._request("GET", "/order", params={"order_id": order_id})


class CoinSwitchV2FixedClient(CoinSwitchClient):
    def __init__(self, api_key="", secret_key="", ip="1.1.1.1"):
        super().__init__(api_key=api_key, secret_key=secret_key, ip=ip)

    def coins(self):
        return self._spot_request("GET", "/coins", params={"exchange": "c2c1"})

    def pairs(self, from_coin: str = None, to_coin: str = None):
        r = self.coins()
        if not r.is_success():
            return r
        data = r.data()
        all_pairs = []
        for exchange, symbols in data.items():
            for sym in symbols:
                if "/" in sym:
                    base, quote = sym.split("/")
                    if from_coin and base.lower() != from_coin.lower():
                        continue
                    if to_coin and quote.lower() != to_coin.lower():
                        continue
                    all_pairs.append(sym)
        return ApiResponseV2(json_response={"success": True, "data": all_pairs})

    def from_coin(self, from_coin: str):
        return self.pairs(from_coin=from_coin)

    def to_coin(self, to_coin: str):
        return self.pairs(to_coin=to_coin)

    def place_offer(self, from_coin: str, to_coin: str,
                    quantity_from: float = None, quantity_to: float = None,
                    **kwargs):
        if quantity_from is not None and quantity_to is not None:
            raise ValueError('Specify one of quantity_from OR quantity_to')
        symbol = kwargs.get('symbol', _to_futures_symbol(from_coin, to_coin))
        side = kwargs.get('side', 'BUY')
        price = kwargs.get('price')
        data = {
            "symbol": symbol,
            "side": side,
            "exchange": kwargs.get('exchange', "EXCHANGE_2"),
        }
        if price:
            data["order_type"] = "LIMIT"
            data["price"] = price
            data["quantity"] = quantity_from if quantity_from is not None else quantity_to
        else:
            data["order_type"] = "MARKET"
            data["quantity"] = quantity_from if quantity_from is not None else quantity_to
        r = self._request("POST", "/order", data=data)
        if r.is_success():
            order_data = r.data()
            order_data['offerReferenceId'] = order_data.get('orderId')
            return ApiResponseV2(json_response={"success": True, "data": order_data})
        return r

    def order(self, from_coin: str, to_coin: str, offer_id: str,
              to_address=None, refund_adress=None,
              quantity_from: float = None, quantity_to: float = None,
              **kwargs):
        if quantity_from is not None and quantity_to is not None:
            raise ValueError('Specify one of quantity_from OR quantity_to')
        symbol = kwargs.get('symbol', _to_futures_symbol(from_coin, to_coin))
        side = kwargs.get('side', 'BUY')
        data = {
            "symbol": symbol,
            "side": side,
            "order_type": "MARKET",
            "quantity": quantity_from if quantity_from is not None else quantity_to,
            "exchange": kwargs.get('exchange', "EXCHANGE_2"),
        }
        r = self._request("POST", "/order", data=data)
        if r.is_success():
            order_data = r.data()
            order_data['orderId'] = order_data.get('orderId')
            return ApiResponseV2(json_response={"success": True, "data": order_data})
        return r

    def order_status(self, order_id: str):
        return self._request("GET", "/order", params={"order_id": order_id})

    def get_positions(self, symbol: str = None):
        params = {"exchange": "EXCHANGE_2"}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/positions", params=params)

    def update_leverage(self, symbol: str, leverage: int):
        data = {
            "symbol": symbol,
            "leverage": leverage,
            "exchange": "EXCHANGE_2",
        }
        return self._request("POST", "/leverage", data=data)

    def add_margin(self, symbol: str, amount: float):
        data = {
            "symbol": symbol,
            "amount": amount,
            "exchange": "EXCHANGE_2",
        }
        return self._request("POST", "/margin", data=data)


class CoinSwitchV2InstantClient(CoinSwitchClient):
    def __init__(self, api_key="", secret_key="", ip="1.1.1.1"):
        super().__init__(api_key=api_key, secret_key=secret_key, ip=ip)

    def coins(self):
        return self._spot_request("GET", "/coins", params={"exchange": "c2c1"})

    def pairs(self, from_coin: str = None, to_coin: str = None):
        r = self.coins()
        if not r.is_success():
            return r
        data = r.data()
        all_pairs = []
        for exchange, symbols in data.items():
            for sym in symbols:
                if "/" in sym:
                    base, quote = sym.split("/")
                    if from_coin and base.lower() != from_coin.lower():
                        continue
                    if to_coin and quote.lower() != to_coin.lower():
                        continue
                    all_pairs.append(sym)
        return ApiResponseV2(json_response={"success": True, "data": all_pairs})

    def from_coin(self, from_coin: str):
        return self.pairs(from_coin=from_coin)

    def to_coin(self, to_coin: str):
        return self.pairs(to_coin=to_coin)

    def rates(self, from_coin: str, to_coin: str):
        symbol = _to_futures_symbol(from_coin, to_coin)
        return self._request("GET", "/ticker", params={
            "symbol": symbol,
            "exchange": "EXCHANGE_2",
        })

    def order(self, from_coin: str, to_coin: str,
              to_address=None, refund_adress=None,
              quantity_from: float = None, quantity_to: float = None,
              **kwargs):
        if quantity_from is not None and quantity_to is not None:
            raise ValueError('Specify one of quantity_from OR quantity_to')
        symbol = kwargs.get('symbol', _to_futures_symbol(from_coin, to_coin))
        side = kwargs.get('side', 'BUY')
        data = {
            "symbol": symbol,
            "side": side,
            "order_type": "MARKET",
            "quantity": quantity_from if quantity_from is not None else quantity_to,
            "exchange": kwargs.get('exchange', "EXCHANGE_2"),
        }
        r = self._request("POST", "/order", data=data)
        if r.is_success():
            order_data = r.data()
            order_data['orderId'] = order_data.get('orderId')
            return ApiResponseV2(json_response={"success": True, "data": order_data})
        return r

    def orders(self):
        return self._request("GET", "/positions", params={"exchange": "EXCHANGE_2"})

    def order_status(self, order_id: str):
        return self._request("GET", "/order", params={"order_id": order_id})

    def wallet_balance(self):
        return self._spot_request("GET", "/user/portfolio")

    def get_transactions(self):
        return self._request("GET", "/transactions", params={"exchange": "EXCHANGE_2"})
