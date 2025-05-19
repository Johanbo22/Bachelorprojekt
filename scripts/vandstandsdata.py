import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
import os

file_path = r""
if os.path.exists(file_path):
    print("yes")
else:
    print("no")

sheets_dict = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')

dfs = []
for sheet_name, sheet_df in sheets_dict.items():
    sheet_df['Sheet'] = sheet_name
    dfs.append(sheet_df)

df = pd.concat(dfs, ignore_index=True)

df["observed"] = pd.to_datetime(df["observed"], errors="coerce")

df = df.dropna(subset=['observed', 'value'])
df['value'] = pd.to_numeric(df['value'], errors="coerce")

df.head()

scat = False
if scat:
    for sheet_name, sheet_df in df.groupby("Sheet"):
        plt.figure(figsize=(12, 6))
        sns.scatterplot(x="observed", y="value", data=sheet_df, alpha=0.7)
        plt.xlabel("Tidspunkt")
        plt.ylabel("Vandstand (cm)")
        plt.title(f"Vandstanden for {sheet_name} i oktober 2023")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.show()
else:
    for sheet_name, sheet_df in df.groupby("Sheet"):
        plt.figure(figsize=(12, 6))
        sns.lineplot(x="observed", y="value", data=sheet_df, marker="", linewidth=2)
        plt.xlabel("Tidspunkt")
        plt.ylabel("Vandstand (cm)")
        plt.title(f"Vandstanden for {sheet_name} i oktober 2023")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.show()
