import gsw
from .calculateStructure import thermocline,halocline, picnocline

def Structures(df, lat, lon):
    try:
        df['SA'] = gsw.SA_from_SP(df['SP'].values, df['pres'].values, lon, lat)
        df['CT'] = gsw.CT_from_t(df['SA'].values, df['t'].values, df['pres'].values)
        df['sigma0'] = gsw.sigma0(df['SA'], df['CT'])

        df = df.rename(columns={'SA': 'asal', 'CT': 'ctemp'})

        pres_mtd, temp_mtd, pres_mld, temp_mld, r2, _, _, _ = thermocline(df)
        start_halocline, end_halocline, _ = halocline(df)
        start_picnocline, end_picnocline, _ = picnocline(df)

        return {
            
            "thermocline": {
                "pres_mtd": pres_mtd,
                "temp_mtd": temp_mtd,
                "pres_mld": pres_mld,
                "temp_mld": temp_mld,
                "r2": r2
            },
            "halocline": {
                "start": start_halocline,
                "end": end_halocline
            },
            "picnocline": {
                "start": start_picnocline,
                "end": end_picnocline
            }
        }

    except Exception as e:
        print(f"Error en cálculo oceanográfico: {e}")
        return None