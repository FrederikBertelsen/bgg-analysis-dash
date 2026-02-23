import pandas as pd


def model_list_to_dataframe(models: list) -> pd.DataFrame:
    if not models:
        return pd.DataFrame()

    dicts = [m.to_dict() for m in models]

    return pd.DataFrame(dicts)
