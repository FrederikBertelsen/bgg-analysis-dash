from datetime import datetime
from typing import Optional

import pandas as pd


def model_list_to_dataframe(models: list) -> pd.DataFrame:
    if not models:
        return pd.DataFrame()

    dicts = [m.to_dict() for m in models]

    return pd.DataFrame(dicts)


def estimate_eta(
    progress: float | None, last_update: datetime | None, created_at: datetime | None
) -> Optional[str]:
    if progress is None or last_update is None or created_at is None or progress <= 0:
        return None

    elapsed = (last_update - created_at).total_seconds()
    if elapsed < 0:
        elapsed = 0

    total_estimated = elapsed / progress
    eta_seconds = max(0, total_estimated - elapsed)
    secs = int(round(eta_seconds))
    if secs == 0:
        return "<1s"

    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")

    # Keep it concise: at most three components (e.g. "1d 2h 3m")
    if len(parts) > 3:
        parts = parts[:3]

    return " ".join(parts)
