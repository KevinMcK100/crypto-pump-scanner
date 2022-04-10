"""
Builds and prints a dataframe presenting the top price movers across all KuCoin Futures coins
"""
import datetime as dt
import time
from threading import Semaphore, Thread
from time import sleep
from typing import Dict, List

import ccxt
import numpy as np
import pandas as pd
from ccxt import Exchange
from IPython.display import HTML, clear_output, display

from ohlcv import Ohlcv


class KucoinPumpScanner:
    """
    Fetches price data from KuCoin and displays top price movers in a dataframe
    """

    timeframes = [1, 3, 5, 15, 30, 60]
    pd.options.mode.chained_assignment = None
    raw_dataframe = pd.DataFrame()
    top_mover_symbols = []
    lock = Semaphore()

    def __init__(self, timeframe: int):
        if timeframe not in self.timeframes:
            raise ValueError(f"Invalid timeframe '{timeframe}'. Timeframe must be one of: {self.timeframes}")
        self.timeframe = timeframe
        self.kucoin = ccxt.kucoinfutures()
        self.kucoin.load_markets()
        self.symbols = self.kucoin.symbols
        load_all_coins_task = Thread(target=self.__start_all_coins_refresh_task)
        print("Loading price data for all futures pairs on KuCoin. This may take a couple of minutes to complete...")
        try:
            load_all_coins_task.start()
            load_top_mover_coins_task = Thread(target=self.__start_top_coins_refresh_task)
            load_top_mover_coins_task.start()
            load_top_mover_coins_task.join()
        except (KeyboardInterrupt, SystemError):
            pass

    def __start_all_coins_refresh_task(self):
        while True:
            start_at = time.time()
            since_minutes = 61 if self.raw_dataframe.empty else 1
            processed_df = self.__load_latest_data(self.symbols, since_minutes)
            processed_df = processed_df.loc[processed_df["Period"] == self.timeframe]
            self.top_mover_symbols = list(x for x in processed_df.head(5)["Symbol"])
            sleep(max(60 - (time.time() - start_at), 0))

    def __start_top_coins_refresh_task(self):
        while True:
            start_at = time.time()
            if not self.raw_dataframe.empty:
                processed_df = self.__load_latest_data(self.top_mover_symbols, 1)
                print_top_movers(processed_df, self.timeframe)
            delay = max(10 - (time.time() - start_at), 0) if not self.raw_dataframe.empty else 0.01
            sleep(delay)

    def __load_latest_data(self, symbols: List[str], since_minutes: int) -> pd.DataFrame:
        # Fetch historical data
        since = round(time.time() * 1000 - dt.timedelta(minutes=since_minutes).total_seconds() * 1000)
        ohlcv_df = fetch_ohlcv(self.kucoin, symbols, "1m", since)
        self.lock.acquire()
        self.raw_dataframe = pd.concat([self.raw_dataframe, ohlcv_df])
        self.raw_dataframe = self.raw_dataframe.sort_index(ascending=False)
        self.lock.release()
        processed_data = self.__calculate_price_changes(self.raw_dataframe)
        processed_df = pd.DataFrame(
            data=processed_data,
            columns=["Period", "Timestamp", "Symbol", "Price", "Volume", "Price Change", "Volume Change"],
        )
        sorted_df = processed_df.sort_values(by="Price Change", ascending=False)
        return sorted_df

    def __calculate_price_changes(self, data: pd.DataFrame) -> List:
        calc = []
        # Lookback timeframes (in minutes) over which to calculate price changes
        for symbol in self.symbols:
            ohlcv: Dict[int, Ohlcv] = {}
            # Calculate the timestamp for each timeframe lookback
            time_tuple = [(m, round((time.time() - m * 60) * 1000)) for m in self.timeframes]
            sym_df = data.loc[data["sym"] == symbol]
            for timestamp in time_tuple:
                # Dataframe index is the timestamp of the price info
                for idx in sym_df.index:
                    # When we meet a record with a timestamp older than the lookback timestamp, then select this row
                    if idx <= timestamp[1]:
                        row = sym_df.loc[[idx]]
                        ohlcv[timestamp[0]] = Ohlcv(
                            idx,
                            str(dt.datetime.fromtimestamp(idx / 1000)),
                            row.sym.values[0],
                            row.c.values[0],
                            row.v.values[0],
                        )
                        # Select the latest price info and calculate delta against historical price info
                        latest_row = sym_df.head(1)
                        percent_change = round(((latest_row.c.values[0] / row.c.values[0]) - 1) * 100, 2)
                        volume_change = round(((latest_row.v.values[0] / row.v.values[0]) - 1) * 100, 2)
                        calc.append(
                            [
                                timestamp[0],
                                idx,
                                row.sym.values[0],
                                row.c.values[0],
                                row.v.values[0],
                                percent_change,
                                volume_change,
                            ]
                        )
                        break
        return calc


def fetch_ohlcv(exchange: Exchange, symbols: List[str], timeframe: str, since: int) -> pd.DataFrame:
    """Fetch latest OHLCV data from KuCoin for given list of symbols"""
    df1 = pd.DataFrame()
    for symbol in symbols:
        candles = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=since)
        for candle in candles:
            data = {"sym": symbol, "c": candle[4], "v": candle[5]}
            df2 = pd.DataFrame(data=data, index=[candle[0]])
            df1 = pd.concat([df1, df2])
    return df1


def print_top_movers(processed_df: pd.DataFrame, timeframe: int = 15):
    """Transform and print the dataframe"""
    processed_df = processed_df.loc[processed_df["Period"] == timeframe]
    processed_df = processed_df.loc[processed_df["Period"] == timeframe]
    processed_df["Symbol"] = processed_df["Symbol"].apply(
        lambda x: x if ":" not in x else str(x).split(":", maxsplit=1)[0]
    )
    processed_df["Price Change"] = processed_df["Price Change"].apply(lambda x: str(x) + "%")
    processed_df["Volume Change"] = processed_df["Volume Change"].apply(lambda x: str(x) + "%")
    processed_df["Rank"] = np.arange(1, len(processed_df) + 1)
    processed_df = processed_df[["Rank", "Symbol", "Price", "Volume", "Price Change", "Volume Change"]]
    display(HTML(processed_df.head(10).to_html(index=False)))
    clear_output(wait=True)
