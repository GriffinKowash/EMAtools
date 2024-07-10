from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import numpy as np

from .metrics import calc_error


class Plotter(ABC):
	@abstractmethod
	def plot(self, sim, ref):
		pass


class SimplePlotter(Plotter):
	def __init__(self, test_name, plot_name, xlabel, ylabel):
		self.test_name = test_name
		self.plot_name = plot_name
		self.xlabel = xlabel
		self.ylabel = ylabel

	def plot(self, sim, ref):
		"""Plots simple_plot results and optionally error against reference data."""
			
		# Plot results
		fig_sim = self.plot_simulation(sim, ref)
		fig_error = self.plot_error(sim, ref)
			
		return fig_sim, fig_error

	def plot_simulation(self, sim, ref):
		"""Plot simulation and reference data."""

		# Unpack results
		t_sim, min_sim, mean_sim, max_sim = sim
		t_ref, min_ref, mean_ref, max_ref = ref

		# Plot simulation and reference data
		fig, ax = plt.subplots()
		ax.plot(t_sim, mean_sim, color='C0', label='Simulation')
		ax.fill_between(t_sim, min_sim, max_sim, color='C0', alpha=0.4)
		if t_ref is not None:
			ax.plot(t_ref, mean_ref, color='C1', label='Reference')
			ax.fill_between(t_ref, min_ref, max_ref, color='C1', alpha=0.4)
		ax.legend()
		ax.set_xlabel(self.xlabel)
		ax.set_ylabel(self.ylabel)
		fig.suptitle(f'{self.test_name} - {self.plot_name}')

		return fig

	def plot_error(self, t_sim, mean_sim, t_ref, mean_ref):
		"""Plot percent error against reference."""

		# Unpack results
		t_sim, min_sim, mean_sim, max_sim = sim
		t_ref, min_ref, mean_ref, max_ref = ref

		# Calculate percent error
		error = calc_error(mean_sim, mean_ref, axis=-1)
		error_percent = 100 * error

		# Plot error
		fig, ax = plt.subplots()
		ax.plot(t_ref, error_percent, label='Error')
		ax.legend()
		ax.set_xlabel(self.xlabel)
		ax.set_ylabel('Error (%)')
		fig.suptitle(f'{self.test_name} - {self.plot_name} (error)')

		return fig


class SimpleFemPlotter(SimplePlotter):
	def __init__(self, test_name):
		plot_name = 'simple plot FEM'
		xlabel = 'Time (s)'
		ylabel = 'Potential (V)'
		super().__init__(test_name, plot_name, xlabel, ylabel)