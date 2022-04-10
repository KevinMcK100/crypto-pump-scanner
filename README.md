# Crypto Pump Scanner

Pulls price data for every available crypto on a given exchange and ranks assets by highest price change percentage.

This is useful for detecting which asset are "overbought" and a retrace may be imminent (identifying shorting opportunities).

The top 10 pumping coins are displayed in a dataframe in a Jupyter notebook. Price changes are refreshed every 10 seconds.

## Installation

Run `source start-scanner.sh` from within the project's directory

## Exchanges Available

- KuCoin Futures

## Limitations

### KuCoin Futures

#### KuCoin API Limitations

Initially I wanted to subscribe to a websocket for each coin on KuCoin Futures to get realtime price data. However the [maximum number of websocket connections allowed by KuCoin is 50](https://docs.kucoin.com/#request-rate-limit) and KuCoin has over 100 coins on Futures.

Next I tried pulling price data for each of the 100+ coins. Unfortunately KuCoin's API doesn't allow pulling price data for a specific list of coins. Instead you must pull each coin's price data in separate requests. This number of requests degraded performance due to network latency. 

Given that a refresh of all coins takes 30-40 seconds it was never going to be possible to refresh price data at regular intervals like 10 seconds using this method

#### Work Around

The workaround is to refresh the top 5 moving coins on a more regular interval and refresh the entire 100+ coins on a less regular interval. The idea is that we generally only care about getting regular updates on the coins which are already pumping.

The code handles this as follows:

- Initial load of all price data across all coins (takes 30-40 seconds to complete)
- Data is displayed in a table upon fetching and ranking all price data
- A separate thread pulls the top 5 top moves and refreshes price data for these coins every 10 seconds
- After a minute, the first thread will refresh all price data again
