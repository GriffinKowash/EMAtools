import warnings
import os
import glob

import numpy as np

from .file import File


class Inp(File):
    """Class to handle editing of .inp simulation files."""
    
    def __init__(self, path):
        """Initializes Inp object from path and filename."""
        
        File.__init__(self, path)