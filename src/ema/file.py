import warnings
import os
import time

import numpy as np


class File:
    """Parent class for handling .emin, .inp, and .cin files."""
    
    def __init__(self, path):
        """Initializes file object from path and filename."""
        
        if not os.path.exists(path):
            raise FileNotFoundError(f'Path {path} does not exist.')
        else:
            self.path = path
            
        with open(self.path, 'r') as file:
            #self.lines = file.readlines()
            self.lines = file.read().splitlines()
        
        
    def save(self, path=None):
        """Writes modified lines to file.

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
            # TODO: decide on management of newline characters
            #file.writelines(self.lines)
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
        
        
    def find_all(self, text, start=0, exact=False, case=True, n_max=None):
        """Finds indices of all occurrences of a text string in self.lines.

        Parameters
        ----------
        text : str
            Text string for which to search file.
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
                    break
            
        if n_found == 0:
            print(f'Text string "{text}" not found in file.')

        return np.array(indices)
        
        
    def find(self, text, n=1, **kwargs):
        """Finds index of nth occurrence (default first) of text string in self.lines.

        Parameters
        ----------
        text : str
            Text string for which to search file.
        n : int (optional)
            Which occurrence of text to select (n=1 for first occurrence)
        **kwargs : see File.find_all
            
        Returns
        -------
        int | None
            Index of text string in self.lines; None if not present.
        """
        
        indices = self.find_all(text, n_max=n, **kwargs)
        
        if len(indices) > 0:
            return indices[-1]
        else:
            return None
        

    def find_next(self, i, text, **kwargs):
        """Finds next occurrence of text after index i; wrapper for File.find.
        
        Parameters
        ----------
        i : int
            Index at which to begin search.
        text : str
            Text string for which to search file.
        **kwargs : see File.find_all
            
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
        """Inserts text at position i+1 in self.lines; wrapper for File.insert.

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
        
        # Increment indices by one and call File.insert
        if np.iterable(i):
            i = np.array(i)
        
        self.insert(i + 1, text)

    
    def remove(self, i0, i1=None):
        """Removes line index or range of line indices (endpoint inclusive) from file text.

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
            #self.lines = [line for i, line in enumerate(self.lines) if i not in range(i0, i1+1)]
            self.lines = self.lines[:i0] + self.lines[i1+1:]  #10x faster than list comprehension
        
        
    def replace(self, i, text):
        """Inserts text at position or range i in self.lines.

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
        if isinstance(i, (int, np.integer)):
            i0 = i
            i1 = i0 + len(text) - 1

        elif np.iterable(i):
            # TODO: warning for len(i) > 2
            i0, i1 = i

        else:
            print('Unrecognized type for index i:', type(i))
        
        # handle case where self.lines is too short
        if i1 > len(self.lines):
            i1 = len(self.lines)
            #n_pad = i1 - len(self.lines)
            #self.lines.extend([''] * n_pad)
        
        # replace lines with provided text
        
        if i0 == i1:
            self.remove(i0)
        else:
            self.remove(i0, i1)
            
        self.insert(i0, text)
                
                
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
        """Returns requested line numbers; wrapper for File.get.

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
            i0 = File.ltoi(l0)
            i1 = None
        
        elif l1 is not None:
            i0, i1 = File.ltoi(l0, l1)
        
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
            
                
    def head(self, n=10):
        """Wrapper for File.printlines; prints first n lines of file contents.

        Parameters
        ----------
        n : int
            Number of lines to print.

        Returns
        -------
        None
        """
        
        self.printlines(1, n)


    ### Aliases for backward compatibility ###
    find_occurrences = find_all