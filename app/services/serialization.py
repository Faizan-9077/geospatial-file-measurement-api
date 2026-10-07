import math
from datetime import date, datetime

import pandas as pd


def make_json_safe(value):

    if pd.isna(value):
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and math.isnan(value):
        return None

    return value