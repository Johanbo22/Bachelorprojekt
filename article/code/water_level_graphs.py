import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
import re
import matplotlib.dates as mdates
import datetime
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)

sheet_id: str = "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
water_level_sheets: list[str] = ['vandstand_aabenraa', 'vandstand_gedser', 'vandstand_hesnaes', 'vandstand_praestoe_roedvig']

log: bool = True

def parse_iso_date(date_str: str) -> Optional[str]:
    match: Optional[re.match] = re.match(r'(\d{4})-(\d{2})-(\d{2})T', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month-{day}}"
    return None

def date_format(date_str: Optional[str]) -> Optional[str]:
    if date_str:
        try:
            date_obj: datetime.datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return f"{date_obj.day:02d}/{date_obj.month:02d}\n{date_obj.year}"
        except ValueError:
            return date_str
    return None

def load_water_level_data(sheet_name: str) -> pd.DataFrame:
    url: str = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    data: pd.DataFrame = pd.read_csv(url, decimal=",")
    df: pd.DataFrame = pd.DataFrame(data)
    df["observed"] = pd.to_datetime(df["observed"], utc=True)
    df = df.sort_values(by="observed")

    if log:
        logging.info(f"Data information for {sheet_name}")
        logging.info(data.info())
        logging.info(data.describe())
    
    return df

def create_combined_plot() -> plt.Figure:
    sns.set_theme(style="ticks")
    sns.set_context("paper", font_scale=1)

    plt.rcParams["font.family"] = "DeJavu Serif"
    plt.rcParams["font.serif"] = "Times New Roman"

    label_map: dict[str, str] = {
        "aabenraa": "(A)",
        "gedser": "(B)",
        "hesnaes": "(C)",
        "praestoe": "(D)"
    }
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True, sharey=True)
    axes = axes.flatten()

    global_min_date = None
    global_max_date = None

    all_data = {}
    for sheet_name in water_level_sheets:
        df = load_water_level_data(sheet_name)
        all_data[sheet_name] = df
        
        if global_min_date is None or df["observed"].min() < global_min_date:
            global_min_date = df["observed"].min()
        if global_max_date is None or df["observed"].max() > global_max_date:
            global_max_date = df["observed"].max()
    
    time_range = global_max_date - global_min_date
    padding = time_range * 0.01
    global_min_date = global_min_date - padding
    global_max_date = global_max_date + padding

    for idx, sheet_name in enumerate(water_level_sheets):
        ax = axes[idx]
        df = all_data[sheet_name]

        location_key: str = sheet_name.split("_")[1].lower()
        subplot_label: str = label_map.get(location_key, "")

        ax.plot(
            df["observed"],
            df["value"],
            marker="o",
            linestyle="-",
            linewidth=1.1,
            color="#044da1",
            alpha=1,
            markersize=1,
            markeredgecolor="white",
            markeredgewidth=0.0
        )

        ax.text(
            0.01, 0.98, subplot_label,
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            va="top",
            ha="left"
        )

        if sheet_name == "vandstand_hesnaes":
            unofficial_date = pd.Timestamp("2023-10-20T20:30:10Z")
            unofficial_value = 239
            
            ax.plot(
                unofficial_date,
                unofficial_value,
                marker="x",
                color="red",
                markersize=6
            )
        
        ax.set_xlim(global_min_date, global_max_date)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%Y"))
        ax.set_ylim(-60, 250)

        ax.tick_params(axis="both", labelsize=12)

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
            spine.set_edgecolor("black")
    
    for idx in [2, 3]:
        axes[idx].set_xlabel("Date", fontsize=14)
    
    for idx in [0, 2]:
        axes[idx].set_ylabel("Water level (cm)", fontsize=14)
    
    fig.tight_layout()

    return fig

if __name__ == "__main__":
    output_folder = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\images"
    print("ding dong")

    try:
        fig = create_combined_plot()
        gemmes: bool = True

        if gemmes:
            format: str = "svg"
            chartsave: str = os.path.join(output_folder, f"vandstandsGrafVersion4.{format}")
            fig.savefig(chartsave, dpi=1200, format=format, bbox_inches="tight")
            print(f"Gemt som {format} i {chartsave}")
    
    except Exception as e:
        logging.error(f"Fejl {str(e)}")
    
    print("Data behandlet og plottet")
