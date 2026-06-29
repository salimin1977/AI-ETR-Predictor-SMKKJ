from pathlib import Path
import pandas as pd

RAW_FOLDER = Path("data/raw")


class DataPreprocessor:

    def load_gps(self):
        file = RAW_FOLDER / "GPS_Bidang_SMKKJ_2026.xlsx"
        return pd.read_excel(file)

    def load_ppt(self):
        file = RAW_FOLDER / "ANALISIS_PPT_2026_T5_OPTIMISED.xlsx"
        return pd.read_excel(file)
