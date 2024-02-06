import warnings
import time
import os
import glob

import numpy as np


def rfft(t, x, window=None):
    """Calculates FFT from real time series data.
    
    The result is normalized such that the FFT provides the true amplitude of each frequency.
    
    The data array (x) is expected to have time steps along the first axis. Multiple data sets
    can be processed simultaneously by stacking along additional axes.
    
    Parameters
    ----------
    t : np.ndarray
        Time step data (1d)
    x : np.ndarray
        Time series data (nd)
    window : string (optional)
        Name of window function

    Returns
    -------
    tuple
        A tuple of ndarrays of the form (frequency, FFT)
    """
    
    windows = {'hann': np.hanning}
    
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    elif t.size != x.shape[-1]:
        raise ValueError(f'Last dimension of x ({x.shape[-1]}) must match size of t ({t.size}).')
        
    elif np.any(np.iscomplexobj(x)):
        warnings.warn(f'Array x has complex dtype {x.dtype}; imaginary components will be discarded, which may affect results.')
        
    if window is not None and window not in windows.keys():
        warnings.warn(f'Provided invalid window type "{window}"; window will default to rectangular.')
    
    # Compute FFT and frequency array
    if window in windows.keys():
        window_func = windows[window]
        # TODO: allow user to specify arbitrary axis axis for time steps
        window_array = window_func(x.shape[0])
        x = np.swapaxes(np.swapaxes(x, -1, 0) * window_array, -1, 0)
    
    f = np.fft.rfftfreq(t.size) / (t[1] - t[0])
    x_fft = np.fft.rfft(x, norm='forward', axis=-1) * 2
    
    return f, x_fft


def trim_to_time(t, x, cutoff):
    """Trims time domain data to a specified cutoff time.
    
    Can be used on a single 
    
    Parameters
    ----------
    t : np.ndarray
        Time step data (1d)
    x : np.ndarray
        Time series data (nd)
    cutoff : float
        Cutoff time in seconds

    Returns
    -------
    tuple : ndarray, ndarray
        A tuple of trimmed data the form (t_trim, x_trim)
    """
    
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    elif x.shape[0] != t.size:
        raise ValueError(f'First dimension of x ({x.shape[0]}) must match size of t ({t.size}).')
        
    elif cutoff < 0:
        raise ValueError(f'Cutoff time ({cutoff}) must be greater than or equal to zero.')
        
    # Identify cutoff index and return trimmed data
    index = np.abs(t - cutoff).argmin()
    t_trim = t[:index]
    x_trim = x[:index, ...]
    
    return t_trim, x_trim


def pad_array_to_length(x, size, val=0):
    """Pads an array with entries of "val" along 0th axis to match size.
    
    Parameters
    ----------
    x : np.ndarray
        Array to pad (currently only supports 1D)
    size : int
        Desired size of padded array
    val : float (optional)
        Value to pad with (defaults to zero)

    Returns
    -------
    np.ndarray
        Padded array
    """
    
    # Handle exceptions
    # TODO: support arbitrary padding dimensions
    if x.ndim > 1:
        raise ValueError(f'pad_array_to_length currently only supports 1D arrays ({x.ndim}D array provided).')
    
    # Create padded array
    # TODO: match dtype of val and/or original array    
    padding = val * np.ones(size - x.size)
    x_new = np.concatenate([x, padding])
    
    return x_new


def pad_data_to_time(t, x, endtime, val=0):
    """Wrapper for pad_array_to_length that pads both time steps and data to the desired end time.
    
    Parameters
    ----------
    t : np.ndarray
        time steps
    x : np.ndarray
        data to pad (currently only supports 1D)
    endtime : float
        Desired end time of padded data
    val : float (optional)
        Value to pad with (defaults to zero)

    Returns
    -------
    tuple
        Tuple (t_padded, x_padded) of padded data.
    """
    
    dt = t[1] - t[0]
    t_padded = np.arange(t[0], endtime + dt, dt)
    x_padded = pad_array_to_length(x, t_padded.size, val=val)
    
    return t_padded, x_padded


def resample(t, x, steps):
    # TODO: use scipy.interpolate.interp1d to support non-linear interpolation
    """Resamples time series data using linear interpolation to a specified time step.
    
    Typical use cases relate to frequency domain operations between data sets with different
    time steps, including non-uniform time series produced by magnetostatic scaling.
    
    Parameters
    ----------
    t : np.ndarray
        original time steps
    x : np.ndarray
        data to resample
    step : float | np.ndarray
        Step size or array of sample points
        
    Returns
    -------
    tuple
        Tuple (t_resamp, x_resamp) of the resampled data
    """
    
    if isinstance(steps, (list, tuple, np.ndarray)):
        # Note: isn't there a method for checking ArrayLike?
        # Array of sample points
        t_resamp = steps
    
    else:
        # TODO: handle cases where is not float/int
        dt = steps
        t_resamp = np.arange(t[0], t[-1] + dt, dt)
    
    x_resamp = np.interp(t_resamp, t, x)
    
    return t_resamp, x_resamp