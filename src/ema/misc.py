import warnings
import time
import os
import glob

import numpy as np


def shielding(t, x, xref):
    """Calculates shielding effectiveness from time series data.
    
    The result is normalized such that the FFT provides the true amplitude of each frequency.
    
    The data array (x) is expected to have time steps along the first axis. Multiple data sets
    can be processed simultaneously by stacking along additional axes.
    
    Parameters
    ----------
    t : np.ndarray
        Time step data (1d)
    x : np.ndarray
        Time series data (nd)
    xref: np.ndarray
        Time series data for reference waveform (nd)

    Returns
    -------
    tuple : ndarray, ndarray
        A tuple of the form (frequency, shielding)
    """
    
    # Handle errors and warnings
    if t.ndim > 1:
        raise ValueError(f'Array t must have exactly one dimension; {t.ndim} provided.')
        
    elif x.shape[-1] != t.size:
        raise ValueError(f'Last dimension of x ({x.shape[-1]}) must match size of t ({t.size}).')
        
    elif np.any(xref.shape != x.shape):
        raise ValueError(f'Shape of xref ({xref.shape}) must match x ({x.shape}).')
        
    elif np.any(np.iscomplex(x)):
        warnings.warn(f'Array x has complex dtype {x.dtype}; imaginary components will be disregarded, which may affect results.')
    
    # Compute FFTs and frequency array
    f = np.fft.rfftfreq(t.size) / (t[1] - t[0])
    x_fft = np.fft.rfft(x, norm='forward', axis=0) * 2
    xref_fft = np.fft.rfft(xref, norm='forward', axis=0) * 2
    
    # Compute shielding (dB)
    se = 20 * np.log10(np.abs(xref_fft / x_fft))
    
    return f, se


def restrict_surface_current(path, direction, overwrite=True):
    """Restricts surface current definition in emin file to a single direction.
    
    As of 2024R1, the direction of a surface current cannot be specified in the GUI.
    For example, a current source applied to a z-normal surface will have
    currents in both the x and y directions. This function can modify such a
    current source to be directed only in the x or y direction.
    
    Parameters
    ----------
    path : str
        Path to emin file or directory containing emin file
    direction : int | str
        Desired current direction (0|'x', 1|'y', 2|'z')
    overwrite : bool (option)
        Whether to overwrite emin or save timestamped copy

    Returns
    -------
    None
    """
    
    # Map between direction string and column index
    column_dict = {'x': 3, 'y': 4, 'z': 5}
    
    # Handle exceptions and warnings
    if direction not in column_dict:
        raise ValueError(f'Direction must be "x", "y", or "z" (provided "{direction}")')
        
    # open emin file
    emin_path_and_name = find_emin(path)
    with open(emin_path_and_name, 'r') as emin:
        lines = emin.readlines()

    # identify start and end of current source definition
    i0, i1 = 0, 0

    for i, line in enumerate(lines):
        # TODO: evaluate flexibility of this approach
        if 'SourceCurrent.dat' in line:
            i0 = i + 1

        elif 'PROBES' in line:
            i1 = i - 2
            break

    # Only retain lines with non-zero values in the desired column
    column = column_dict[direction]
    probe = [line for line in lines[i0:i1] if float(line.split()[column]) != 0]
    new_lines = lines[:i0] + probe + lines[i1:]
    
    if len(probe) == 0:
        warnings.warn(f'No {direction}-directed source elements found; probe definition deleted.')

    # Save emin
    if overwrite:
        save_path_and_name = emin_path_and_name
    else:
        save_path_and_name = emin_path_and_name[:-5] + '_' + str(time.time()) + '.emin'
    
    with open(save_path_and_name, 'w') as emin:
        emin.writelines(new_lines)

    print(f'Saved modified emin file to {save_path_and_name}')
        
    
def find_emin(path):
    """Helper function to identify an emin file within a directory.
    
    The "path" argument can also point directly to the emin file rather
    than the containing directory to improve flexibility for users.
    
    Parameters
    ----------
    path : str
        Path to emin file or directory containing emin file

    Returns
    -------
    str | None
        Full path and name to emin file, or None if absent.
    """
    
    # check for existence of file/directory
    if not os.path.exists(path):
        raise Exception(f'Path specified by user does not exist. ({path})')
    
    # determine emin path and name from "path" argument
    if path[-4:] == 'emin':
        path_and_name = path
    
    else:
        emins = glob.glob('\\'.join([path, '*.emin']))
        
        if len(emins) > 0:
            path_and_name = emins[0]
            if len(emins) > 1:
                warnings.warn(f'Multiple emin files found in directory; selecting {path_and_name}.')
                
        else:
            raise Exception(f'No emin file found in specified directory ({path})')
            
    return path_and_name

