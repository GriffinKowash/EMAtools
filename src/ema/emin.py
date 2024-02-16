import warnings
import time
import os
import glob

import numpy as np


class Emin:
    """Class to handle editing of .emin simulation files."""
    
    def __init__(self, path):
        """Initializes Emin object from path and filename."""
        
        if not os.path.exists(path):
            raise ValueError(f'Path {path} does not exist.')
        else:
            self.path = path
            
        with open(self.path, 'r') as file:
            self.lines = file.read().splitlines()
        
        
    def save(self, path=None):
        """Writes modified lines to emin file.

        Parameters
        ----------
        path : str (optional)
            Alternative save path; defaults to overwriting original file.
                        
        Returns
        -------
        None
        """
        
        if path is None:
            path = self.path
            
        with open(path, 'w') as file:
            # TODO: clean up management of newline characters
            file.writelines([line + '\n' for line in self.lines])
            
        
    @staticmethod
    def ltoi(*args):
        """Converts line number (one-based indexing) to index (zero-based indexing).

        Parameters
        ----------
        *args : int | array-like
            One or more line numbers, or array of line numbers.

        Returns
        -------
        int | np.ndarray
            Indices corresponding to line numbers.
        """
        

        # Accept either an iterable in the first position or multiple line numbers
        if np.iterable(args[0]):
            l = np.array(args[0])
            
        else:
            #TODO: verify if length check is necessary. Will len=1 list unpack?
            if len(args) > 1:
                l = np.array(args)
            else:
                l = args[0]
                
        # Handle errors
        if np.any(l < 1):
            raise ValueError('Argument l may not be or contain values less than one; line numbers are one-indexed.')
        
        return l - 1
    
    
    @staticmethod
    def itol(*args):
        """Converts index (zero-based indexing) to line number (one-based indexing).

        Parameters
        ----------
        *args : int | array-like
            One or more indices, or array of indices.

        Returns
        -------
        int | np.ndarray
            Line number(s) corresponding to index/indices.
        """
                
        # Accept either an iterable in the first position or multiple indices
        if np.iterable(args[0]):
            i = np.array(args[0])
            
        else:
            if len(args) > 1:
                i = np.array(args)
            else:
                i = args[0]
        
        return i + 1
        
        
    def find_occurrences(self, text, start=0, exact=False, case=True, n_max=None):
        """Finds indices of all occurrences of a text string in self.lines.

        Parameters
        ----------
        text : str
            Text string for which to search emin file.
        start : int (optional)
            Index at which to begin search; defaults to start of file.
        exact : bool (optional)
            Whether line must exactly match or simply contain text string.
        case : bool (optional)
            Whether to require case matching.
        n_max : int (optional)
            Interrupts search after n_max occurrences have been found.
            
        Returns
        -------
        list
            Indices of text string in self.lines; empty list if not present.
        """
        
        # Make text lowercase if not case sensitive
        if not case:
            text = text.lower()
        
        # Search for occurrences of text up to n_max
        n_found = 0
        indices = []
        
        for i, line in enumerate(self.lines[start:]):
            if not case:
                line = line.lower()
                
            if (exact and text == line) or (not exact and text in line):
                indices.append(start + i)
                n_found += 1
                
                if n_found == n_max:
                    return np.array(indices)
            
        if n_found == 0:
            print(f'Text string "{text}" not found in emin file.')

        return np.array(indices)
        
        
    def find(self, text, n=1, **kwargs):
        """Finds index of nth occurrence of text string in self.lines

        Parameters
        ----------
        text : str
            Text string for which to search emin file.
        n : int (optional)
            Which occurrence of text to select (n=1 for first occurrence)
        exact : bool (optional)
            Whether line must exactly match or simply contain text string.
        case : bool (optional)
            Whether to require case matching.
            
        Returns
        -------
        int | None
            Index of text string in self.lines; None if not present.
        """
        
        indices = self.find_occurrences(text, n_max=n, **kwargs)
        
        if len(indices) > 0:
            return indices[-1]
        else:
            return indices
        

    def find_next(self, i, text, **kwargs):
        """Finds next occurrence of text after index i; wrapper for Emin.find.
        
        Parameters
        ----------
        i : int
            Index at which to begin search.
        text : str
            Text string for which to search emin file.
            
        Returns
        -------
        int | None
            Index of text string in self.lines; None if not present.
        """

        return self.find(text, start=i+1, **kwargs)
    
    
    def insert(self, i, text):
        """Inserts text at position i in self.lines.

        Parameters
        ----------
        i : int | list
            Index/indices at which to insert.
        text : str | list
            Line or list of lines to insert.
            
        Returns
        -------
        None
        """
        
        # Put single index into list
        if not np.iterable(i):
             i = [i]
        
        # make single string into list for convenience
        if isinstance(text, str):
            text = [text]
        
        # Insert lines
        text.reverse()
        i = sorted(i, reverse=True)
        
        for index in i:
            for line in text:
                self.lines.insert(index, line)
        
    
    def insert_after(self, i, text):
        """Inserts text at position i+1 in self.lines; wrapper for Emin.insert.

        Parameters
        ----------
        i : int | list
            Index/indices after which to insert text.
        text : str | list
            String or list of strings to insert.
            
        Returns
        -------
        None
        """
        
        # Increment indices by one and call Emin.insert
        if np.iterable(i):
            i = np.array(i)
        
        self.insert(i + 1, text)

    
    def remove(self, i0, i1=None):
        """Removes line or range of lines from emin text

        Parameters
        ----------
        i : int | tuple
            Index or range of indices to remove.

        Returns
        -------
        None
        """

        # delete single line
        if i1 is None:
            del(self.lines[i0])

        # delete range of lines
        else:
            self.lines = [line for i, line in enumerate(self.lines) if i not in range(i0, i1+1)]
        
        
    def replace(self, i, text):
        """Inserts text at position or range i in self.lines

        Parameters
        ----------
        i : int | tuple
            Index or range of indices to replace.
        text : str | list
            String or list of strings with which to replace.
            
        Returns
        -------
        None
        """
        
        # make single string into list for convenience
        if isinstance(text, str):
            text = [text]
        
        # find start/stop indices
        if isinstance(i, int):
            i0 = i
            i1 = i0 + len(text) - 1

        elif np.iterable(i):
            # TODO: warning for len(i) > 2
            i0, i1 = i
        
        # handle case where self.lines is too short
        if i1 > len(self.lines):
            i1 = len(self.lines)
            #n_pad = i1 - len(self.lines)
            #self.lines.extend([''] * n_pad)
        
        # replace lines with provided text
        self.remove(i0, i1)
        self.insert(i0, text)
        #self.lines[i0:i1] = text
                
                
    def get(self, i0, i1=None):
        """Returns lines defined by slice (endpoint inclusive) or array of indices.

        Parameters
        ----------
        i0 : int | array-like
            First index, or array of indices to return.
        i1 : int
            Last index, if i0 is not an array.

        Returns
        -------
        list
        """
        
        #TODO: fix!
        
        # Handle warnings            
        if np.iterable(i0) and i1 is not None:
            warnings.warn('Argument i0 is iterable; i1 will be ignored.')
        
        # Print lines
        if np.iterable(i0):
            return [self.lines[i] for i in i0]
        
        elif i1 is not None:
            return self.lines[i0:i1+1]
        
        else:
            return self.lines[i0]
        

    def getlines(self, l0, l1=None):
        """Returns requested line numbers; wrapper for Emin.get.

        Parameters
        ----------
        l0 : int | array-like
            First line, or array of lines to return.
        l1 : int
            Last line, if i0 is not an array.

        Returns
        -------
        list
        """
        
        # Handle warnings            
        if np.iterable(l0) and l1 is not None:
            warnings.warn('Argument l0 is iterable; l1 will be ignored.')
        
        # Get lines
        if np.iterable(l0) or l1 is None:
            i0 = Emin.ltoi(l0)
            i1 = None
        
        elif l1 is not None:
            i0, i1 = Emin.ltoi(l0, l1)
        
        return self.get(i0, i1)

    
    def printlines(self, l0, l1=None):
        """
        Prints out lines l0 to l1 (1-based indexing) formatted with line numbers.
        
        Alternatively, if l0 is an iterable object, it will be treated as an array
        of lines to print out. Values passed for l1 will be ignored in this case.

        Parameters
        ----------
        l0 : int | array-like
            First line to print, or array of lines to print.
        l1 : int
            Last line to print.

        Returns
        -------
        None
        """
        
        # Handle warnings
        if not np.iterable(l0):
            if l0 < 1:
                warnings.warn(f'Argument l0 is one-indexed; {l0} provided. Setting l0 to first line.')
                l0 = 1
            
        elif np.iterable(l0) and l1 is not None:
            warnings.warn('Argument l0 is iterable; l1 will be ignored.')
                    
        # Print lines
        lines = self.getlines(l0, l1)

        for i, line in enumerate(lines):
            if np.iterable(l0):
                n = l0[i]
            else:
                n = l0 + i
            
            print(n, '\t|', line)
            
                
    def head(self, n):
        """Wrapper for Emin.printlines; prints first n lines of emin contents.

        Parameters
        ----------
        n : int
            Number of lines to print.

        Returns
        -------
        None
        """
        
        self.printlines(1, n)
        
        
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
        
        for index in self.find_occurrences(f'* MATERIAL : {name}'):
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
        path : str
            Path to emin file or directory containing emin file
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
        i1 = self.find_next(i0, '', exact=True) - 1

        # Only retain lines with non-zero values in the desired column
        column = column_dict[direction]

        lines_filtered = [line for line in self.lines[i0:i1] if float(line.split()[column]) != 0]
        self.replace((i0, i1), lines_filtered)

        if len(lines_filtered) == 0:
            warnings.warn(f'No {direction}-directed source elements found; probe definition deleted.')


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