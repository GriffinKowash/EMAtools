import warnings
import os
import glob
import time

import numpy as np

from .file import File


class Emin(File):
    """Class to handle editing of emin simulation files."""
    
    def __init__(self, path):
        """Initializes Emin object from path and filename."""
        
        File.__init__(self, path, ext='.emin')


    def modify_isotropic_material(self, name, sig=None, eps=None, mu=None, sigm=None, eps_rel=None, mu_rel=None):
        """Modifies properties of an isotropic material to the provided values.

        Parameters
        ----------
        name : str
            Name of material as listed in emin file
        sig : float (optional)
            Electric conductivity
        eps : float (optional)
            Permittivity
        mu : float (optional)
            Permeability
        sigm : float (optiona)
            Magnetic conductivity
        eps_rel : float (optional)
            Relative permittivity (overrides eps)
        mu_rel : float (optional)
            Relative permeability (overrides mu)

        Returns
        -------
        None
        """
        
        # Handle warnings
        if eps is not None and eps_rel is not None:
            warnings.warn('Permittivity was specified as both absolute and relative; absolute value will be discarded.')
        
        if mu is not None and eps_rel is not None:
            warnings.warn('Permeability was specified as both absolute and relative; absolute value will be discarded.')
            
        # Convert relative values to absolute
        if eps_rel is not None:
            eps = eps_rel * 8.85418782e-12
        
        if mu_rel is not None:
            mu = mu_rel * 1.25663706e-6
            
        # Modify emin lines
        text = None
        
        for index in self.find_all(f'* MATERIAL : {name}'):
            i = index + 4 #assumes properties are four lines below name
            
            if text is None:
                sig0, eps0, mu0, sigm0 = np.array(self.get(i).split()).astype(np.float64)
                
                if sig is not None:
                    sig0 = sig
                if eps is not None:
                    eps0 = eps
                if mu is not None:
                    mu0 = mu
                if sigm is not None:
                    sigm0 = sigm
                    
                strings = ['%.10E' % val for val in [sig0, eps0, mu0, sigm0]]
                text = '    '.join(strings)       
            
            self.replace(i, text)
            

    def restrict_surface_current(self, direction):
        """Restricts surface current definition in emin file to a single direction.
        
        As of 2024R1, the direction of a surface current cannot be specified in the GUI.
        For example, a current source applied to a z-normal surface will have
        currents in both the x and y directions. This function can modify such a
        current source to be directed only in the x or y direction.
        
        Parameters
        ----------
        direction : int | str
            Desired current direction (0|'x', 1|'y', 2|'z')

        Returns
        -------
        None
        """
        
        # Map between direction string and column index
        if direction in [0, 1, 2]:
            direction = {0: 'x', 1: 'y', 2: 'z'}[direction]

        column_dict = {'x': 3, 'y': 4, 'z': 5}
        
        # Handle exceptions and warnings
        if direction not in column_dict:
            raise ValueError(f'Direction must be "x"/0, "y"/1, or "z"/2 (provided "{direction}")')
            
        # identify start and end of current source definition
        i0 = self.find('!CURRENT DENSITY SOURCE') + 4 #assumes 4-line offset to start of point list
        i1 = self.find_next(i0, '', exact=True) - 1 #end before next blank line

        # Only retain lines with non-zero values in the desired column
        column = column_dict[direction]

        lines_filtered = [line for line in self.lines[i0:i1] if float(line.split()[column]) != 0]

        if len(lines_filtered) == 0:
            warnings.warn(f'No {direction}-directed source elements found; probe definition not changed.')

        else:
            self.replace((i0, i1), lines_filtered)


    @staticmethod
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
        if path.split('.')[-1] == 'emin':
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