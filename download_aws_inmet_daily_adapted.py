# -*- coding: utf-8 -*-
"""download_AWS_INMET_daily_adapted.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1r6QtaZbCqv3581ntueL151VyE54p8TmI
"""

install.packages("BrazilMet")

library(tidyverse)
library(BrazilMet)

# Função adaptada para fazer o download de diversas estações
download_AWS_INMET_daily_adapted <- function(stations, start_date, end_date) {
  year <- substr(start_date, 1, 4)
  tempdir <- tempfile()
  tf <- paste0(gsub("\\", "/", tempdir, fixed = TRUE), ".zip")
  outdir <- gsub("\\", "/", tempdir, fixed = TRUE)
  utils::download.file(url = paste0(
    "https://portal.inmet.gov.br/uploads/dadoshistoricos/",
    year, ".zip"
  ), destfile = tf, method = "auto", cacheOK = F)
  a <- unzip(zipfile = tf, exdir = outdir, junkpaths = T)
  pasta <- paste0(outdir)
  # Criando dataframe para conseguir fazer o join
  df_combined <- data.frame()
  for (station in stations) {
    if (length(list.files(pasta,
                          pattern = station, full.names = T,
                          all.files = T
    )) == 0) {next} else {
      list.files(pasta, pattern = station)
      b <- read.csv(
        file = list.files(pasta,
                          pattern = station,
                          full.names = T
        ), header = T, sep = ";", skip = 8,
        na = "-9999", dec = ",", check.names = F
      )
      a <- as.data.frame(a)
      X <- `pressao-max(mB)` <- `pressao-min(mB)` <- Data <- Hora <- NULL
      `to-min(C)` <- `to-max(C)` <- `tar_min(C)` <- `tar_max(C)` <- `tbs(C)` <- NULL
      `ppt-h (mm)` <- `pressao (mB)` <- `UR-max` <- `UR-min` <- UR <- NULL
      `U10 (m/s)` <- `U-raj (m/s)` <- `U-dir(degrees)` <- `RG(Kj/m2)` <- `RG(Mj/m2)` <- NULL
      df <- data.frame(matrix(ncol = 18, nrow = 0))
      colnames(df) <- c(
        "Data", "Hora", "ppt-h (mm)", "pressao (mB)",
        "RG(Mj/m2)", "tbs-(C)", "tpo(C)", "tar_max(C)", "tar_min(C)",
        "to-max(C)", "to-min(C)", "UR-max", "UR-min", "UR",
        "U-dir(degrees)", "U-raj (m/s)", "U10 (m/s)", "OMM"
      )
      metadados <- read.csv(file = list.files(pasta,
                                              pattern = station,
                                              full.names = T
      ), header = F, sep = ";")

      UF <- metadados[2, 2]
      Station <- metadados[3, 2]
      OMM <- metadados[4, 2]

      latitude <- metadados[5, 2]
      latitude <- gsub(",", replacement = ".", latitude)
      latitude <- as.numeric(latitude)

      longitude <- metadados[6, 2]
      longitude <- gsub(",", replacement = ".", longitude)
      longitude <- as.numeric(longitude)

      altitude <- metadados[7, 2]
      altitude <- gsub(",", replacement = ".", altitude)
      altitude <- as.numeric(altitude)

      dfx <- read.csv(
        file = list.files(pasta,
                          pattern = station,
                          full.names = T
        ), header = T, sep = ";", skip = 8,
        na = "-9999", dec = ",", check.names = F
      )
      names(dfx) <- c(
        "Data", "Hora", "ppt-h (mm)", "pressao (mB)",
        "pressao-max(mB)", "pressao-min(mB)", "RG(Kj/m2)",
        "tbs(C)", "tpo(C)", "tar_max(C)", "tar_min(C)", "to-max(C)",
        "to-min(C)", "UR-max", "UR-min", "UR", "U-dir(degrees)",
        "U-raj (m/s)", "U10 (m/s)", "X"
      )

      dfx <- dplyr::select(dfx, -X, -`pressao-max(mB)`, -`pressao-min(mB)`)
      dfx <- tibble::as_tibble(dfx)
      dfx <- dplyr::mutate(dfx, Data = as.Date(Data), Hora = as.numeric(as.factor(Hora)))
      dfx$date_hora <- paste0(dfx$Data, dfx$Hora)
      dfx$date_hora <- as.POSIXct(strptime(dfx$date_hora, format = "%Y-%m-%d %H"))

      for (i in 1:nrow(dfx)) {
        if (longitude > -37.5) {
          dfx$date_hora[i] <- dfx$date_hora[i] - as.difftime(2,
                                                             units = "hours"
          )
        } else if (longitude > -52.5) {
          dfx$date_hora[i] <- dfx$date_hora[i] - as.difftime(3,
                                                             units = "hours"
          )
        } else if (longitude > -67.5) {
          dfx$date_hora[i] <- dfx$date_hora[i] - as.difftime(4,
                                                             units = "hours"
          )
        } else if (longitude > -82.5) {
          dfx$date_hora[i] <- dfx$date_hora[i] - as.difftime(5,
                                                             units = "hours"
          )
        }
      }
      dfx$Data <- as.POSIXct(strptime(dfx$date_hora, format = "%Y-%m-%d"))
      dfx$Hora <- format(
        as.POSIXct(dfx$date_hora, format = "%Y-%m-%d %H"),
        "%H"
      )

      # Engenharia para dados de temperatura
      dfx_temp <- na.omit(dplyr::select(
        dfx, Hora, Data,
        `to-min(C)`, `to-max(C)`, `tar_min(C)`, `tar_max(C)`,
        `tbs(C)`
      ))
      n_dfx_temp <- group_by(dfx_temp, Data) %>%
        summarise(n = n()) %>%
        filter(n == 24)
      if (nrow(n_dfx_temp) == 0) {
        dfx_temps_day = data.frame(matrix(ncol = 8, nrow = 0))
        colnames(dfx_temps_day) = c("Data","tar_mean","tar_min(C)",
                                    "tar_max(C)","to_mean","to-min(C)",
                                    "to-max(C)","tbs(C)")
        dfx_temps_day$Data = as.Date(dfx_temps_day$Data)
      } else {
        dfx_temp <- left_join(dfx_temp, n_dfx_temp, by = "Data")
        dfx_temp <- dplyr::filter(dfx_temp, n == 24)
        dfx_temp <- dplyr::mutate(dfx_temp, tar_mean = (`tar_min(C)` +
                                                          `tar_max(C)`) / 2)
        dfx_temp <- dplyr::mutate(dfx_temp, to_mean = (`to-min(C)` +
                                                         `to-max(C)`) / 2)
        dfx_temp_mean_day <- aggregate(
          tar_mean ~ Data,
          dfx_temp, mean
        )
        dfx_temp_min_day <- aggregate(`tar_min(C)` ~
                                        Data, dfx_temp, min)
        dfx_temp_max_day <- aggregate(`tar_max(C)` ~
                                        Data, dfx_temp, max)
        dfx_to_min_day <- aggregate(
          `to-min(C)` ~ Data,
          dfx_temp, min
        )
        dfx_to_max_day <- aggregate(
          `to-max(C)` ~ Data,
          dfx_temp, max
        )
        dfx_to_mean_day <- aggregate(
          to_mean ~ Data,
          dfx_temp, mean
        )
        dfx_tbs_day <- aggregate(
          `tbs(C)` ~ Data, dfx_temp,
          mean
        )
        dfx_temps_day <- cbind(
          dfx_temp_mean_day, dfx_temp_min_day,
          dfx_temp_max_day, dfx_to_mean_day, dfx_to_min_day,
          dfx_to_max_day, dfx_tbs_day
        )
        dfx_temps_day <- dplyr::select(
          dfx_temps_day, # exclui as datas duplicadas
          -3, -5, -7, -9, -11, -13
        )
      }
      # Fim engenharia para dados de temperatura

      # Engenharia de dados para precipitação
      dfx_prec <- na.omit(dplyr::select(
        dfx, Hora,
        Data, `ppt-h (mm)`
      ))

      dfx_prec <- group_by(dfx_prec, Data)
      n_dfx_prec <- group_by(dfx_prec, Data) %>%
        summarise(n = n()) %>%
        filter(n == 24)
      if (nrow(n_dfx_prec) == 0) {
        dfx_prec_day = data.frame(matrix(ncol = 2, nrow = 0))
        colnames(dfx_prec_day) = c("Data","ppt-h (mm)")
        dfx_prec_day$Data = as.Date(dfx_prec_day$Data)
      } else {
        dfx_prec_day <- aggregate(
          `ppt-h (mm)` ~ Data,
          dfx_prec, sum
        )
      }
      # Fim engenharia de dados da precipitação

      # Engenharia de dados para pressão
      dfx_press <- na.omit(dplyr::select(
        dfx, Hora,
        Data, `pressao (mB)`
      ))
      n_dfx_press <- group_by(dfx_press, Data) %>%
        summarise(n = n()) %>%
        filter(n == 24)
      if (nrow(n_dfx_press) == 0) {
        dfx_press_mean_day = data.frame(matrix(ncol = 2, nrow = 0))
        colnames(dfx_press_mean_day) = c("Data","pressao (mB)")
        dfx_press_mean_day$Data = as.Date(dfx_press_mean_day$Data)
      } else {
        dfx_press <- left_join(dfx_press, n_dfx_press,
                               by = "Data"
        )
        dfx_press <- dplyr::filter(dfx_press, n ==
                                     24)
        dfx_press_mean_day <- aggregate(`pressao (mB)` ~
                                          Data, dfx_press, mean)
      }
      # Fim engenharia de dados da pressão

      # Engenharia de dados para umidade relativa
      dfx_ur <- na.omit(dplyr::select(
        dfx, Hora,
        Data, `UR-max`, `UR-min`, UR
      ))
      n_dfx_ur <- group_by(dfx_ur, Data) %>%
        summarise(n = n()) %>%
        filter(n == 24)
      if (nrow(n_dfx_ur) == 0) {
        dfx_urs_day = data.frame(matrix(ncol = 4, nrow = 0))
        colnames(dfx_urs_day) = c("Data","UR","UR-max","UR-min")
        dfx_urs_day$Data = as.Date(dfx_urs_day$Data)
      } else {
        dfx_ur <- left_join(dfx_ur, n_dfx_ur, by = "Data")
        dfx_ur <- dplyr::filter(dfx_ur, n == 24)
        dfx_ur_mean_day <- aggregate(
          UR ~ Data,
          dfx_ur, mean
        )
        dfx_ur_min_day <- aggregate(`UR-min` ~
                                      Data, dfx_ur, min)
        dfx_ur_max_day <- aggregate(`UR-max` ~
                                      Data, dfx_ur, max)
        dfx_urs_day <- cbind(
          dfx_ur_mean_day, dfx_ur_max_day,
          dfx_ur_min_day
        )
        dfx_urs_day <- dplyr::select(
          dfx_urs_day,
          -3, -5 # Retira colunas com datas duplicadas
        )
      } # Fim engenharia de dados da umidade relativa

      # Engenharia de dados para o vento
      dfx_vv <- na.omit(dplyr::select(
        dfx, Hora,
        Data, `U10 (m/s)`, `U-raj (m/s)`, `U-dir(degrees)`
      ))
      n_dfx_vv <- group_by(dfx_vv, Data) %>%
        summarise(n = n()) %>%
        filter(n == 24)
      if (nrow(n_dfx_vv) == 0) {
        dfx_vvs_day = data.frame(matrix(ncol = 4, nrow = 0))
        colnames(dfx_vvs_day) = c("Data","U10 (m/s)","U-raj (m/s)","U-dir(degrees)")
        dfx_vvs_day$Data = as.Date(dfx_vvs_day$Data)
      } else {
        dfx_vv <- left_join(dfx_vv, n_dfx_vv,
                            by = "Data"
        )
        dfx_vv <- dplyr::filter(dfx_vv, n ==
                                  24)
        dfx_vv_mean_day <- aggregate(`U10 (m/s)` ~
                                       Data, dfx_vv, mean)

        dfx_vv_raj_day <- aggregate(`U-raj (m/s)` ~
                                      Data, dfx_vv, max)
        dfx_vv_dir_day <- aggregate(`U-dir(degrees)` ~
                                      Data, dfx_vv, mean)
        dfx_vvs_day <- cbind(
          dfx_vv_mean_day,
          dfx_vv_raj_day,
          dfx_vv_dir_day
        )
        dfx_vvs_day <- dplyr::select(
          dfx_vvs_day,
          -3, -5 # Retira colunas com datas duplicadas
        )
      } # Fim da engenharia de dados para o vento

      # Engenharia para as variáveis de radiação
      dfx_RG <- dplyr::select(
        dfx, Hora, Data,
        `RG(Kj/m2)`
      )
      dfx_RG <- dplyr::mutate(dfx_RG, `RG(Mj/m2)` = `RG(Kj/m2)` / 1000)
      dfx_RG <- na.omit(dplyr::select(
        dfx_RG,
        -`RG(Kj/m2)`
      ))
      dfx_RG <- dplyr::filter(dfx_RG, `RG(Mj/m2)` >
                                0)
      n_RG <- group_by(dfx_RG, Data) %>%
        summarise(n = n()) %>%
        filter(n >= 12)
      if (nrow(n_RG) == 0) {
        dfx_RG_sum_day = data.frame(matrix(ncol = 4, nrow = 0))
        colnames(dfx_RG_sum_day) = c("Data","RG(Mj/m2)","julian_day","ra")
        dfx_RG_sum_day$Data = as.Date(dfx_RG_sum_day$Data)
      } else {
        dfx_RG <- left_join(dfx_RG, n_RG, by = "Data")
        dfx_RG <- dplyr::filter(dfx_RG, n >=
                                  12)
        dfx_RG_sum_day <- aggregate(`RG(Mj/m2)` ~
                                      Data, dfx_RG, sum)
        julian_day <- as.data.frame(as.numeric(format(
          dfx_RG_sum_day$Data,
          "%j"
        )))
        names(julian_day) <- "julian_day"
        dfx_RG_sum_day <- cbind(
          dfx_RG_sum_day,
          julian_day
        )
        lat_rad <- (pi / 180) * (latitude)
        dr <- 1 + 0.033 * cos((2 * pi / 365) *
                                dfx_RG_sum_day$julian_day)
        summary(dr)
        solar_declination <- 0.409 * sin(((2 *
                                             pi / 365) * dfx_RG_sum_day$julian_day) -
                                           1.39)
        sunset_hour_angle <- acos(-tan(lat_rad) *
                                    tan(solar_declination))
        ra <- ((24 * (60)) / pi) * (0.082) *
          dr * (sunset_hour_angle * sin(lat_rad) *
                  sin(solar_declination) + cos(lat_rad) *
                  cos(solar_declination) * sin(sunset_hour_angle))
        ra <- as.data.frame(ra)
        dfx_RG_sum_day <- cbind(
          dfx_RG_sum_day,
          ra
        )
      } # Fim da engenharia de radiação

      dates_of_the_year <- seq.Date(as.Date(start_date), as.Date(end_date), by = "days")
      dates_of_the_year <- as.Date(dates_of_the_year, format = "%Y-%m-%d")
      dfx_day <- data.frame(Data = dates_of_the_year)

      dfx_temps_day$Data <- as.POSIXct(strptime(dfx_temps_day$Data, format = "%Y-%m-%d"))
      dfx_prec_day$Data <- as.POSIXct(strptime(dfx_prec_day$Data, format = "%Y-%m-%d"))
      dfx_press_mean_day$Data <- as.POSIXct(strptime(dfx_press_mean_day$Data, format = "%Y-%m-%d"))
      dfx_urs_day$Data <- as.POSIXct(strptime(dfx_urs_day$Data, format = "%Y-%m-%d"))
      dfx_vvs_day$Data <- as.POSIXct(strptime(dfx_vvs_day$Data, format = "%Y-%m-%d"))
      dfx_RG_sum_day$Data <- as.POSIXct(strptime(dfx_RG_sum_day$Data, format = "%Y-%m-%d"))

      dfx_day <- dplyr::full_join(dfx_day,
                                  dfx_temps_day,
                                  by = "Data"
      )
      dfx_day <- dplyr::full_join(dfx_day,
                                  dfx_prec_day,
                                  by = "Data"
      )
      dfx_day <- dplyr::full_join(dfx_day, dfx_press_mean_day,
                                  by = "Data"
      )
      dfx_day <- dplyr::full_join(dfx_day, dfx_urs_day,
                                  by = "Data"
      )
      dfx_day <- dplyr::full_join(dfx_day, dfx_vvs_day,
                                  by = "Data"
      )
      dfx_day <- dplyr::full_join(dfx_day, dfx_RG_sum_day,
                                  by = "Data"
      )
      dfx_day <- dplyr::mutate(dfx_day, OMM = OMM)
      df <- rbind(df, dfx_day)
    }

    df <- filter(df, Data >= start_date & Data <= end_date)
    df <- df %>% mutate(
      Station = Station,
      UF = UF,
      longitude = longitude,
      latitude = latitude,
      altitude = altitude
    )
    colnames(df) <- c(
      "Date", "Tair_mean (c)", "Tair_min (c)",
      "Tair_max (c)", "Dew_tmean (c)", "Dew_tmin (c)",
      "Dew_tmax (c)", "Dry_bulb_t (c)", "Rainfall (mm)",
      "Patm (mB)", "Rh_mean (porc)", "Rh_max (porc)", "Rh_min (porc)",
      "Ws_10 (m s-1)", "Ws_gust (m s-1)",
      "Wd (degrees)", "Sr (Mj m-2 day-1)", "DOY", "Ra (Mj m-2 day-1)",
      "Station_code","Station", "UF" ,"Longitude (degrees)", "Latitude (degrees)",
      "Altitude (m)"
    )
    df_combined <- bind_rows(df_combined,df)
  }
  return(df_combined)
}

# loop para todas as estações
stations <- see_stations_info()
df <- data.frame()
for (year in 2000:2022) {
  start <- Sys.time()
  df.new <- download_AWS_INMET_daily_adapted(stations = stations$OMM, start_date = paste0(year,"-01-01"), end_date = paste0(year,"-12-31"))
  df <- bind_rows(df,df.new)
  end <- Sys.time()
  cat("\n",end-start)
}