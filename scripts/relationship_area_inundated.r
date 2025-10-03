library(ggplot2)
library(dplyr)
library(stringr)
library(extrafont)

# Data setup
observed <- c(70.7, 34.5, 3.5, 53.5)
simulated <- c(129.8, 33.2, 3.3, 39.8)
locations <- c("Aabenraa", "Gedser", "Hesnæs", "Præstø")

df <- data.frame(
  observed = observed,
  simulated = simulated,
  location = locations
)


lims <- c(0, max(c(observed, simulated)))


p <- ggplot(df, aes(x = observed, y = simulated)) +
  geom_point(color = "blue", shape = 3, size = 2) +  # shape 3 = "+"
  geom_text(aes(label = location), hjust = 0, nudge_x = 1, size = 2.5) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "black", alpha = 0.5) +
  scale_x_continuous(limits = lims) +
  scale_y_continuous(limits = lims) +
  labs(
    x = "Observed inundated area in hectares",
    y = "Simulated inundated area in hectares"
  ) +
  theme_minimal(base_family = "Times New Roman") +
  theme(
    axis.title = element_text(size = 8),
    axis.text = element_text(size = 8),
    legend.position = "none",
    panel.border = element_rect(color = "black", fill = NA, linewidth = 0.5),
    axis.ticks.length = unit(0.2, "cm"),
    axis.ticks = element_line(linewidth = 0.5),
    axis.text.x = element_text(angle = 0, vjust = 0.5),
    axis.text.y = element_text(angle = 0, hjust = 1)
  )


output_folder <- "C:/Users/joha4/OneDrive/Skrivebord_LapTop/Bsc_artikel/scripts"
ggsave(filename = file.path(output_folder, "XY_plot_for_area.jpg"),
       plot = p, dpi = 600, width = 6, height = 4, units = "in")
