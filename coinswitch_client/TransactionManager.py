from coinswitch_client.APIClient import CoinSwitchV2InstantClient


class StatusCode:
    STATUS_NEW = "new"
    STATUS_PARTIALLY_FILLED = "partially_filled"
    STATUS_FILLED = "filled"
    STATUS_CANCELED = "canceled"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"
    STATUS_PENDING = "pending"


class TransactionManager:
    orders = []
    api_key = ""
    secret_key = ""
    ip = ""

    def __init__(self, api_key="", secret_key="", ip="1.1.1.1"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.ip = ip
        self.api_client = CoinSwitchV2InstantClient(
            api_key=api_key, secret_key=secret_key, ip=ip
        )

    def convert(self, from_coin: str, to_coin: str, quantity: float,
                address_to=None, address_refund=None, side="buy", **kwargs):
        if quantity <= 0:
            raise ValueError(
                'Quantity must be greater than 0')

        symbol = kwargs.get('symbol', f"{from_coin.upper()}/{to_coin.upper()}")

        r = self.api_client.pairs(from_coin, to_coin)
        if not r.is_success() or not len(r.data()) > 0:
            raise ValueError(
                'No available trading pair for '
                f'{from_coin}/{to_coin} ({r.message()})')

        r = self.api_client.order(
            from_coin, to_coin,
            quantity_from=quantity, side=side, **kwargs,
        )
        if not r.is_success():
            raise ValueError(f'Order failed ({r.message()})')

        order_data = r.data()
        order_id = order_data.get('orderId')
        if order_id:
            self.orders.append(order_id)
        return order_data

    def orders_status(self):
        data = {}
        for order_id in self.orders:
            r = self.api_client.order_status(order_id)
            if not r.is_success():
                continue
            status = r.data().get('status', '')
            data[order_id] = status
        return data

    def pending_order(self):
        pending = {}
        for order_id, status in self.orders_status().items():
            if status in (
                StatusCode.STATUS_NEW,
                StatusCode.STATUS_PARTIALLY_FILLED,
                StatusCode.STATUS_PENDING,
            ):
                pending[order_id] = status
        return pending

    def finished_orders(self):
        finished = {}
        for order_id, status in self.orders_status().items():
            if status in (
                StatusCode.STATUS_FILLED,
                StatusCode.STATUS_CANCELED,
                StatusCode.STATUS_REJECTED,
                StatusCode.STATUS_EXPIRED,
            ):
                finished[order_id] = status
        return finished
