import os
import platform
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from .test import Test
from .metrics import calc_quality_metric, calc_error

try:
	import seaborn as sns
	sns.set()
except:
	pass


class RegressionTestStrategy:
	def __init__(self, filename, xlabel, ylabel, plot_name, label_suffix=None):
		self._filename = filename
		self._xlabel = xlabel
		self._ylabel = ylabel
		self._plot_name = plot_name
		self._label_suffix = label_suffix or ''

	def get_filename(self):
		return self._filename

	def get_xlabel(self):
		return self._xlabel

	def get_ylabel(self):
		return self._ylabel

	def get_label_suffix(self, index):
		return self._label_suffix.format(index=index)

	def get_plot_name(self, index):
		return self._plot_name.format(index=index)

class BEMStrategy(RegressionTestStrategy):
	def __init__(self):
		super().__init__(
			filename='simple_plot.dat',
			xlabel='Time (s)',
			ylabel='Potential (V)',
			plot_name='BEM potential'
		)

class FEMStrategy(RegressionTestStrategy):
	def __init__(self):
		super().__init__(
			filename='simple_plot_fem.dat',
			xlabel='Time (s)',
			ylabel='Potential (V)',
			plot_name='FEM potential'
		)

class PICTempStrategy(RegressionTestStrategy):
	def __init__(self):
		super().__init__(
			filename='simple_plot_pic_temp.dat',
			xlabel='Time (s)',
			ylabel='Temperature (eV)',
			plot_name='plasma temperature, species {index}',
			label_suffix='_species{index}'
		)

class PICDensStrategy(RegressionTestStrategy):
	def __init__(self):
		super().__init__(
			filename='simple_plot_pic_dens.dat',
			xlabel='Time (s)',
			ylabel='Number density (#/m^3)',
			plot_name='plasma density, species {index}',
			label_suffix='_species{index}'
		)

class FluidTempStrategy(RegressionTestStrategy):
	def __init__(self):
		super().__init__(
			filename='simple_plot_fluid.dat',
			xlabel='Time (s)',
			ylabel='Temperature (K)',
			plot_name='fluid temperature, component {index}',
			label_suffix='_component{index}'
		)

class FluidDensStrategy(RegressionTestStrategy):
	def __init__(self):
		super().__init__(
			filename='simple_plot_density.dat',
			xlabel='Time (s)',
			ylabel='Density (kg/m^3)',
			plot_name='fluid density, component {index}',
			label_suffix='_component{index}'
		)

