import pandas as pd

pd.read_json("db.json").to_excel("output.xlsx")