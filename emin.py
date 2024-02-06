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
            
        file = open(self.path, 'r')
        self.lines = file.readlines()
        file.close()
        
        
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
            
        file = open(path, 'w')
        file.writelines(self.lines)
        file.close()
        
        
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
            #TODO: verify if length check is necessary. Will len=1 list unpack?
            if len(args) > 1:
                i = np.array(args)
            else:
                i = args[0]
        
        return i + 1
        
        
    def find_occurrences(self, text, exact=False, case=True, n_max=None):
        """Finds indices of all occurrences of a text string in self.lines.

        Parameters
        ----------
        text : str
            Text string for which to search emin file.
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
        
        for i, line in enumerate(self.lines):
            if not case:
                line = line.lower()
                
            if (exact and text == line) or (not exact and text in line):
                indices.append(i)
                n_found += 1
                
                if n_found == n_max:
                    return np.array(indices)
            
        #print(f'Text string "{text}" not found in emin file.')
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
    
        temp = """
        # Make text lowercase if not case sensitive
        if not case:
            text = text.lower()
        
        # Search for nth occurrence of text
        n_found = 0
        
        for i, line in enumerate(self.lines):
            if not case:
                line = line.lower()
                
            if (exact and text == line) or (not exact and text in line):
                n_found += 1
                
                if n_found == n:
                    return i
            
        print(f'Text string "{text}" not found in emin file.')
        return None
        """
    
    
    def insert(self, i, text):
        """Inserts text at position i in self.lines.

        Parameters
        ----------
        i : int
            Index at which to insert.
        text : str | list
            String or list of strings to insert.
            
        Returns
        -------
        None
        """
        
        # make single string into list for convenience
        if isinstance(text, str):
            text = [text]
        
        # add lines in reverse order at position i
        text.reverse()
        for line in text:
            self.lines.insert(i, line)
        
    
    def insert_after(self, i, text):
        """Inserts text at position i+1 in self.lines; wrapper for Emin.insert.

        Parameters
        ----------
        i : int
            Index of line prior to inserted line.
        text : str | list
            String or list of strings to insert.
            
        Returns
        -------
        None
        """
        
        self.insert(i + 1, text)
        
        
    def replace(self, i, text):
        """Inserts text at position i in self.lines

        Parameters
        ----------
        i : int
            Index at which to replace.
        text : str | list
            String or list of strings with which to replace.
            
        Returns
        -------
        None
        """
        
        # make single string into list for convenience
        if isinstance(text, str):
            text = [text]
        
        # find stop index and handle case where self.lines is too short
        i_stop = i + len(text)
        
        if i_stop > len(self.lines):
            n_pad = i_stop - len(self.lines)
            self.lines.extend([''] * n_pad)
        
        # replace lines with provided text
        self.lines[i:i+3] = text
                
                
    def get(self, i0, i1=None):
        """Returns lines defined by slice or array of indices.

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
        if not np.iterable(i0):
            return self.lines[i0:i1]
        
        else:
            return [self.lines[i] for i in i0]
        

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
        i0 = Emin.ltoi(l0)
        i1 = l1
        
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
            
            print(n, '\t|', line[:-1])  #trim trailing newline character
            
                
    
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