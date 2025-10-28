import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

with_mimic = True
if with_mimic:

    # assign the x values as observed values from the storm surge event
    observed: np.ndarray = np.array([74.9, 74.9, 37.3, 3.7, 56.4, 56.3])

    # assign the y values to the simulated values from the Inundaiton mOdel
    simulated: np.ndarray = np.array([137.5, 71.4, 36.0, 3.6, 41.0, 66.1])

    # assign names of the study sites
    locations: list[str] = ["Aabenraa", "Aabenraa (with emergency response)", "Gedser", "Hesnæs", "Præstø", "Præstø (Collapsed Sluice Gate)"]

    #random bullshit go
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    plt.rcParams["axes.labelsize"] = 8
    plt.rcParams["legend.fontsize"] = 8
    plt.rcParams["xtick.labelsize"] = 15
    plt.rcParams["ytick.labelsize"] = 15
    plt.rcParams["axes.linewidth"] = 0.5
    plt.rcParams["lines.linewidth"] = 1.0
    plt.rcParams["grid.linewidth"] = 0.5
    plt.rcParams["xtick.direction"] = "out"
    plt.rcParams["ytick.direction"] = "out"


    plt.figure(figsize=(6,4))
    plt.scatter(observed, simulated, color="blue", marker="+", s=20)

    # assign text to plot
    # for x, y, label
    for x, y, label in zip(observed.tolist(), simulated.tolist(), locations):
        x_val: float = float(x)
        y_val: float = float(y)
        label_str: str = label
        plt.text(x_val + 2, y_val - 1.5, label_str, size=8)
else:
    # assign the x values as observed values from the storm surge event
    observed: np.ndarray = np.array([74.9, 37.3, 3.7, 56.3])

    # assign the y values to the simulated values from the Inundaiton mOdel
    simulated: np.ndarray = np.array([137.5, 36.0, 3.6, 41.0])

    # assign names of the study sites
    locations: list[str] = ["Aabenraa", "Gedser", "Hesnæs", "Præstø"]

    #random bullshit go
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman"]
    plt.rcParams["axes.labelsize"] = 8
    plt.rcParams["legend.fontsize"] = 8
    plt.rcParams["xtick.labelsize"] = 15
    plt.rcParams["ytick.labelsize"] = 15
    plt.rcParams["axes.linewidth"] = 0.5
    plt.rcParams["lines.linewidth"] = 1.0
    plt.rcParams["grid.linewidth"] = 0.5
    plt.rcParams["xtick.direction"] = "out"
    plt.rcParams["ytick.direction"] = "out"


    plt.figure(figsize=(6,4))
    plt.scatter(observed, simulated, color="blue", marker="+", s=20)

    # assign text to plot
    # for x, y, label
    for x, y, label in zip(observed.tolist(), simulated.tolist(), locations):
        x_val: float = float(x)
        y_val: float = float(y)
        label_str: str = label
        plt.text(x_val + 2, y_val - 1.5, label_str, size=8)

# X = observed.reshape(-1, 1)
# y = simulated
# model = LinearRegression().fit(X, y)
# y_pred = model.predict(X)
# r2 = r2_score(y, y_pred)
# draw the line of agreement
lims: list[float] = [
    0.0,
    float(max(np.max(observed) + 10, np.max(simulated))+ 10)
]



plt.plot(lims, lims, '--k' , alpha=0.5)
plt.text(132, 125, "1:1", size=11)
#plt.plot(observed, y_pred, color="red", linestyle="-", label=f"Linear fit: (R^2: {r2:.2f})")

plt.xlabel("Observed inundated area (ha)", fontsize=9)
plt.ylim(top=140)
plt.xlim(right=140)
plt.ylabel("Simulated inundated area (ha)", fontsize=9)
plt.tick_params("both", labelsize=8)
#plt.legend(loc="best", fontsize=8)
plt.grid(False)
plt.axis([0,140,0,140])
plt.tight_layout()

output_folder: str = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\second_draft_29092025\images\engelsk\jpg"

gemmes: bool = False
if gemmes:
    chartsave: str = os.path.join(output_folder, f"XY_plot_for_area.jpg")
    format: str = "jpg"
    plt.savefig(chartsave, dpi=600, format=format)
    print(f"Gemt som {format} i {chartsave}")
