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
        dataframe.to_excel(output, index=False)

    def clean_data(self, dataframe):
        dataframe = dataframe.copy()
        dataframe = dataframe.drop_duplicates()
        dataframe = dataframe.fillna("")
        return dataframe
