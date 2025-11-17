import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def plot_xy_parity(with_mimic: bool, gemmes: bool, format: str, output_folder: str):
    if with_mimic:
        observed = np.array([75.0, 75.0, 37.3, 3.7, 56.3, 56.3])
        simulated = np.array([137.5, 71.4, 36.0, 3.6, 41.1, 66.1])
        locations = ["Aabenraa", "Aabenraa (with emergency response)","Gedser","Hesnæs", "Præstø", "Præstø (Collapsed Sluice Gate)"
        ]
    else:
        observed = np.array([75, 37.3, 3.7, 56.3])
        simulated = np.array([137.5, 36.0, 3.6, 41.1])
        locations = ["Aabenraa", "Gedser", "Hesnæs", "Præstø"]

    plt.figure(figsize=(4, 4))
    plt.scatter(observed, simulated, color="blue", marker="+", s=20)

    for x, y, label in zip(observed.tolist(), simulated.tolist(), locations):
        plt.text(float(x) + 2, float(y) - 2.5, label, size=8)
    
    lims = [0.0, float(max(np.max(observed) + 10, np.max(simulated)) + 10)]
    plt.plot(lims, lims, '--k', alpha=0.5)

    plt.text(127, 120, "1:1", size=11)

    plt.xlabel("Observed flooding extent (ha)", fontsize=9)
    plt.ylabel("Simulated flooding extent (ha)", fontsize=9)
    plt.tick_params("both", labelsize=8)
    plt.grid(False)
    plt.axis([0, 140, 0, 140])
    plt.tight_layout()

    if gemmes:
        filename = f"XY_plot_for_area_with_extra_{with_mimic}.{format}"
        chartsave = os.path.join(output_folder, filename)
        plt.savefig(chartsave, format=format)
        print(f"Gemt som {format} i {chartsave}")
    else:
        print("Viser graf")

#Uden mimic som EPS
plot = True
if plot:
    plot_xy_parity(with_mimic=False, gemmes=True, format="jpg", output_folder=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\images")



#med mimic
plot2 = False
if plot2:
    plot_xy_parity(with_mimic=True, gemmes=True, format="jpg", output_folder=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\images")
