import warnings
import time
import os
import glob

import numpy as np


def load_distributed_probe(path_and_name, last_index='probe', precision='single'):
    """Converts distributed and box probe results into a numpy array.
    
    For readability, each time step of a distributed probe is split into
    multiple output lines with nine entries in each, with measured values
    for each point listed in order x, y, z. Since values must be written
    out in multiples of three, and the initial time step value introduces
    a one-entry offset, there will always be a line with fewer than nine
    entries at the end of each time step, allowing the file to be parsed.
    
    The dimensions of the returned data depend on the 'last_index' argument:
        'probe':     (time, component, probe)
        'component': (time, probe, component)
         None:       (time, probes * components)
    
    Parameters
    ----------
    path_and_name : str | list
        Path to probe file with .dat suffix, or list of paths
    last_index : str (optional)
        Specifies structure of data array by last index
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    tuple : np.ndarray, np.ndarray
        A tuple of time steps and probe results in the form (t, data)
    """
    
    # Handle exceptions
    if last_index not in ['probe', 'component', None]:
        raise ValueError(f'Argument "last_index" must be one of "probe", "component", or None; "{last_index}" provided.')
        
    if not os.path.exists(path_and_name):
        raise Exception(f'File path specified by user does not exist. ({path_and_name})')
    
    # Process probe data
    with open(path_and_name, 'r') as file:
        lines = file.readlines()

    time, data, timestep = [], [], []

    #total_lines = len(lines)
    
    for i, line in enumerate(lines):
        #if i % (int(total_lines / 100)) == 0:
        #    print(f'{round(i / total_lines * 100)}% complete.')
        
        line_split = line.split()
        
        try:
            dtype = np.float32 if precision == 'single' else np.float64
            values = [dtype(val) for val in line_split]
        except:
            raise ValueError(f'Entry in line {i} cannot be cast to {dtype}: "{line_split}"')

        if len(timestep) == 0:
            time.append(values[0])
            timestep = timestep + values[1:]
        else:
            timestep = timestep + values

        if len(values) != 9:
            if last_index == 'probe':
                x = timestep[::3]
                y = timestep[1::3]
                z = timestep[2::3]
                data.append([x, y, z])
            
            elif last_index == 'component':
                data.append(np.reshape(timestep, (-1, 3)))
                
            elif last_index == None:
                data.append(timestep)
            
            timestep = []

    return np.array(time), np.array(data)


def load_distributed_probes(paths_and_names, last_index='probe', precision='single'):
    # TODO: use type checking to combine with load_distributed_probe
    """Loads multiple distributed or box probe results into a numpy array.
    
    The dimensions of the returned data depend on the 'last_index' argument:
        'probe':     (time, component, probe)
        'component': (time, probe, component)
         None:       (time, probes * components)
    
    Parameters
    ----------
    paths_and_names : array-like
        Paths to probe files (with .dat suffix)
    last_index : str (optional)
        Specifies structure of data array by last index
    precision : str (optional)
        Precision of simulation results ('single' | 'double')

    Returns
    -------
    tuple : np.ndarray, np.ndarray
        A tuple of time steps and probe results in the form (t, data)
    """
    
    data_sets = []

    for path_and_name in paths_and_names:
        t, d = load_distributed_probe(path_and_name, last_index, precision)
        data_sets.append(d)

    if last_index == 'probe':
        data = np.concatenate(data_sets, axis=2)
        
    elif last_index == 'component' or last_index == None:
        data = np.concatenate(data_sets, axis=1)

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
    
    # Obtain flattened array
    t, data = load_distributed_probe(path_and_name, last_index=None, precision=precision)
    array = np.concatenate([t[:,np.newaxis], data], axis=1)
    
    # Save to file    
    if fname == None:
        # TODO: make hardcoded slice more flexible?
        save_path_and_name = path_and_name[:-4] + '_' + str(time.time()) + '.dat'
    else:
        save_path_and_name = '\\'.join(path_and_name.split('\\')[-1] + [fname])
        
    fmt = '%.7E' if precision == 'single' else '%.15E'
    np.savetxt(save_path_and_name, array, fmt=fmt)

    
### Create aliases for box probes ###
load_box_probe = load_distributed_probe
load_box_probes = load_distributed_probes
convert_box_probe = convert_distributed_probe