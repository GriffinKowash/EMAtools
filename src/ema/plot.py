"""This module contains some quick plotting utilities intended to be used interactively from the command line."""

import os
import numpy as np
import matplotlib.pyplot as plt
try:
	import seaborn as sns
	sns.set()
except:
	pass

def simple_plot(path=None):
	"""Plot simple_plot.dat results."""
	
	# Look in cwd if no path provided
	if path is None:
		path = os.getcwd()

	# Look for file if not specified
	if not path.endswith('.dat'):
		path = os.path.join(path, 'simple_plot.dat')

	# Throw exception if not found
	if not os.path.isfile(path):
		raise ValueError(f'Could not find file {path}')

	# Load data and plot
	t, vmin, vmax, vmean = np.loadtxt(path).T
	plt.plot(t, vmean, label='Mean')
	plt.fill_between(t, vmin, vmax, alpha=0.4, label='Range')
	plt.legend()
	plt.xlabel('Time (s)')
	plt.ylabel('Potential (V)')
	plt.suptitle(f'Simple plot results - {os.path.basename(os.path.dirname(path))}')
	plt.show()