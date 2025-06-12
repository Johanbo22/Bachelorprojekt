import pandas as pd

'''
Dette tool kan hurtigt omdanne tidsstempler fra .tid til ISO tid
'''

file_path = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bachelorprojekt\Data_Raw\timestamp.xlsx"

df = pd.read_excel(file_path)

df["timestamp"] = df["timestamp"].str.split(".").str[0].str.replace(" ", "T") + "Z"

df.to_csv("konvertede_tidsstempel.csv", index=False)
