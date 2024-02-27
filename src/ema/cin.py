import warnings
import os
import glob

import numpy as np

from .file import File


class Cin(File):
    """Class to handle editing of .cin simulation files."""
    
    def __init__(self, path):
        """Initializes Cin object from path and filename."""
        
        File.__init__(self, path)