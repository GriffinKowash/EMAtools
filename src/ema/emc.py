import warnings
import os
import numpy as np

from .signal import rfft
from .results import load_probe


def shielding(xf, xf_ref, axis=-1):
    """Calculates shielding effectiveness in decibels from frequency domain data.
    
    Default settings require x to have time along the first axis.
    Multiple data sets can be processed simultaneously by stacking along additional axes.
    
    Parameters
    ----------
    xf : np.ndarray
        Measurement data in frequency domain (nd)
    xf_ref : np.ndarray
        Reference data in frequency domain (1d)
    axis : int (optional)
        Axis along which to calculate shielding

    Returns
    -------
    np.ndarray
        Array of shielding values (shape of xf)
    """

    # Handle errors and warnings
    if xf_ref.ndim > 1:
        raise ValueError(f'Array xf_ref must have exactly one dimension; {xf_ref.ndim} provided.')

    elif xf.shape[axis] != xf_ref.size:
        raise ValueError(f'xf dimension {axis} ({xf.shape[axis]}) must match size of xref ({xf_ref.size}).')
        
    # Compute shielding in dB
    se = 20 * np.log10(np.abs(np.swapaxes(xf_ref / np.swapaxes(xf, -1, axis), -1, axis)))
    
    return se


def shielding_from_timeseries(t, x, x_ref):
    """Calculates shielding effectiveness from X/Y/Z field probe data.
    
    Array x is expected to have dimensions [..., component, time], with ...
    indicating that multiple data sets can be stacked along additional dimensions.

    Array xref may be either a 1D array of field amplitudes or a 2D array of field
    probe data with shape [component, time].
    
    Parameters
    ----------
    t : np.ndarray
        Timestep array (1d)
    x : np.ndarray
        Measurement time series (nd)
    x_ref: np.ndarray
        Reference time series (1d/2d)

    Returns
    -------
    tuple : ndarray, ndarray
        A tuple of the form (frequency, shielding)
    """
    
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    if x.shape[-1] != t.size:
        raise ValueError(f'x dimension -1 ({x.shape[-1]}) must match size of t ({t.size}).')

    if x.shape[-1] != x_ref.shape[-1]:
        raise ValueError(f'x dimension -1 ({x.shape[-1]}) must dimension -1 of xref ({x_ref.shape[-1]}).')

    if x_ref.ndim > 2:
        raise ValueError(f'x_ref cannot have more than two dimensions; {x_ref.ndim} provided.')

    if np.any(np.iscomplex(x)):
        warnings.warn(f'Array x has complex dtype {x.dtype}; imaginary components will be disregarded, which may affect results.')
    
    # Compute FFTs
    f, x_fft = rfft(t, x)
    _, x_ref_fft = rfft(t, x_ref)

    # Compute vector magnitudes
    x_fft = np.sqrt(np.sum(x_fft ** 2, axis=-2))
    if x_ref.ndim == 2:
        x_ref_fft = np.sqrt(np.sum(x_ref_fft ** 2, axis=-2))
    
    # Compute shielding in dB
    se = shielding(x_fft, x_ref_fft)

    return f, se


def shielding_from_file(path, refpath):
    """Calculates shielding effectiveness from field probe result files.

    Parameters
    ----------
    path : str | list
        Path to measurement file, or list of paths
    refpath : str
        Path to reference file

    Returns
    -------
    tuple : ndarray, ndarray
        A tuple of the form (frequency, shielding)
    """

    # Handle exceptions
    if isinstance(path, str):
        if not os.path.exists(path):
            raise FileNotFoundError(f'File at {path} does not exist.')

    else:
        for p in path:
            if not os.path.exists(p):
                raise FileNotFoundError(f'File at {p} does not exist.')

    if not os.path.exists(refpath):
        raise FileNotFoundError(f'File at {refpath} does not exist.')

    # Load data assuming probe format
    if isinstance(path, str):
        t, x = load_probe(path)

    else:
        x = []
        for p in path:
            t, xn = load_probe(p)
            x.append(xn)
        x = np.array(x)

    t_ref, x_ref = load_probe(refpath)

    # Calculate shielding
    f, se = shielding_from_timeseries(t, x, x_ref)

    return f, se