class RegressionTest(Test):
	def __init__(self, name=None, sim_path=None, ref_path=None):
		self.name = name
		self.sim_path = sim_path
		self.ref_path = ref_path
		self.data = {} #stores raw test data by label
		self.tests = [] #stores tuples of subtests to run

	@staticmethod
	def _read_simple_plot(filepath):
		contents = np.loadtxt(filepath).T
		t = contents[0]
		data = contents[1:]
		return t, data

	def _add_simple_plot(self, strategy, threshold, metric=None):
		"""Add results to the regression test using an appropriate strategy."""

		# Set default metric
		if metric is None:
			metric = calc_quality_metric
		
		# Get filename and test label
		filename = strategy.get_filename()
		label_base = filename.removesuffix('.dat')

		# Load simulation and reference data
		t_sim, data_sim = self._read_simple_plot(os.path.join(self.sim_path, filename)) 
		t_ref, data_ref = self._read_simple_plot(os.path.join(self.ref_path, filename))
		
		# Ensure time steps align
		self._validate_time_steps(t_ref, t_sim)
		
		# Unpack data and add tests
		for i in range(0, data_sim.shape[0], 3):
			index = i // 3

			min_sim, max_sim, mean_sim = data_sim[i:i+3]
			min_ref, max_ref, mean_ref = data_ref[i:i+3]
			
			label = label_base + strategy.get_label_suffix(index)
			
			self.data[label + '_sim'] = (t_sim, min_sim, mean_sim, max_sim)
			self.data[label + '_ref'] = (t_ref, min_ref, mean_ref, max_ref)
			
			plot_config = {
				'xlabel': strategy.get_xlabel(),
				'ylabel': strategy.get_ylabel(),
				'name': strategy.get_plot_name(index)
				}
			
			self.tests.append((label, t_sim, mean_sim, mean_ref, metric, threshold, plot_config))
			
	def add_simple_plot_bem(self, threshold, metric=None):
		self._add_simple_plot(BEMStrategy(), threshold, metric)
		
	def add_simple_plot_fem(self, threshold, metric=None):
		self._add_simple_plot(FEMStrategy(), threshold, metric)
		
	def add_simple_plot_fluid_temp(self, threshold, metric=None):
		self._add_simple_plot(FluidTempStrategy(), threshold, metric)
	
	def add_simple_plot_fluid_dens(self, threshold, metric=None):
		self._add_simple_plot(FluidDensStrategy(), threshold, metric)
		
	def add_simple_plot_pic_temp(self, threshold, metric=None):
		self._add_simple_plot(PICTempStrategy(), threshold, metric)
		
	def add_simple_plot_pic_dens(self, threshold, metric=None):
		self._add_simple_plot(PICDensStrategy(), threshold, metric)

	def evaluate(self):
		# Evaluate regression for each subtest
		results = {}
		for label, x, sim, ref, metric, threshold, plot_config in self.tests:
			value = metric(sim, ref, axis=-1)

			if metric is calc_quality_metric:
				# Store boolean "passed" and indices "failures" of failure points
				passed = np.all(value >= threshold)
				failures = np.where(value < threshold)[0]
			else:
				print(f'Metric {metric} not supported.')

			results[label] = (passed, failures, value, x, sim, ref)

		# Only pass if every subtest passed
		all_passed = np.all([result[0] for result in results.values()])

		# Store and return detailed pass/fail flag and subtest results
		self.passed = all_passed
		self.results = results

		return all_passed, results

	def report_test_results(self):
		"""Format and print results for each subtest."""
		if not hasattr(self, 'results'):
			raise ValueError('Test results not found. Ensure test has been run before attempting to print results.')

		# Print test header
		print(f'\n_______Test name: {self.name}_______')

		# Print subtest results
		for label, (passed, failures, value, x, sim, ref) in self.results.items():
			print(f'\tSubtest: {label}')

			if passed:
				print('\t\tPASSED')
			else:
				print('\n\t\t***FAILED at the following values of the independent variable:')
				print('\t\t\tx\t\tref\t\tsim\t\tQ')
				print('\t\t\t____\t\t____\t\t____\t\t____')
				for i in failures:
					print(f'\t\t\t{x[i]}\t\t{ref[i]}\t\t{sim[i]}\t\t{value[i]}')
			
			print()
					
	def output_plots(self, output_dir):
		"""Outputs plots for all subtests."""
		
		for label, t, sim, ref, metric, threshold, plot_config in self.tests:
			if 'simple_plot' in label:
				# Create output directory, if necessary
				if not os.path.exists(output_dir):
					os.mkdir(output_dir)

				# Get time series data
				label_ref = label + '_ref'
				label_sim = label + '_sim'
				t_ref, min_ref, mean_ref, max_ref = self.data[label_ref]
				t_sim, min_sim, mean_sim, max_sim = self.data[label_sim]

				# Generate and save plots
				name_fmt = self.name.replace(' ', '_')
				fig1, fig2 = self._create_simple_plot(t_sim, min_sim, mean_sim, max_sim, t_ref, min_ref, mean_ref, max_ref, plot_config)
				fig1.savefig(os.path.join(output_dir, f'{name_fmt}_{label}_results.png'))
				fig2.savefig(os.path.join(output_dir, f'{name_fmt}_{label}_error.png'))
			
			else:
				raise ValueError(f'Test "{label}" not supported for plot generation.')

	def _create_simple_plot(self, t_sim, min_sim, mean_sim, max_sim, t_ref=None, min_ref=None, mean_ref=None, max_ref=None, config=None):
		"""Plots simple_plot results and optionally error against reference data."""

		# Plot configuration defaults
		configuration = {
			'xlabel': 'Time (s)',
			'ylabel': 'Value (unspecified)',
			'name': 'simple plot'
			}
		
		# Update default with optional user parameters
		if config is not None:
			configuration.update(config)
			
		# Calculate percent error
		error = calc_error(mean_sim, mean_ref, axis=-1)
		error_percent = 100 * error
			
		# Plot results
		fig1, ax1 = plt.subplots()
		ax1.plot(t_sim, mean_sim, color='C0', label='Simulation')
		ax1.fill_between(t_sim, min_sim, max_sim, color='C0', alpha=0.4)
		if t_ref is not None:
			ax1.plot(t_ref, mean_ref, color='C1', label='Reference')
			ax1.fill_between(t_ref, min_ref, max_ref, color='C1', alpha=0.4)
		ax1.legend()
		ax1.set_xlabel(configuration['xlabel'])
		ax1.set_ylabel(configuration['ylabel'])
		fig1.suptitle(f'{self.name} - {configuration["name"]}')

		# Plot error if reference is provided
		if t_ref is not None:
			fig2, ax2 = plt.subplots()
			ax2.plot(t_ref, error_percent, label='Error')
			ax2.legend()
			ax2.set_xlabel(configuration['xlabel'])
			ax2.set_ylabel('Error (%)')
			fig2.suptitle(f'{self.name} - {configuration["name"]} (error)')
			
			return fig1, fig2
		
		else:
			return fig1