import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
import re
import matplotlib.dates as mdates
import datetime

'''
Dette script kan håndtere vandstandsdata fra DMI og tegne data på en graf. 
Scriptet bruger en ISO dato parser funktion til at lave datostempler nemmere at læse.
'''

# logging
logging.basicConfig(level=logging.INFO)

sheet_id = "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
water_level_sheets = ["vandstand_aabenraa", "vandstand_gedser", "vandstand_hesnaes", "vandstand_praestoe_roedvig"]

log = False


def parse_iso_date(date_str):
    '''
    En funktion der omdanner en ISO dato til en læsbar dato. Dette er nødvendigt senere da der sker en ValueError ved dato
    '''
    match = re.match(r'(\d{4})-(\d{2})-(\d{2})T', date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    return None

def date_format(date_str):
    if date_str:
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return f"{date_obj.day:02d}/{date_obj.month:02d}\n{date_obj.year}"
        except ValueError:
            return date_str
    return None

def process_water_level_data(sheet_name, to_date=None):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    data = pd.read_csv(url, decimal=",")
    df = pd.DataFrame(data)

    df["observed"] = pd.to_datetime(df["observed"], utc=True)

    dates = []
    x_labels = []
    formatted_dates = []
    
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
        end_idx = df.index[df["date_string"] <= to_date].max()
        if pd.isna(end_idx):
            end_idx = len(df) - 1
    else:
        end_idx = len(df) - 1

    if log:
        logging.info(f"Data information for {sheet_name}")
        logging.info(data.info())
        logging.info(data.describe())
    
    sns.set_theme(style="ticks")
    sns.set_context(None, font_scale=1)

    plt.rcParams["font.family"] = "DeJavu Serif"
    plt.rcParams["font.serif"] = "Times New Roman"

    fig, ax = plt.subplots(figsize=(6, 4))
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

    # placeringen af datostemplerne i plottet for at undgå overlap med xaksen
    '''num_ticks = min(10, len(df))
    tick_positions = [i * (len(df) - 1) // (num_ticks - 1) for i in range(num_ticks)]
    tick_labels = [df["formatted_date"].iloc[pos] for pos in tick_positions]'''

    #ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%Y"))
    #ax.set_xticks(tick_positions)
    #ax.set_xlim(None, end_idx)
    

    location_name = sheet_name.split("_")[1].capitalize()
    #ax.set_title(f"Vandstand {location_name}", fontsize=14, loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("Vandstand (cm)", fontsize=12)
    ax.tick_params(axis="both", labelsize=9)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_edgecolor("black")

    fig.tight_layout()

    return fig, sheet_name

if __name__ == "__main__":
    output_folder = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bachelorprojekt\grafer\vandstands_grafer"

    for sheet_name in water_level_sheets:
        print(f"Behandler ark: {sheet_name}")

        try: 
            fig, current_sheet = process_water_level_data(sheet_name)

            gemmes = True
            if gemmes:
                chartsave = os.path.join(output_folder, f"{current_sheet}_vandstandsplot.{format}")
                format = "jpg"
                fig.savefig(chartsave, dpi=600, format=format)
                print(f"Gemt til {chartsave}")

        except Exception as e:
            logging.error(f"Fejl ved behandling af ark {sheet_name}: {str(e)}")

    print("Alle ark er blevet behandlet")
