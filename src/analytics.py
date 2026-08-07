import pandas as pd


class Analytics:

    def total_students(self, df):
        return len(df)

    def missing_values(self, df):
        return df.isnull().sum()

    def summary(self, df):
        return df.describe(include="all")
