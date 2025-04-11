
import numpy as np
import pwlf
from scipy.signal import savgol_filter
from sklearn.metrics import r2_score
from scipy.optimize import curve_fit

def halocline(df, n_segmentos=5):
    """
    Detecta la haloclina mediante ajuste por tramos lineales.
    Retorna los puntos de ruptura (inicio y fin) y el modelo ajustado.
    """
    profundidad = df['pres'].values
    salinidad = df['asal'].values  # Asume que ya es SA

    # Suavizado interno opcional
    salinidad_smooth = savgol_filter(salinidad, window_length=11, polyorder=2)

    modelo = pwlf.PiecewiseLinFit(profundidad, salinidad_smooth)
    breakpoints = modelo.fit(n_segmentos)

    if len(breakpoints) >= 3:
        start_halocline = breakpoints[1]
        final_halocline = breakpoints[2]
        return start_halocline, final_halocline, modelo
    else:
        raise ValueError("No se pudo identificar la haloclina.")