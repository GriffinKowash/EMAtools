import warnings
import time
import os
import glob

import numpy as np
import scipy


windows = {'hann': np.hanning,
           'hamming': np.hamming,
           'bartlett': np.bartlett,
           'blackman': np.blackman,
           'kaiser': np.kaiser}


def rfft(t, x, axis=-1, window=None):
    """Calculates FFT from real time series data.
    
    The result is normalized such that the FFT provides the true amplitude of each frequency.
    
    The data array x is expected to have time steps along the last axis. Multiple data sets
    can be processed simultaneously by stacking along additional axes.
    
    Parameters
    ----------
    t : np.ndarray
        Time step data (1d)
    x : np.ndarray
        Time series data (nd)
    axis : int (optional)
        Axis along which to take FFT
    window : string (optional)
        Name of window function

    Returns
    -------
    tuple
        A tuple of ndarrays of the form (frequency, FFT)
    """
    
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    elif t.size != x.shape[axis]:
        raise ValueError(f'Dimension of x axis {axis} ({x.shape[axis]}) must match size of t ({t.size}).')
        
    elif np.any(np.iscomplexobj(x)):
        warnings.warn(f'Array x has complex dtype {x.dtype}; imaginary components will be discarded, which may affect results.')

    # Apply window function
    if window is not None:
        if window.lower() in windows:
            window_func = windows[window.lower()]
            window_array = window_func(x.shape[axis], beta=14) if window.lower() == 'kaiser' else window_func(x.shape[axis])
            x = np.swapaxes(np.swapaxes(x, -1, axis) * window_array, -1, axis)

        else:
            warnings.warn(f'Provided invalid window type "{window}"; window will default to rectangular.')
        
    # Compute FFT and frequency array
    # TODO: warning for non-uniform timesteps
    f = np.fft.rfftfreq(t.size) / (t[1] - t[0])
    x_fft = np.fft.rfft(x, norm='forward', axis=axis) * 2
        
    return f, x_fft


def trim_to_time(t, x, t0, t1=None):
    # TODO: accept either single arg (end time) or two args (start/end slice)
    """Trims time domain data to a specified cutoff time.

    Array x may have arbitrary dimensions as long as the last axis corresponds to time.
    
    Parameters
    ----------
    t : np.ndarray
        Time step data (1d)
    x : np.ndarray
        Time series data (nd)
    t0 : float
        End time if t1 is not specified; otherwise start time
    t1 : float (optional)
        End time.

    Returns
    -------
    tuple : ndarray, ndarray
        A tuple of trimmed data the form (t_trim, x_trim)
    """
    
    # Determine start and end time from t0/t1 arguments
    if t1 is None:
        start = 0
        end = t0
        
    else:
        start = t0
        end = t1
        
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    elif x.shape[-1] != t.size:
        raise ValueError(f'last dimension of x ({x.shape[-1]}) must match size of t ({t.size}).')
        
    elif end < 0:
        raise ValueError(f'Start and end times ({start}, {end}) must be greater than or equal to zero.')
        
    elif start > end:
        raise ValueError(f'Start time ({start}) must be less than end time ({end}).')
        
    # Identify cutoff index and return trimmed data   
    i_start = np.abs(t - start).argmin()
    i_end = np.abs(t - end).argmin()
    t_trim = t[i_start:i_end]
    x_trim = x[..., i_start:i_end]
    
    return t_trim, x_trim


def pad(x, size, val=0):
    """Pads an nd array x with entries of "val" along last axis to match size.
    
    Parameters
    ----------
    x : np.ndarray
        Array to pad (nd)
    size : int
        Desired size of padded array
    val : float (optional)
        Value to pad with (default zero)

    Returns
    -------
    np.ndarray
        Padded array
    """

    # Handle exceptions
    if size <= x.shape[-1]:
        warnings.warn(f'Argument "size" ({size}) must be greater than x.shape[-1] ({x.shape[-1]}); returning original array.')
        return x

    # Create padded array
    pad_shape = list(x.shape)
    pad_shape[-1] = size - x.shape[-1]
    padding = val * np.ones(pad_shape)
    x_new = np.concatenate([x, padding], axis=-1)
    
    return x_new


def pad_to_time(t, x, endtime, val=0):
    """Pads time steps and measurements to a given end time; wrapper for signal.pad.

    Array x may have arbitrary dimensions as long as the last axis corresponds to time.
    
    Parameters
    ----------
    t : np.ndarray
        time steps (1d)
    x : np.ndarray
        data to pad (nd)
    endtime : float
        Desired end time
    val : float (optional)
        Value to pad with (default zero)

    Returns
    -------
    tuple
        Tuple (t_padded, x_padded) of padded data.
    """
    
    dt = t[1] - t[0]
    t_padded = np.arange(t[0], endtime + dt, dt)
    x_padded = pad(x, t_padded.size, val=val)
    
    return t_padded, x_padded


def resample(t, x, steps, mode='linear'):
    """Resamples time series data using linear interpolation to a specified time step.

    If x has two or more dimensions, resampling will be applied along the last axis.
    
    Typical use cases relate to frequency domain operations between data sets with different
    time steps, including non-uniform time series produced by magnetostatic scaling.
    
    Parameters
    ----------
    t : np.ndarray
        original time steps (1d)
    x : np.ndarray
        data to resample (nd)
    steps : float | np.ndarray
        Desired time step, or custom array of sample times
    mode : str (optional)
        Interpolation mode (linear or spline)
        
    Returns
    -------
    tuple
        Tuple (t_resamp, x_resamp) of the resampled data
    """
    
    # Discriminate constant timestep from array of timesteps
    if np.iterable(steps):
        t_resamp = steps
    
    else:
        dt = steps
        t_resamp = np.arange(t[0], t[-1] + dt, dt)
    
    # Resample each array in x
    x_flat = x.reshape(-1, x.shape[-1])
    x_resamp = []

    for array in x_flat:
        if mode == 'linear':
            x_resamp.append(np.interp(t_resamp, t, array))
        
        elif mode == 'spline':
            bspline = scipy.interpolate.make_interp_spline(t, array, k=3)
            x_resamp.append(bspline(t_resamp))

    # Shape resampled data to match original dimensions
    new_shape = list(x.shape)
    new_shape[-1] = t_resamp.size
    x_resamp = np.reshape(x_resamp, new_shape)

    return t_resamp, x_resamp


### Aliases ###
pad_data_to_time = pad_to_time
pad_array_to_length = pad