import gsw
import numpy as np
import pwlf
from scipy.signal import savgol_filter
from sklearn.metrics import r2_score
from scipy.optimize import curve_fit


def fsigmoid(x, a, b):
    return 1.0 / (1.0 + np.exp(-a*(x-b)))

########################
# Normalization
########################
def norm(y, y_min, y_max):
	return (y - y_min)/(y_max-y_min)

########################
# Denormalization
########################
def unnorm(y, y_min, y_max):
	return y*(y_max-y_min)+y_min

########################
# NsquaredT
########################
def NsquaredT(SA, CT, p, lat=None, axis=0):
	# Modified from gsw Nsquared function to get NsquaredT 
	# (release https://github.com/TEOS-10/GSW-Python/releases/tag/v3.6.16.post1)
	if lat is not None:
		if np.any((lat < -90) | (lat > 90)):
			raise ValueError('lat is out of range')
		SA, CT, p, lat = np.broadcast_arrays(SA, CT, p, lat)
		g = grav(lat, p)
	else:
		SA, CT, p = np.broadcast_arrays(SA, CT, p)
		g = 9.7963
	
	def axis_slicer(n, sl, axis):
		itup = [slice(None)] * n
		itup[axis] = sl
		return tuple(itup)
	
	db_to_pa = 1e4
	shallow = axis_slicer(SA.ndim, slice(-1), axis)
	deep = axis_slicer(SA.ndim, slice(1, None), axis)
	if lat is not None:
		g_local = 0.5 * (g[shallow] + g[deep])
	else:
		g_local = g
	
	dSA = SA[deep] - SA[shallow]
	dCT = CT[deep] - CT[shallow]
	dp = p[deep] - p[shallow]
	SA_mid = 0.5 * (SA[shallow] + SA[deep])
	CT_mid = 0.5 * (CT[shallow] + CT[deep])
	p_mid = 0.5 * (p[shallow] + p[deep])
	
	specvol_mid, alpha_mid, beta_mid = gsw.specvol_alpha_beta(SA_mid, CT_mid, p_mid)
	
	N2T = ((g_local**2) / (specvol_mid * db_to_pa * dp))
	N2T = N2T * alpha_mid*dCT
	
	return N2T, p_mid
	
########################
# Calculate thermocline
########################
def thermocline(df, m_precision=0.01, threshold=0.2):
	########################
	# parameters:
	# 	df: Dataset, columns=['pres','asal','ctemp']
	# 	m_precision: Accuracy in meters
	#	threshold: Threshold for determining MLD and MTD
	########################
	x_true = df.pres.to_numpy()
	y_true = df.ctemp.to_numpy()

	########################
	# Calculates the buoyancy frequency squared (N2)
	########################
	N2T, p_mid = NsquaredT(df.asal, df.ctemp, df.pres)
	N2T = np.vstack((N2T, p_mid)).T

	########################
	# Obtain the pressure range where N2T is greater
	########################
	try:
		index = np.argmax(np.abs(N2T[:,0]))
	except:
		return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

	max_pres = p_mid[index]*2
	index = x_true < max_pres
	x_true = x_true[index] 
	y_true = y_true[index]
	N2T = N2T[index[:-1]]

	########################
	# Normalize data
	########################
	sign = 1
	if (np.mean(y_true[:2]) > np.mean(y_true[-2:])):
		y_true = -y_true # It is inverted to resemble the function
		sign = -1

	y_min = np.min(y_true) # Min before normalizing
	y_max = np.max(y_true) # Max before normalizing
	y_true = norm(y_true, y_min, y_max) # Normalization

	bounds = ([np.min(y_true), np.min(x_true)], # Lower and upper limits of the parameters
			  [np.max(y_true), np.max(x_true)])

	########################
	# Fit data to sigmoid
	########################
	try:
		popt, pcov = curve_fit(fsigmoid, x_true, y_true, method='dogbox', bounds=bounds)
	except:
		return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

	x_pred = np.linspace(np.min(x_true), np.max(x_true), int(np.max(x_true)-np.min(x_true)))
	y_pred = fsigmoid(x_pred, *popt)

	########################
	# Calculate coefficient of determination (R2)
	########################	
	r2 = r2_score(y_true, fsigmoid(x_true, *popt))

	########################
	# Denormalization data
	########################
	y_true = unnorm(y_true, y_min, y_max) # Denormalize real data
	y_pred = unnorm(y_pred, y_min, y_max) # Denormalize predicted data

	########################
	#  Calculate MLD
	######################### 
	pres_10m = 10
	temp_10m = unnorm(fsigmoid(pres_10m, *popt), y_min, y_max)

	pres_mld = np.nan
	temp_mld = np.nan
	for k in np.arange(pres_10m + m_precision, x_true[-1], m_precision): # check every cm
		temp_mld = unnorm(fsigmoid(k, *popt), y_min, y_max)
		if (temp_mld - temp_10m) >= threshold:
			pres_mld = k
			break

	########################
	#  Calculate MTD
	######################### 
	pres_deep = x_true[-1]
	temp_deep = unnorm(fsigmoid(pres_deep, *popt), y_min, y_max)
	
	pres_mtd = np.nan
	temp_mtd = np.nan
	if ~np.isnan(pres_mld):
		for k in np.arange(pres_deep + m_precision, pres_mld, -m_precision): # check every cm
			temp_mtd = unnorm(fsigmoid(k, *popt), y_min, y_max)
			if (temp_deep - temp_mtd) >= threshold:
				pres_mtd = k
				break

	if pres_mld > pres_mtd:
		return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

	return pres_mtd, temp_mtd*sign, pres_mld, temp_mld*sign, r2, N2T, x_pred, y_pred*sign


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