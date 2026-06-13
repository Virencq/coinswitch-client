# Python CoinSwitch Client

Python client for [CoinSwitch PRO Futures API](https://api-trading.coinswitch.co/). Uses Ed25519 signature-based auth.

## Install

```bash
pip install coinswitch-client
# or with dotenv support:
pip install "coinswitch-client[dotenv]"
```

## Setup

Copy `.env.example` to `.env` and add your API credentials from [CoinSwitch PRO](https://coinswitch.co):

```
COINSWITCH_API_KEY=your_api_key
COINSWITCH_SECRET_KEY=your_ed25519_secret_key
```

## Usage

```python
from coinswitch_client.APIClient import CoinSwitchV2InstantClient

c = CoinSwitchV2InstantClient()

# Market data
print(c.coins())               # available trading pairs
print(c.rates('btc', 'usdt'))  # ticker with last/mark/index price
print(c.order_status('order_id'))

# Trading
c.order('btc', 'usdt', quantity_from=0.001, side='BUY')

# Account
print(c.wallet_balance())      # portfolio (includes futures balances)
print(c.get_positions())
print(c.get_transactions())
```

### CoinSwitchV2FixedClient (limit orders + positions)

```python
from coinswitch_client.APIClient import CoinSwitchV2FixedClient

c = CoinSwitchV2FixedClient()
print(c.coins())
print(c.pairs('btc', 'usdt'))
print(c.get_positions())
r = c.place_offer('btc', 'usdt', quantity_from=0.001, side='BUY', price=60000)
```

### TransactionManager

```python
from coinswitch_client.TransactionManager import TransactionManager

m = TransactionManager()
order = m.convert('btc', 'usdt', 0.001, side='BUY')
print(m.orders_status())
print(m.pending_order())
print(m.finished_orders())
```

## API Reference

Targets the Futures surface at `https://coinswitch.co/trade/api/v2/futures`.

| Method | Endpoint |
|--------|----------|
| `rates()` | `GET /ticker?symbol=BTCUSDT&exchange=EXCHANGE_2` |
| `order()` | `POST /order` (body: symbol, side, order_type, quantity, exchange) |
| `order_status()` | `GET /order?order_id=...` |
| `get_positions()` | `GET /positions?exchange=EXCHANGE_2` |
| `wallet_balance()` | `GET /trade/api/v2/user/portfolio` (Spot) |
| `get_transactions()` | `GET /transactions?exchange=EXCHANGE_2` |

Symbol format: `BTCUSDT` (no slash). Side: `BUY` / `SELL`. Order type: `MARKET` / `LIMIT`.
