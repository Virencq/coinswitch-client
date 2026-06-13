from coinswitch_client.APIClient import CoinSwitchClient


def v2_instant(api_key="", secret_key="", ip="1.1.1.1"):
    return CoinSwitchClient.v2_instant(api_key=api_key, secret_key=secret_key, ip=ip)


def v2_fixed(api_key="", secret_key="", ip="1.1.1.1"):
    return CoinSwitchClient.v2_fixed(api_key=api_key, secret_key=secret_key, ip=ip)
