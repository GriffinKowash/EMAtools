import os
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np

from .metrics import calc_error


class PlotConfig:
	def __init__(self, test_name, plot_name, xlabel, ylabel):
		self.test_name = test_name
		self.plot_name = plot_name
		self.xlabel = xlabel
		self.ylabel = ylabel


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

	def plot(self, sim, ref=None, results=None):
		"""Plots simple_plot results and optionally error against reference data."""
			
		# Plot results
		self.fig_sim = self.plot_simulation(sim, ref)
		self.fig_error = self.plot_error(results)
			
		return self.fig_sim, self.fig_error

	def save(self, output_dir):
		"""Saves plots to output directory."""

		if not os.path.isdir(output_dir):
			print(f'Invalid output directory for plots: {output_dir}')
			return

		sim_filename = '_'.join([self.config.test_name, self.config.plot_name, 'results.png'])
		error_filename = '_'.join([self.config.test_name, self.config.plot_name, 'error.png'])
		sim_filepath = os.path.join(output_dir, sim_filename)
		error_filepath = os.path.join(output_dir, error_filename)

		self.fig_sim.savefig(sim_filepath)
		self.fig_error.savefig(error_filepath)

	def plot_simulation(self, sim, ref):
		"""Plot simulation and reference data."""

		# Plot simulation and reference data
		fig, ax = plt.subplots()
		ax.plot(sim['x'], sim['y'], color='C0', label='Simulation')
		
		if 'ymin' in sim and 'ymax' in sim:
			ax.fill_between(sim['x'], sim['ymin'], sim['ymax'], color='C0', alpha=0.4)

		if ref is not None:
			ax.plot(ref['x'], ref['y'], color='C1', label='Reference')
			if 'ymin' in ref and 'ymax' in ref:
				ax.fill_between(ref['x'], ref['ymin'], ref['ymax'], color='C1', alpha=0.4)

		ax.legend()
		ax.set_xlabel(self.config.xlabel)
		ax.set_ylabel(self.config.ylabel)
		fig.suptitle(f'{self.config.test_name} - {self.config.plot_name}')

		return fig

	def plot_error(self, results):
		"""Plot percent error against reference."""
		
		threshold = results['threshold']

		# Plot error
		fig, ax = plt.subplots()
		ax.plot(results['x'], results['error'], label='Error', color='C0')
		ax.plot(results['x'], results['threshold'], label='Pass/fail', color='C1', linestyle='--')
		ax.legend()
		ax.set_xlabel(self.config.xlabel)
		ax.set_ylabel('Error')
		fig.suptitle(f'{self.config.test_name} - {self.config.plot_name} (error)')

		return fig


class SimpleFemPlotter(SimplePlotter):
	def __init__(self, test_name):
		plot_name = 'simple plot FEM'
		xlabel = 'Time (s)'
		ylabel = 'Potential (V)'
		super().__init__(test_name, plot_name, xlabel, ylabel)