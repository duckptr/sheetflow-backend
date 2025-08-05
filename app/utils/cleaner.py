import pandas as pd
import math

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    NaN, NaT 값을 None으로 변환해 JSON 직렬화 가능하도록 처리
    """
    df = df.astype(object).where(pd.notnull(df), None)
    for col in df.columns:
        df[col] = df[col].apply(lambda x: None if (isinstance(x, float) and math.isnan(x)) else x)
    return df
