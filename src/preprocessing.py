import pandas as pd
from pathlib import Path


class DataPreprocessor:

    def __init__(self):
        self.raw_path = Path("data/raw")

    def clean_dataframe(self, df):
        # Buang baris kosong
        df = df.dropna(how="all")

        # Buang lajur kosong / Unnamed
        df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]

        # Reset index
        df = df.reset_index(drop=True)

        return df

    def load_gps(self):
        file = self.raw_path / "GPS_Bidang_SMKKJ_2026.xlsx"

        df = pd.read_excel(file)

        return self.clean_dataframe(df)

    def load_ppt(self):
        file = self.raw_path / "ANALISIS_PPT_2026_T5_OPTIMISED.xlsx"

        df = pd.read_excel(file)

        return self.clean_dataframe(df)
