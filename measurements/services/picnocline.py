import numpy as np
import pwlf
from scipy.signal import savgol_filter
from sklearn.metrics import r2_score
from scipy.optimize import curve_fit

def picnocline(df, n_segmentos=5):
    """
    Detecta la picnoclina mediante ajuste por tramos lineales.
    Retorna los puntos de ruptura (inicio y fin) y el modelo ajustado.
    """
    profundidad = df['pres'].values
    densidad = df['sigma0'].values

    # Suavizado opcional (si los datos son muy ruidosos, descomenta)
    densidad_smooth = savgol_filter(densidad, window_length=11, polyorder=2)
    # modelo = pwlf.PiecewiseLinFit(profundidad, densidad_smooth)

    modelo = pwlf.PiecewiseLinFit(profundidad, densidad_smooth)
    breakpoints = modelo.fit(n_segmentos)

    if len(breakpoints) >= 3:
        inicio_picnoclina = breakpoints[1]
        final_picnoclina = breakpoints[2]
        return inicio_picnoclina, final_picnoclina, modelo
    else:
        raise ValueError("No se pudo identificar la picnoclina.")