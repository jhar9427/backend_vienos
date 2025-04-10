from mldmtd import getProfileDataFromArgoNc, thermocline

df = getProfileDataFromArgoNc('.../aoml/4900432/profiles/D4900432_106.nc')
pres_mtd, temp_mtd, pres_mld, temp_mld, r2, N2T, pres_pred, temp_pred = thermocline(df)