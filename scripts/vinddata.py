'''
Dette script er lavet til at håndtere vinddata fra DMI og tegne vindretningen.
'''

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
import matplotlib.dates as mdates
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

logging.basicConfig(level=logging.INFO)

sheet_id = "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
wind_sheets = ["vinddata_danmark"]

log = False

def wind_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    data = pd.read_csv(url, decimal=".")
    df = pd.DataFrame(data)

    location = sheet_name.replace("vinddata_", "").capitalize()

    # en liste der indeholder retningerne og tilhørende vinkler
    directions_to_angle = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }

    

    # ændrer datostemplet til et Day/Month/Year format
    if "tidspunkt" in df.columns:
        df["tidspunkt"] = pd.to_datetime(df["tidspunkt"], format="%d/%m/%Y", errors="coerce")

    sns.set_theme(style="ticks")
    sns.set_context(None, font_scale=1)

    plt.rcParams["font.family"] = "DeJavu Serif"
    plt.rcParams["font.serif"] = "Times New Roman"

    fig, main_ax = plt.subplots(figsize=(8, 4))

    # plotter alle tre datasæt
    if "tidspunkt" in df.columns:
        if "Middelvind" in df.columns:
            sns.lineplot(data=df, x="tidspunkt", y="Middelvind", ax=main_ax, label="Middelvind", marker="o", color="#73c5ce")
        if "High10minMiddel" in df.columns:
            sns.lineplot(data=df, x="tidspunkt", y="High10minMiddel", ax=main_ax, label="Højeste 10-min middelvind", marker="X", color="#e5ab01")
        if "HøjesteWind" in df.columns:
            sns.lineplot(data=df, x="tidspunkt", y="HøjesteWind", ax=main_ax, label="Højeste vindhastighed", marker="^", color="#cc1f1f")
        
        #ændring af datoformat
        date_format = mdates.DateFormatter("%d/%m\n%Y")
        main_ax.xaxis.set_major_formatter(date_format)
        main_ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))


        #main_ax.set_title(f"Vinddata for {location}", fontsize=14, loc="left")
        main_ax.set_xlabel("", fontsize=8)
        main_ax.set_ylabel("Vindhastighed (m/s)", fontsize=10)
        main_ax.tick_params(axis="both", labelsize=8)
        main_ax.legend(
            loc="best",
            fontsize=8,
            frameon=True,
            facecolor="white",
            edgecolor="black",
            shadow=False,
            fancybox=True,
            borderpad=0.5,
            labelspacing=0.5
        )

        # søger efter retning i df
        if "retning" in df.columns:
            
            # danner en ny akse til vindretningspilene. afhænger af grafens størrelse
            fig_height = fig.get_figheight()
            fig.set_figheight(fig_height * 1.1)  
            
            arrow_ax = fig.add_axes([0.087, 0.000, 0.89, 0.03])  
            
            # placeringen af pile
            arrow_ax.set_xticks([])
            arrow_ax.set_yticks([])
            for spine in arrow_ax.spines.values():
                spine.set_visible(False) # sættes til False for at være usynlig
            
          
            arrow_ax.set_xlim(main_ax.get_xlim())
            arrow_ax.set_ylim([0, 1])

            '''arrow_ax.text(
                main_ax.get_xlim()[0] + (main_ax.get_xlim()[1] - main_ax.get_xlim()[0]) * 0.01,
                0.5,
                "Vindretning:",
                fontsize=6,
                verticalalignment='center'
            )'''
            
            
            # hver vindretning konverteres til en vinkel og tildeles en pil med arrowprops
            for idx, row in df.iterrows(): # idx er unødvendig
                if pd.notnull(row["retning"]) and row["retning"] in directions_to_angle:
                    x_date = mdates.date2num(row["tidspunkt"]) # da xaksen er i datoformat omregnes der til en num værdi der knyttes til hver retning
                    angle = directions_to_angle[row["retning"]]
                    
                    # længden af pilen
                    arrow_length = 0.3
                    
                    # beregner pilens x og y koordinater baseret på vinklen
                    dx = arrow_length * np.sin(np.radians(angle))
                    dy = arrow_length * np.cos(np.radians(angle))
                    
                    # tegner
                    arrow_ax.annotate(
                        '',
                        xy=(x_date + dx, 0.5 + dy),
                        xytext=(x_date, 0.5),
                        arrowprops=dict(arrowstyle="->", lw=0.8, color="black", mutation_scale=10)
                    )
        

        plt.xticks(rotation=0)
        fig.tight_layout()
        
        save = True
        if save: 
            output_folder = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bachelorprojekt\grafer\vinddata_grafer"  
            plt.savefig(f"{output_folder}/{location}_vinddata.pdf", dpi=600, format="pdf") 

        plt.show()

    return fig, df

#main
def main():
    all_data = {}

    for sheet in wind_sheets:
        try:
            all_data[sheet] = wind_data(sheet)
        except Exception as e:
            logging.error(f"Fejl ved behandling af ark {sheet}: {str(e)}")

if __name__ == "__main__":
    main()
    print("Alle ark er blevet behandlet")
