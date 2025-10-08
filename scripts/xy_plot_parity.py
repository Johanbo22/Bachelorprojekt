import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


# assign the x values as observed values from the storm surge event
observed: np.ndarray = np.array([70.7, 34.5, 3.5, 53.5])

# assign the y values to the simulated values from the Inundaiton mOdel
simulated: np.ndarray = np.array([129.8, 33.2, 3.3, 39.8])

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
    plt.text(x_val + 2, y_val -1, label_str, size=8)

# X = observed.reshape(-1, 1)
# y = simulated
# model = LinearRegression().fit(X, y)
# y_pred = model.predict(X)
# r2 = r2_score(y, y_pred)
# draw the line of agreement
lims: list[float] = [
    0.0,
    float(max(np.max(observed), np.max(simulated)))
]



plt.plot(lims, lims, '--k' , label="Line of Simulated=Observed", alpha=0.5)
#plt.plot(observed, y_pred, color="red", linestyle="-", label=f"Linear fit: (R^2: {r2:.2f})")

plt.xlabel("Observed inundated area in hectares", fontsize=9)
plt.ylabel("Simulated inundated area in hectares", fontsize=9)
plt.tick_params("both", labelsize=8)
plt.legend(loc="best", fontsize=8)
plt.grid(False)
plt.tight_layout()

output_folder: str = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\second_draft_29092025\images\engelsk\jpg"

gemmes: bool = True
if gemmes:
    chartsave: str = os.path.join(output_folder, f"XY_plot_for_area.jpg")
    format: str = "jpg"
    plt.savefig(chartsave, dpi=600, format=format)
    print(f"Gemt som {format} i {chartsave}")
