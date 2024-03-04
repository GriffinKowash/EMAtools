import warnings
import time
import os
import glob

import numpy as np


def load_data(path_and_name, precision='single'):
    """Loads a generic data file with a consistent number of entries per row.

    Parameters
    ----------
    path_and_name : str
        Path to data file with extension
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    np.ndarray
        A 2D array of the file contents with the columns along the first axis.
    """

    # Handle exceptions
    if not os.path.exists(path_and_name):
        raise FileNotFoundError(f'File {path_and_name} does not exist.')

    # Attempt to load data file
    try:
        data = np.loadtxt(path_and_name)

    except ValueError as e:
        # ValueError occurs when number of columns in inconsistent (e.g. for box probe results)
        print(e)
        print('Inconsistent column numbers; verify that the data file being loaded was not produced by a box, distributed, or animation probe.')

    except Exception as e:
        print(e)

    # Return data shaped with entries along the last axis
    return data.T


def load_probe(path_and_name, precision='single'):
    """Loads a point probe file assuming that time steps are listed in the first column.

    Parameters
    ----------
    path_and_name : str
        Path to data file with extension
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    tuple
        A tuple of the form (timesteps, data), where data contains all but the first column.
    """

    # Load data file
    columns = load_data(path_and_name, precision)

    # Separate timesteps and data
    t = columns[0]
    data = columns[1:]

    # Return tuple of timesteps and data
    return t, data


def load_distributed_probe(path_and_name, precision='single'):
    """Converts distributed and box probe results into a numpy array.
    
    For readability, each time step of a distributed probe is split into
    multiple output lines with nine entries in each, with measured values
    for each point listed in order x, y, z. Since values must be written
    out in multiples of three, and the initial time step value introduces
    a one-entry offset, there will always be a line with fewer than nine
    entries at the end of each time step, allowing the file to be parsed.
    
    The dimensions of the returned data are [sample, component, time],
    where "sample" refers to the individual probe points and "component"
    refers to the x/y/z field components.
    
    Parameters
    ----------
    path_and_name : str | list
        Path to probe file with .dat suffix, or list of paths
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    tuple : np.ndarray, np.ndarray
        A tuple of time steps and probe measurements in the form (t, data)
    """
    
    # Handle exceptions
    if not os.path.exists(path_and_name):
        raise Exception(f'File path specified by user does not exist. ({path_and_name})')
    
    # Process probe data
    with open(path_and_name, 'r') as file:
        lines = file.readlines()

    time, data, buffer = [], [], []
    # TODO: automate precision check   
    dtype = np.float32 if precision == 'single' else np.float64
    #total_lines = len(lines)
    
    for i, line in enumerate(lines):
        #if i % (int(total_lines / 100)) == 0:
        #    print(f'{round(i / total_lines * 100)}% complete.')
        
        line_split = line.split()
        
        # Error for non-float values in file
        try:
            values = [dtype(val) for val in line_split]
        except:
            raise ValueError(f'Entry in line {i} cannot be cast to {dtype}: "{line_split}"')

        # If new timestep, add to time array
        if len(buffer) == 0:
            time.append(values[0])
            buffer += values[1:]
        else:
            buffer += values

        # If end of timestep, reshape and append to data array; reset buffer
        if len(values) != 9:
            data.append(np.reshape(buffer, (-1, 3)).T)            
            buffer = []

    # Swap axes to have shape [sample, component, time]
    data = np.swapaxes(np.array(data), 0, -1)
    time = np.array(time)

    return time, data


def load_distributed_probes(*args, precision='single'):
    """Loads multiple distributed or box probe results into a numpy array.
    
    Parameters
    ----------
    *args : str | list
        Paths to probe files, entered as args or single list
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    tuple : np.ndarray, np.ndarray
        A tuple of time steps and probe results in the form (t, data)
    """
    # TODO: use type checking to combine with load_distributed_probe

    # Handle paths provided as args vs list
    if isinstance(args[0], list):
        paths = args[0]
    else:
        paths = args

    # Load distributed probe files
    data_sets = []
    for path in paths:
        t, d = load_distributed_probe(path, precision)
        data_sets.append(d)

    # Combine into single array
    data = np.concatenate(data_sets)

    return t, data


def convert_distributed_probe(path_and_name, fname=None, precision='single'):
    """Flattens distributed probe file to have one time step per line.
    
    This makes the data more readable for NumPy and similar tools by
    shaping the file into easily identifiable, evenly shaped time steps.

    Parameters
    ----------
    path_and_name : str
        Path to probe file (with .dat suffix)
    fname : str (optional)
        Name of new formatted probe file (saved to same directory)
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    None
    """
    
    # Obtain flattened array and combine with timesteps
    t, data = load_distributed_probe(path_and_name, precision=precision)
    flattened = np.concatenate(data, axis=0).T
    combined = np.concatenate([t[:,np.newaxis], flattened], axis=1)

    # Save to file    
    if fname == None:
        # TODO: make hardcoded slice more flexible?
        save_path_and_name = path_and_name[:-4] + '_' + str(time.time()) + '.dat'
    else:
        save_path_and_name = '\\'.join(path_and_name.split('\\')[-1] + [fname])
        
    fmt = '%.7E' if precision == 'single' else '%.15E'
    np.savetxt(save_path_and_name, combined, fmt=fmt)

    
### Create aliases for box probes ###
load_box_probe = load_distributed_probe
load_box_probes = load_distributed_probes
convert_box_probe = convert_distributed_probe