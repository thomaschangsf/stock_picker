from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class MarketData:
    """
    Canonical OHLCV time series with a DatetimeIndex.
    """

    df: pd.DataFrame

    def __post_init__(self) -> None:
        if not isinstance(self.df.index, pd.DatetimeIndex):
            raise TypeError("MarketData.df must have a DatetimeIndex")
        if "close" not in self.df.columns:
            raise ValueError("MarketData.df must include a 'close' column")


class Strategy(Protocol):
    name: str

    def positions(self, data: MarketData) -> pd.Series:
        """
        Return a 0/1 (flat/long) position series indexed like data.df.
        """

