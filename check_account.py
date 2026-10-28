import urllib.request
import json

url = "https://paper-api.alpaca.markets/v2/account"
headers = {
    "APCA-API-KEY-ID": "PKVEJ4HX3LOBLG3W3UPLKUT7A3",
    "APCA-API-SECRET-KEY": "D1dSLTkrjVmJggZVgsV9jgg7wLi1yfVbCZSBg7JkWYua"
}

try:
    req = urllib.request.Request(url, headers=headers)
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())
    print(f"Status: {data['status']}")
    print(f"Cash: ${float(data['cash']):,.2f}")
    print(f"Buying Power: ${float(data['buying_power']):,.2f}")
    print(f"Portfolio Value: ${float(data['portfolio_value']):,.2f}")
except Exception as e:
    print(f"Error fetching account details: {e}")