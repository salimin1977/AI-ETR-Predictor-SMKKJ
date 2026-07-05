import pandas as pd
from pathlib import Path

class DataPreprocessor:

    def __init__(self):
        self.raw_path = Path("data/raw")
        self.processed_path = Path("data/processed")

    def load_excel(self, filename):
        file_path = self.raw_path / filename
        return pd.read_excel(file_path)

    def save_processed(self, dataframe, filename):
        output = self.processed_path / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_excel(output, index=False)

    def clean_dataframe(self, df):
        # Buang baris kosong
        df = df.dropna(how="all")

        # Buang lajur Unnamed
        df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]

        # Reset index
        df = df.reset_index(drop=True)

        # Buang data pendua
        df = df.drop_duplicates()

        # Gantikan nilai kosong
        df = df.fillna("")

        return df

    def load_gps(self):
        df = self.load_excel("GPS_Bidang_SMKKJ_2026.xlsx")
        return self.clean_dataframe(df)

    def load_ppt(self):
        df = self.load_excel("ANALISIS_PPT_2026_T5_OPTIMISED.xlsx")
        return self.clean_dataframe(df)