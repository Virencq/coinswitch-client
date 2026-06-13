# Python CoinSwitch Client

Python client for [CoinSwitch PRO Futures API](https://api-trading.coinswitch.co/). Uses Ed25519 signature-based authentication.

## Install

```bash
pip install requests cryptography
# optionally for .env support:
pip install python-dotenv
```

## Setup

Copy `.env.example` to `.env` and add your API credentials:

```
COINSWITCH_API_KEY=your_api_key
COINSWITCH_SECRET_KEY=your_ed25519_secret_key
```

Generate keys at [CoinSwitch PRO](https://coinswitch.co) → API section.

## Usage

```python
from coinswitch_client.APIClient import CoinSwitchV2InstantClient
from dotenv import load_dotenv
import os

load_dotenv()

c = CoinSwitchV2InstantClient(
    api_key=os.getenv('COINSWITCH_API_KEY'),
    secret_key=os.getenv('COINSWITCH_SECRET_KEY'),
)

# Market data
print(c.coins())                          # available trading pairs
print(c.rates('btc', 'usdt'))             # ticker (last/mark/index price)
print(c.order_status('order_id'))

# Trading
c.order('btc', 'usdt', quantity_from=0.001, side='BUY')

# Account
print(c.wallet_balance())                 # portfolio balances (INR, crypto)
print(c.get_positions())                  # open futures positions
print(c.get_transactions())               # transaction history
```

### Limit orders, leverage & margin

```python
from coinswitch_client.APIClient import CoinSwitchV2FixedClient

c = CoinSwitchV2FixedClient()

# Limit order
c.place_offer('btc', 'usdt', quantity_from=0.001, side='BUY', price=60000)

# Leverage
c.update_leverage('BTCUSDT', 5)

# Add margin
c.add_margin('BTCUSDT', 100)
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
| `order()` | `POST /order` |
| `order_status()` | `GET /order?order_id=...` |
| `get_positions()` | `GET /positions?exchange=EXCHANGE_2` |
| `wallet_balance()` | `GET /trade/api/v2/user/portfolio` |
| `get_transactions()` | `GET /transactions?exchange=EXCHANGE_2` |
| `update_leverage()` | `POST /leverage` |
| `add_margin()` | `POST /margin` |

- Symbol format: `BTCUSDT` (no slash)
- Side: `BUY` / `SELL`
- Order type: `MARKET` / `LIMIT`
- Exchange: `EXCHANGE_2`
