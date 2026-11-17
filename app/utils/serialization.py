import math
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


def sanitize(value: Any) -> Any:
    """Ubah nilai hasil DuckDB menjadi nilai yang aman untuk JSON valid.

    - NaN / +-Infinity -> None (null)
    - Decimal -> float
    - date / datetime / time -> string ISO 8601
    """
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        f = float(value)
        return f if math.isfinite(f) else None
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(v) for v in value]
    return value
