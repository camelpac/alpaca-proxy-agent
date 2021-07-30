from enum import Enum

from alpaca_trade_api.entity import quote_mapping, agg_mapping, trade_mapping

QUOTE_PREFIX = "alpacadatav1/Q."
TRADE_PREFIX = "alpacadatav1/T."
MINUTE_AGG_PREFIX = "AM."
SECOND_AGG_PREFIX = "A."

reverse_qoute_mapping = {v: k for k, v in quote_mapping.items()}

reverse_trade_mapping = {v: k for k, v in trade_mapping.items()}

reverse_minute_agg_mapping = {v: k for k, v in agg_mapping.items()}


class MessageType(Enum):
    Quote = 1
    MinuteAgg = 2
    SecondAgg = 3  # only with polygon
    Trade = 4
