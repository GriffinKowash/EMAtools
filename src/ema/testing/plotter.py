import os
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np

from .metrics import calc_error

try:
	import seaborn as sns
	sns.set()
except:
	pass


class PlotConfig:
	def __init__(self, xlabel, ylabel, show_threshold=True):
		self.xlabel = xlabel
		self.ylabel = ylabel
		self.show_threshold = show_threshold


class Plotter(ABC):
	@abstractmethod
	def __init__(self, plot_config):
		pass

	@abstractmethod
	def plot(self, sim, ref, results):
		pass

	@abstractmethod
	def save(self, output_dir):
		pass


class SimplePlotter(Plotter):
	def __init__(self, plot_config):
		self.config = plot_config

	def plot(self, sim, ref=None, results=None, name=None):
		"""Plots simple_plot results and optionally error against reference data."""

		# Set default name
		if name is None:
			name = 'Unnamed test'
			
		# Plot results
		self.fig_sim = self.plot_simulation(sim, ref, name)
		self.fig_error = self.plot_error(results, name)
			
		return self.fig_sim, self.fig_error

	def save(self, output_dir, name):
		"""Saves plots to output directory."""

		if not os.path.isdir(output_dir):
			try:
				os.mkdir(output_dir)
			except Exception as exc:
				print(exc)
				raise ValueError(f'Invalid output directory for plots: {output_dir}')

		name_fmt = name.replace(' - ', '_').replace(' ', '_').replace('(', '').replace(')', '')
		sim_filename = '_'.join([name_fmt, 'results.png'])
		error_filename = '_'.join([name_fmt, 'error.png'])
		sim_filepath = os.path.join(output_dir, sim_filename)
		error_filepath = os.path.join(output_dir, error_filename)

		self.fig_sim.savefig(sim_filepath)
		self.fig_error.savefig(error_filepath)

	def plot_simulation(self, sim, ref, name):
		"""Plot simulation and reference data."""

		# Unpack data
		ref_y = ref['ymean'] if 'ymean' in ref else ref['y']
		sim_y = sim['ymean'] if 'ymean' in sim else sim['y']

		# Plot simulation and reference data
		fig, ax = plt.subplots()
		ax.plot(sim['x'], sim_y, color='C0', label='Simulation')
		
		if 'ymin' in sim and 'ymax' in sim:
			ax.fill_between(sim['x'], sim['ymin'], sim['ymax'], color='C0', alpha=0.4)

		if ref is not None:
			ax.plot(ref['x'], ref_y, color='C1', label='Reference')
			if 'ymin' in ref and 'ymax' in ref:
				ax.fill_between(ref['x'], ref['ymin'], ref['ymax'], color='C1', alpha=0.4)

		ax.legend()
		ax.set_xlabel(self.config.xlabel)
		ax.set_ylabel(self.config.ylabel)
		fig.suptitle(name)

		return fig

	def plot_error(self, results, name):
		"""Plot percent error against reference."""
		
		# Temporary handling of 2D FEM/BEM arrays
		if results['threshold'].ndim > 1:
			threshold = np.mean(results['threshold'], axis=0)
		else:
			threshold = results['threshold']

		if results['error'].ndim > 1:
			error = np.mean(results['error'], axis=0)
		else:
			error = results['error']

		# Plot error
		fig, ax = plt.subplots()
		ax.plot(results['x'], error, label='Error', color='C0')
		if self.config.show_threshold:
			ax.plot(results['x'], threshold, label='Pass/fail', color='C1', linestyle='--')
		ax.legend()
		ax.set_xlabel(self.config.xlabel)
		ax.set_ylabel('Error')
		fig.suptitle(f'{name} (error)')

		return fig


class SimpleBemPlotter(SimplePlotter):
	def __init__(self):
		xlabel = 'Time (s)'
		ylabel = 'Potential (V)'
		plot_config = PlotConfig(xlabel, ylabel)
		super().__init__(plot_config)


class SimpleFemPlotter(SimplePlotter):
	def __init__(self):
		xlabel = 'Time (s)'
		ylabel = 'Potential (V)'
		plot_config = PlotConfig(xlabel, ylabel)
		super().__init__(plot_config)


class SimplePicDensPlotter(SimplePlotter):
	def __init__(self):
		xlabel = 'Time (s)'
		ylabel = 'Number density (#/m^3)'
		plot_config = PlotConfig(xlabel, ylabel)
		super().__init__(plot_config)


class SimplePicTempPlotter(SimplePlotter):
	def __init__(self):
		xlabel = 'Time (s)'
		ylabel = 'Temperature (eV)'
		plot_config = PlotConfig(xlabel, ylabel)
		super().__init__(plot_config)


class SimpleFluidDensPlotter(SimplePlotter):
	def __init__(self):
		xlabel = 'Time (s)'
		ylabel = 'Density (kg/m^3)'
		plot_config = PlotConfig(xlabel, ylabel)
		super().__init__(plot_config)


class SimpleFluidTempPlotter(SimplePlotter):
	def __init__(self):
		xlabel = 'Time (s)'
		ylabel = 'Temperature (K)'
		plot_config = PlotConfig(xlabel, ylabel)
		super().__init__(plot_config)


