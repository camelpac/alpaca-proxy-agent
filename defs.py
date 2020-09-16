from enum import Enum

import os

from alpaca_trade_api.entity import quote_mapping, agg_mapping, trade_mapping
from alpaca_trade_api.polygon.entity import quote_mapping as \
    polygon_quote_mapping, agg_mapping as polygon_aggs_mapping, \
    trade_mapping as polygon_trade_mapping


USE_POLYGON = True if os.environ.get("USE_POLYGON") == 'true' else False



QUOTE_PREFIX = "Q." if USE_POLYGON else "alpacadatav1/Q."
TRADE_PREFIX = "T." if USE_POLYGON else "alpacadatav1/T."
# MINUTE_AGG_PREFIX = "AM." if USE_POLYGON else "alpacadatav1/AM."
MINUTE_AGG_PREFIX = "AM."
SECOND_AGG_PREFIX = "A."



reverse_qoute_mapping = {v: k for k, v in quote_mapping.items()}
reverse_polygon_qoute_mapping = {
    v: k for k, v in polygon_quote_mapping.items()
}

reverse_trade_mapping = {v: k for k, v in trade_mapping.items()}
reverse_polygon_trade_mapping = {
    v: k for k, v in polygon_trade_mapping.items()
}

reverse_minute_agg_mapping = {v: k for k, v in agg_mapping.items()}
reverse_polygon_aggs_mapping = {
    v: k for k, v in polygon_aggs_mapping.items()
}


class MessageType(Enum):
    Quote = 1
    MinuteAgg = 2
    SecondAgg = 3  # only with polygon
    Trade = 4

