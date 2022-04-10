"""
Data model to represent OHLCV data from an exchange
"""
from dataclasses import dataclass


@dataclass
class Ohlcv:
    """
    Data model to represent OHLCV data from an exchange
    """

    timestamp: int
    time: str
    symbol: str
    close: float
    volume: float
    price_change: float = 0
    volume_change: float = 0
