from .emc import *
from .signal import *
from .results import *

from .file import File
from .emin import Emin
from .coupled import CoupledSim
from .inp import Inp
from .cin import Cin

from . import testing

### Aliases for backward compatibility ###
import ema.results as probes