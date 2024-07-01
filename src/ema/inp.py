import warnings
import os
import glob

import numpy as np

from .file import File


# Current/voltage probe format string
_probe_fmt = """
!PROBE
!!TYPE
NAME.dat  
START    END    STEP   
SEGMENT      CONDUCTOR      INDEX  
"""


class Inp(File):
    """Class to handle editing of .inp simulation files."""
    
    def __init__(self, path):
        """Initializes Inp object from path and filename."""
        
        File.__init__(self, path, ext='.inp')

        # Store timestep parameters
        self.timestep, self.n_timesteps, self.endtime = self.get_timesteps()


    def get_timesteps(self):
        """Parses and returns timestep information."""

        i_time = self.find('!TIME STEP')
        compute_type = self.get(i_time + 1)

        if compute_type == '!!NOTCOMPUTE':
            timestep, n_timesteps = [float(val) for val in self.get(i_time + 2).split()]
            endtime = n_timesteps * timestep
            return timestep, n_timesteps, endtime

        elif compute_type == '!!COMPUTE':
            print('"!!COMPUTE" mode for timestep specification is not yet supported.')
            return None


    def probe(self, probe_type, segment, conductor, index, name=None, start=None, end=None, timestep=None):
        """Places a voltage or current probe on a conductor in a segment.

        Parameters
        ----------
        probe_type : str
            Type of probe ("current" | "voltage")
        segment : str
            Name of MHARNESS segment
        conductor : str
            Name of MHARNESS conductor
        index : int
            Mesh index at which to probe
        name : str (optional)
            Name of ouput file; automatically set if None
        start : float (optional)
            Measurement start time
        end : float (optional)
            Measurement end time
        timestep : float (optional)
            Measurement timestep

        Returns
        -------
        None
        """

        # Replace whitespace with underscores
        segment = segment.replace(' ', '_')
        conductor = conductor.replace(' ', '_')

        # Default name if not provided
        if name is None:
            name = '{}_{}_{}_{}'.format(probe_type, conductor, segment, index)

        # Pull start, end, and step from domain settings if not provided
        if start is None:
            start = 0

        if end is None:
            end = self.endtime

        if timestep is None:
            timestep = self.timestep

        # Map between argument and probe type string
        probe_types = {'voltage': 'CABLE VOLTAGE', 'current': 'CABLE CURRENT'}

        # Format probe text
        probe_text = _probe_fmt
        probe_text = probe_text.replace('TYPE', probe_types[probe_type])
        probe_text = probe_text.replace('NAME', name)
        probe_text = probe_text.replace('START', '%.10E' % start)
        probe_text = probe_text.replace('END', '%.10E' % end)
        probe_text = probe_text.replace('STEP', '%.10E' % timestep)
        probe_text = probe_text.replace('SEGMENT', segment)
        probe_text = probe_text.replace('CONDUCTOR', conductor)
        probe_text = probe_text.replace('INDEX', str(index))

        # Insert probe text
        index = self.find('Section 14: OUTPUT / PROBES') + 2
        self.insert(index, probe_text.splitlines())


    def probe_voltage(self, segment, conductor, index, **kwargs):
        """Places a voltage probe on a conductor in a segment.

        Parameters
        ----------
        segment : str
            Name of MHARNESS segment
        conductor : str
            Name of MHARNESS conductor
        index : int
            Mesh index at which to probe
        **kwargs : see Inp.probe

        Returns
        -------
        None
        """

        self.probe('voltage', segment, conductor, index, **kwargs)


    def probe_current(self, segment, conductor, index, **kwargs):
        """Places a current probe on a conductor in a segment.

        Parameters
        ----------
        segment : str
            Name of MHARNESS segment
        conductor : str
            Name of MHARNESS conductor
        index : int
            Mesh index at which to probe
        **kwargs : see Inp.probe

        Returns
        -------
        None
        """

        self.probe('current', segment, conductor, index, **kwargs)


    def print_probes(self, numbered=True):
        """Prints lines containing probe definitions to the console.

        Parameters
        ----------
        numbered : bool (optional)
            Whether to print with line numbers and indents (set False if planning to copy-paste output)

        Returns
        -------
        None
        """

        i0 = self.find('OUTPUT / PROBES') - 1
        i1 = self.find('END THE INPUT FILE')

        if i0 is not None and i1 is not None:
            self.print(i0, i1, numbered)


    def set_terminations_by_segment(self, segments, resistance):
        """Sets conductor terminations on a given segment to the specified value.
        If a conductor terminates at both ends of a segment, the first end listed
        in the inp is modified while the other is unchanged.
        """

        # Make single segment into list if necessary
        if not isinstance(segments, (list, tuple)):
            segments = [segments]

        # Modify terminations
        termination_levels = self.find_all('!BOUNDARY CONDITION')

        for i0 in termination_levels:
            if self.get(i0 + 1) != '!!RESISTIVE':
                print(f'Skipping termination at line {Inp.itol(i0)}; only resistive terminations are currently supported.')
                continue

            i1 = self.find_next(i0, '', exact=True)

            for segment in segments:
                occurrences = self.find_all(segment, start=i0, end=i1, exact=True, separator=['_', ' '])
                added = []

                if len(occurrences) > 0:
                    for j in occurrences:
                        entries = self.get(j).split()

                        # Only modify first termination of each conductor and omit shields
                        if '___S' not in entries[1] and entries[1] not in added:
                            entries[3] = str(resistance)
                            self.lines[j] = '        '.join(entries)
                            added.append(entries[1])