import warnings
import numpy as np

from .signal import rfft


def shielding(t, x, xref, axis=0):
    """Calculates shielding effectiveness from time series data.
    
    Default settings require x to have time along the first axis.
    Multiple data sets can be processed simultaneously by stacking along additional axes.
    
    Parameters
    ----------
    t : np.ndarray
        Timestep array (1d)
    x : np.ndarray
        Measurement time series (nd)
    xref: np.ndarray
        Reference time series (1d)
    axis : int (optional)
        Time axis along which to calculate shielding

    Returns
    -------
    tuple : ndarray, ndarray
        A tuple of the form (frequency, shielding)
    """
    
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    elif x.shape[axis] != t.size:
        raise ValueError(f'x dimension {axis} ({x.shape[axis]}) must match size of t ({t.size}).')
        
    elif x.shape[axis] != xref.size:
        raise ValueError(f'x dimension {axis} ({x.shape[axis]}) must match size of xref ({xref.size}).')
        
    elif np.any(np.iscomplex(x)):
        warnings.warn(f'Array x has complex dtype {x.dtype}; imaginary components will be disregarded, which may affect results.')
    
    # Compute FFTs
    f, x_fft = rfft(t, x, axis)
    _, xref_fft = rfft(t, xref)

    # Compute shielding in dB
    # TODO: decide on alternative to swapaxes
    se = 20 * np.log10(np.abs(np.swapaxes(xref_fft / np.swapaxes(x_fft, -1, axis), -1, axis)))
    
    return f, se