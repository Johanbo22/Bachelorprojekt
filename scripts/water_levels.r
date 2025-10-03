library(ggplot2)
library(readr)
library(lubridate)
library(dplyr)
library(scales)
library(stringr)


sheet_id <- "1RhK_viiUoW2F_Qc6Wu1L-4nVdepBwTcnIYfxZDG58j0"
water_level_sheets <- c("vandstand_aabenraa", "vandstand_gedser", "vandstand_hesnaes", "vandstand_praestoe_roedvig")

label_map <- list(
  aabenraa = "(a)",
  gedser = "(b)",
  hesnaes = "(c)",
  praestoe = "(d)"
)

output_folder <- "C:/Users/joha4/OneDrive/Skrivebord_LapTop/Bsc_artikel/second_draft_29092025/images/engelsk/jpg"

process_water_level_data <- function(sheet_name) {
  url <- paste0("https://docs.google.com/spreadsheets/d/", sheet_id, "/gviz/tq?tqx=out:csv&sheet=", sheet_name)
  df <- read_csv(url, locale = locale(decimal_mark = ","))

  df <- df %>%
    mutate(observed = ymd_hms(observed, tz = "UTC")) %>%
    arrange(observed)

  location_key <- tolower(str_split(sheet_name, "_")[[1]][2])
  subplot_label <- label_map[[location_key]]
  location_name <- str_to_title(location_key)

  p <- ggplot(df, aes(x = observed, y = value)) +
    geom_line(color = "#044da1", linewidth = 1.1) +
    geom_point(color = "#044da1", size = 0.8) +
    annotate("text", x = min(df$observed), y = max(df$value), label = subplot_label,
             hjust = 0, vjust = 1, fontface = "bold", size = 4) +
    scale_x_datetime(labels = date_format("%d/%m\n%Y")) +
    labs(y = "Water level (cm)", x = NULL) +
    theme_minimal(base_family = "Times New Roman") +
    theme(
      axis.text = element_text(size = 9),
      axis.title.y = element_text(size = 12),
      panel.border = element_rect(color = "black", fill = NA, linewidth = 0.5)
    )

  
  if (sheet_name == "vandstand_hesnaes") {
    p <- p + 
      geom_point(aes(x = as.POSIXct("2023-10-20 20:30:10", tz = "UTC"), y = 239),
                 color = "red", shape = 4, size = 2)
  }

  
  ggsave(filename = paste0(output_folder, "/", sheet_name, "_vandstandsplot.jpg"),
         plot = p, dpi = 600, width = 6, height = 4, units = "in")
}


for (sheet_name in water_level_sheets) {
  message("Behandler ark: ", sheet_name)
  tryCatch({
    process_water_level_data(sheet_name)
    message("Gemt til ", sheet_name)
  }, error = function(e) {
    message("Fejl ved behandling af ark ", sheet_name, ": ", e$message)
  })
}

message("Alle ark er blevet behandlet")
