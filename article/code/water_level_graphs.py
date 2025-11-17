import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
import re
import matplotlib.dates as mdates
import datetime
from typing import Optional, Tuple

'''
Dette script kan håndtere vandstandsdata fra DMI og tegne data på en graf. 
Scriptet bruger en ISO dato parser funktion til at lave datostempler nemmere at læse.
'''

# logging
logging.basicConfig(level=logging.INFO)

sheet_id: str = "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
water_level_sheets: list[str] = ["vandstand_aabenraa", "vandstand_gedser", "vandstand_hesnaes", "vandstand_praestoe_roedvig"]

log: bool = False


def parse_iso_date(date_str: str) -> Optional[str]:
    '''
    En funktion der omdanner en ISO dato til en læsbar dato. Dette er nødvendigt senere da der sker en ValueError ved dato
    '''
    match: Optional[re.match] = re.match(r'(\d{4})-(\d{2})-(\d{2})T', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    return None

def date_format(date_str: Optional[str]) -> Optional[str]:
    if date_str:
        try:
            date_obj: datetime.datetime = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return f"{date_obj.day:02d}/{date_obj.month:02d}\n{date_obj.year}"
        except ValueError:
            return date_str
    return None

def process_water_level_data(sheet_name: str, to_date: Optional[str]=None) -> Tuple[plt.Figure, str]:
    url: str = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    data: pd.DataFrame = pd.read_csv(url, decimal=",")
    df: pd.DataFrame = pd.DataFrame(data)

    df["observed"] = pd.to_datetime(df["observed"], utc=True)

    dates: list[Optional[str]] = []
    x_labels: list[Optional[str]] = []
    formatted_dates: list[Optional[str]] = []
    
    # tager datomærkerne i arket og konverterer dem til en mere læsbar dato ved brug af parse_iso_date funktionen. Bruges ikke
    '''for date_str in df["observed"]:
        parsed_date = parse_iso_date(date_str)
        if parsed_date:
            dates.append(parsed_date)
            x_labels.append(parsed_date)

            formatted_date = date_format(parsed_date)
            formatted_dates.append(formatted_date)
        else:
            dates.append(None)
            x_labels.append(None)
            formatted_dates.append(None)'''

    # sorterer værdier efter dato
    #df["date_string"] = dates
    #df["formatted_date"] = formatted_dates
    df = df.sort_values(by="observed")
    if to_date:
        end_idx: int = df.index[df["date_string"] <= to_date].max()
        if pd.isna(end_idx):
            end_idx = len(df) - 1
    else:
        end_idx = len(df) - 1

    if log:
        logging.info(f"Data information for {sheet_name}")
        logging.info(data.info())
        logging.info(data.describe())
    
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

    location_key: str = sheet_name.split("_")[1].lower()
    subplot_label: str = label_map.get(location_key, "")

    fig, ax = plt.subplots(figsize=(7, 5))
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

    # sSæt unverified vandstand i Hesnæs Kl 18:30UTC+0 med 239 cm. 
    if sheet_name == "vandstand_hesnaes":
        unoffical_date = pd.Timestamp("2023-10-20T20:30:10Z")
        unoffical_value = 239
        
        ax.plot(
            unoffical_date,
            unoffical_value,
            marker="x",
            color="red",
            markersize=6
        )

    # placeringen af datostemplerne i plottet for at undgå overlap med xaksen
    '''num_ticks = min(10, len(df))
    tick_positions = [i * (len(df) - 1) // (num_ticks - 1) for i in range(num_ticks)]
    tick_labels = [df["formatted_date"].iloc[pos] for pos in tick_positions]'''

    #ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%Y"))
    #ax.set_xticks(tick_positions)
    #ax.set_xlim(None, end_idx)
    

    location_name: str = sheet_name.split("_")[1].capitalize()
    #ax.set_title(f"Vandstand {location_name}", fontsize=14, loc="left")
    ax.set_xlabel("Date", fontsize=14)
    ax.set_ylabel("Water level (cm)", fontsize=14)
    ax.tick_params(axis="y", labelsize=12)
    ax.tick_params(axis="x", labelsize=12)
    ax.set_ylim(-60, 250)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_edgecolor("black")

    fig.tight_layout()

    return fig, sheet_name

if __name__ == "__main__":
    output_folder = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\images\eps"

    for sheet_name in water_level_sheets:
        print(f"Behandler ark: {sheet_name}")

        try: 
            fig, current_sheet = process_water_level_data(sheet_name)

            gemmes: bool = True
            if gemmes:
                format: str = "png"
                chartsave: str = os.path.join(output_folder, f"{current_sheet}_vandstandsplot.{format}")
                fig.savefig(chartsave, dpi=1200, format=format)
                print(f"Gemt som {format} i {chartsave}")

        except Exception as e:
            logging.error(f"Fejl ved behandling af ark {sheet_name}: {str(e)}")

    print("Alle ark er blevet behandlet")
