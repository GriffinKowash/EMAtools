#from .midpoint_probes import create_graph, find_conductors_and_segments, parse_segment, find_limb_containing, add_limb, create_limbs, find_limb_endpoints, order_limb, find_segment_length, find_array_midpoint, find_limb_midpoint, probe_conductor_currents
from .midpoint_probes import probe_conductor_currents, find_conductors_and_segments
from .endpoint_probes import find_terminations, find_segment_endpoint_index


class CoupledSim:
	"""Class for manipulation coupled EMA3D/MHARNESS simulations."""

	def __init__(self, emin, inp):
		"""Initialize Coupled object from Emin and Inp objects."""
		self.emin = emin
		self.inp = inp


	def probe_midpoint_currents(self, conductors=None, verbose=False):
		"""Place current pin probes at the midpoint of each non-branching chain of segments.

		Parameters
        ----------
        conductors : str | list (optional)
        	Name or names of conductors to probe. If None, probes all conductors.
		verbose : bool (optional)
			Whether to print status messages to the console. Mainly for debugging.

        Returns
        -------
        None
		"""

		# Grab all conductors if none are specified
		if conductors is None:
			conductors = list(find_conductors_and_segments(self.inp).keys())
		elif isinstance(conductors, str):
			conductors = [conductors]

		# Add current probes to midpoints
		for conductor in conductors:
		    print(f'Probing conductor {conductor}...')
		    #try:
		    probe_conductor_currents(conductor, self.inp, self.emin, verbose)
		    print('Probes added.\n')
		    #except Exception as exc:  #bug-prone; better to target explicit exceptions
		    #    print(f'*** Failed to add probes to conductor {conductor}.')
		    #    print(exc)
		        
		print('\nFinished probing conductors.')


	def probe_termination_voltages(self, conductors=None, threshold=0):
		"""Place voltage pin probes at the terminations of a set of conductors.

		Parameters
        ----------
        conductors : str | list (optional)
        	Name or list of names of conductors to probe. If None, probes all conductors.
        threshold : float (optional)
        	Minimum termination resistance to probe. Useful for probing only Mohm terminations in Voc simulations.

        Returns
        -------
        None
		"""

		# Find terminations defined in inp file, optionally filtering by conductor name
		terminations = find_terminations(self.inp, conductors)

		# Loop over terminations and place voltage probes
		for segment, conductor, endpoint, resistance in terminations:
			if float(resistance) < threshold:
				continue

			segment_root = segment.split('_')[0] #remove topology information if present
			index = find_segment_endpoint_index(segment_root, endpoint, self.emin)
			self.inp.probe_voltage(segment, conductor, index)


	def print_probes(self):
		"""Prints lines containing probe definitions to the console.

        Parameters
        ----------
        numbered : bool (optional)
            Whether to print with line numbers and indents (set False if planning to copy-paste output)

        Returns
        -------
        None
        """

		self.inp.print_probes()


	def save(self):
		#TODO: add docstring and option for custom path
		self.emin.save()
		self.inp.save()