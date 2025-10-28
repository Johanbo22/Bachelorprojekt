import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import radians
from matplotlib.dates import DateFormatter, DayLocator
import seaborn as sns
from matplotlib.lines import Line2D

sheet_name = "vinddata_danmark"
sheet_id = "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
URL = f"https://docs.google.com/spreadsheets/d/1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0/gviz/tq?tqx=out:csv&sheet=vinddata_danmark"

# Mapping of cardinal direction strings to degrees (0=East, 90=North, clockwise rotation)
# This mapping is used because matplotlib's standard coordinate system is Cartesian 
# (East=0, North=90).
DIRECTION_TO_DEGREES = {
    "N": 90.0, "NNE": 67.5, "NE": 45.0, "ENE": 22.5,
    "E": 0.0, "ESE": 337.5, "SE": 315.0, "SSE": 292.5,
    "S": 270.0, "SSW": 247.5, "SW": 225.0, "WSW": 202.5,
    "W": 180.0, "WNW": 157.5, "NW": 135.0, "NNW": 112.5
}

def get_uv_components(direction_string):
    if direction_string not in DIRECTION_TO_DEGREES:
        print(f"Warning: Unknown direction '{direction_string}'. Skipping arrow.")
        return 0, 0
    
    # Get angle in degrees (Cartesian: East=0, North=90)
    angle_deg = DIRECTION_TO_DEGREES[direction_string]
    # Convert to radians for sin/cos functions
    angle_rad = radians(angle_deg)
    
    # u (x-component) is cos(angle_rad)
    u = np.cos(angle_rad)
    # v (y-component) is sin(angle_rad)
    v = np.sin(angle_rad)
    
    return u, v

def plot_wind_data(filename):
    df = None 
    try:
        #
        df = pd.read_csv(filename, sep=',', decimal=".", skipinitialspace=True)
        df.columns = df.columns.str.strip()
        df['tidspunkt'] = pd.to_datetime(df['tidspunkt'], format="%d/%m/%Y", errors="coerce")
        
        sns.set_theme(style="ticks")
        sns.set_context(None, font_scale=1)
        #plt.style.use('seaborn-v0_8-whitegrid') # Use a clean, modern style
        plt.rcParams["font.family"] = "DeJavu Serif"
        plt.rcParams["font.serif"] = "Times New Roman"

        
        fig, ax = plt.subplots(figsize=(7.5, 4.5)) # Slightly larger figure

        sns.lineplot(data=df, x='tidspunkt', y='Middelvind', ax=ax, 
                label='Mean wind speed', marker='o', linestyle='-', color='#2c7bb6', zorder=5) 
        sns.lineplot(data=df, x='tidspunkt',  y='High10minMiddel', 
                label='Highest 10-min mean wind speed', marker='X', linestyle='--', color='#fdae61', zorder=5)
        sns.lineplot(data=df, x='tidspunkt',  y='HøjesteWind', 
                label='Highest wind speed', marker='^', linestyle=':', color='#d7191c', zorder=5)

        
        u_components = []
        v_components = []
        
        for direction in df['retning']:
            u, v = get_uv_components(direction)
            u_components.append(u)
            v_components.append(v)

        
        arrow_y_position = -1.0 
        
        
        arrow_start_y = [arrow_y_position - 0.5] * len(df)
        arrow_start_x = df['tidspunkt']

        
        ax.quiver(
            arrow_start_x, 
            arrow_start_y, 
            u_components, 
            v_components, 
            scale=75,          
            width=0.0015,    
            headwidth=4,      
            headlength=4,
            color='black', 
            zorder=10 
        )

        ##Draw a colored band
        ax.axhspan(arrow_y_position - 5, arrow_y_position + 1, facecolor='lightgray', alpha=0.2, zorder=0)

        
        # text_offset = 0.5 
        # for x, y, direction in zip(df['tidspunkt'], arrow_start_y, df['retning']):
        #     ax.text(x, y + text_offset, direction, 
        #             fontsize=9, ha='center', va='bottom', color='black', 
        #             fontweight='bold', # Make the direction text stand out
        #             bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', boxstyle='round,pad=0.2'), zorder=11)
        
        
        #ax.text(df['tidspunkt'].min(), arrow_y_position - 1.5, 'Wind Direction', 
                #fontsize=11, va='center', ha='left', color='dimgray')
        arrow_handle = Line2D([0], [0], color='black', marker=r'$\rightarrow$', markersize=10, linestyle='', label='Wind Direction', markeredgewidth=0)
        handles, labels = ax.get_legend_handles_labels()
        handles.append(arrow_handle)
        labels.append("Wind Direction")
        # 
        #ax.set_title('Wind Speed and Direction Analysis', fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=9)
        ax.set_ylabel('Wind Speed (ms⁻¹)', fontsize=10)
        ax.tick_params(axis="both", labelsize=8)
        
        # F
        date_format = DateFormatter("%d/%m\n%Y")
        ax.xaxis.set_major_formatter(date_format)
        ax.xaxis.set_major_locator(DayLocator(interval=3)) # Sy 3 days

        #fig.autofmt_xdate(rotation=45, ha='right') 

        # d
        y_min = arrow_y_position - 2 # Go lower than the arrow base
        ax.set_ylim(bottom=y_min, top=df['HøjesteWind'].max() + 3)
        
        # 
        #ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.legend(handles=handles, labels=labels, loc='best',ncol=1, fontsize=7, facecolor="white", edgecolor="black", frameon=True, fancybox=True, shadow=False, borderpad=0.5, labelspacing=0.5)

        plt.tight_layout() 
        save = True
        if save: 
            output_folder = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel"  
            plt.savefig(f"{output_folder}/Danmark_vinddata.jpg", dpi=600, format="jpg")
            print("Gemt")
        else:
            print("Ikke gemt")
        plt.show()
        

    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except KeyError as ke:
        print(f"Error: Column '{ke}' not found. Check that the columns in your CSV are: tidspunkt, Middelvind, High10minMiddel, HøjesteWind, retning.")
        if df is not None:
            print(f"Available columns found: {list(df.columns)}")
        else:
            print("Data frame could not be loaded at all.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    

if __name__ == '__main__':
    
    plot_wind_data(URL)
