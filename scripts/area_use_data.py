import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
import textwrap
import logging
import os

# Logging opstart
logging.basicConfig(level=logging.INFO)

# unikt google sheets id og arknavne
sheet_id = "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
sheet_names = ["aabenraa", "gedser", "hesnaes", "praestoe"]

#sæt til True for at logge
log = False

def process_sheet(sheet_name, datatype):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    data = pd.read_csv(url, decimal=",")
    df = pd.DataFrame(data)

    # vis data information for tjeksum
    if log:
        logging.info(f"Data information for {sheet_name}")
        logging.info(data.info())
        logging.info(data.describe())
    
    # sætter kontekst og tema for seaborn-plot
    sns.set_theme(style="ticks")
    sns.set_context(None, font_scale=1) # øhhh kan ikke huske hvad denne gør. tema er plot designet, men kontekst er noget andet.

    # sætter skrifttype parametre
    plt.rcParams["font.family"] = "DeJavu Serif"
    plt.rcParams["font.serif"] = "Times New Roman"

    if datatype == "procent":
        
        # smelter dataramen sammen til at skabe et enkelt diagram for hvert område og dermed sammenligne model v målt
        df_melted = pd.melt(
            df,
            id_vars=["CLASS"],
            value_vars=["%_AREA_REAL", "%_AREA_MODEL"],
            var_name="Type",
            value_name="Percentage"
        )

        # ændrer navne på kolonnerne 
        df_melted["Type"] = df_melted["Type"].replace({
            '%_AREA_REAL': 'Observeret stormflod',
            '%_AREA_MODEL': 'Simuleret stormflod'
        })

        # plot
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.barplot(
            x="CLASS",
            y="Percentage",
            hue="Type",
            data=df_melted,
            palette={'Observeret stormflod': '#3b9ae5', 'Simuleret stormflod': '#f28e14'},
            ax=ax
        )
        
        ax.set_ylabel("Oversvømmet areal i % af total areal", fontsize=10)
        # ændrer yaksens format til %
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1, 0, "", True))
        ax.yaxis.set_major_locator(mtick.MultipleLocator(0.1))
        
        ax.tick_params(axis="y", labelsize=8)
        
    if datatype == "area_m2":
        # smelter dataramen sammen til at skabe et enkelt diagram for hvert område og dermed sammenligne model v målt
        df_melted = pd.melt(
            df,
            id_vars=["CLASS"],
            value_vars=["AREA_REAL_M2", "AREA_MODEL_M2"],
            var_name="Type",
            value_name="Area"
        )

        # ændrer navne på kolonnerne 
        df_melted["Type"] = df_melted["Type"].replace({
            'AREA_REAL_M2': 'Observeret stormflod',
            'AREA_MODEL_M2': 'Simuleret stormflod'
        })

        # plot
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.barplot(
            x="CLASS",
            y="Area",
            hue="Type",
            data=df_melted,
            palette={'Observeret stormflod': '#3b9ae5', 'Simuleret stormflod': '#f28e14'},
            ax=ax
        )
        
        ax.set_ylabel("Oversvømmet areal i m²", fontsize=10)
        
        ax.tick_params(axis="y", labelsize=7)
    
    if datatype == "ha":
        # smelter dataramen sammen til at skabe et enkelt diagram for hvert område og dermed sammenligne model v målt
        df_melted = pd.melt(
            df,
            id_vars=["CLASS"],
            value_vars=["AREA_REAL_HA", "AREA_MODEL_HA"],
            var_name="Type",
            value_name="Area"
        )

        # ændrer navne på kolonnerne 
        df_melted["Type"] = df_melted["Type"].replace({
            'AREA_REAL_HA': 'Observeret stormflod',
            'AREA_MODEL_HA': 'Simuleret stormflod'
        })

        # plot
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.barplot(
            x="CLASS",
            y="Area",
            hue="Type",
            data=df_melted,
            palette={'Observeret stormflod': '#3b9ae5', 'Simuleret stormflod': '#f28e14'},
            ax=ax
        )
        
        ax.set_ylabel("Oversvømmet areal i ha", fontsize=10)
        
        ax.tick_params(axis="y", labelsize=8)

    # gør så teksten på xaksen er ombrydelig
    wrapped_labels = wrap_labels(df["CLASS"])
    ax.set_xticklabels(wrapped_labels, rotation=30, fontsize=7)

    # fjerner labels fra akserne
    #ax.set_title(f"Arealanvendelse i {sheet_name}", fontsize=14, loc="left")
    ax.set_xlabel("Arealklasser", fontsize=10)
    
    # legend
    ax.legend(
        loc="best",
        fontsize=8,
        frameon=True,
        facecolor="white",
        edgecolor="black",
        shadow=False,
        fancybox=False,
        borderpad=0.5,
        labelspacing=0.2,
        handlelength=2,
        handleheight=1.8
    )

    # kassen omkring plottet
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_edgecolor("black")

    fig.tight_layout()

    return fig, sheet_name

# funktion der håndterer ombrydning af teksten
def wrap_labels(labels, width=15):
    return [textwrap.fill(label, width) for label in labels] # sikrer at hver label bliver wrappet? wrapped?

# main
if __name__ == "__main__":
    output_folder = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bachelorprojekt\grafer\areal_anvendelses_grafer"

    print(f"Behandler arkene {sheet_names}")

    # behandler hvert ark VÆLG MELLEM "procent" ELLER "area" gælder ikke mere
    # gemmer for arealanvendelse i procent
    for sheet_name in sheet_names:
        fig, current_sheet = process_sheet(sheet_name, "procent")
        
        # sæt til True for at gemme
        gemmes = True
        if gemmes: 
            chartsave = os.path.join(output_folder, f"{current_sheet}_arealanvendelse.jpg")
            format = "jpg" # format 
            fig.savefig(chartsave, dpi=600, format=format)
            
            print(f"Gemt som {format} i {chartsave}")
    
    # Gemmer for m^2
    for sheet in sheet_names:
        fig, current_sheet = process_sheet(sheet, "area_m2")
        
        gemmes = False
        if gemmes:
            chartsave = os.path.join(output_folder, f"{current_sheet}_oversvommet_areal_m2.jpg")
            format = "jpg"
            fig.savefig(chartsave, dpi=600, format=format)
            
            print(f"Gemt som {format} i {chartsave}")
    
    # Gemmer for hektar
    for sheet in sheet_names:
        fig, current_sheet = process_sheet(sheet, "ha")

        gemmes = True
        if gemmes:
            chartsave = os.path.join(output_folder, f"{current_sheet}_oversvommet_Hektar.jpg")
            format = "jpg"
            fig.savefig(chartsave, dpi=600, format=format)
            print(f"Gemt som {format} i {chartsave}")


    print(f"Alle ark er blevet behandlet")
