import requests 

def get_crypto_prices() :
    
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dogecoin&vs_currencies=usd"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    bitcoin_price = data["bitcoin"]["usd"]
    ethereum_price = data["ethereum"]["usd"]
    solana_price = data["solana"]["usd"]
    dogecoin_price = data["dogecoin"]["usd"]

    return bitcoin_price , ethereum_price , solana_price ,dogecoin_price

# if __name__ == "__main__":

#     btc, eth, sol, dog = get_crypto_prices()

#     print("Bitcoin Price:", btc)
#     print("Ethereum Price:", eth)
#     print("Solana Price:", sol)
#     print("Dogecoin Price:", dog)

import yfinance as yf


def get_stock_prices():

    apple = yf.Ticker("AAPL")
    tesla = yf.Ticker("TSLA")

    apple_price = apple.history(period="1d")["Close"].iloc[-1]
    tesla_price = tesla.history(period="1d")["Close"].iloc[-1]

    return apple_price, tesla_price