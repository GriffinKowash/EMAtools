import os
import platform
import subprocess
from tkinter.filedialog import dialogstates
import numpy as np
import matplotlib.pyplot as plt

from .metrics import calc_quality_metric, calc_error

try:
	import seaborn as sns
	sns.set()
except:
	pass


class Test:
	def __init__(self):
		pass

	def evaluate(self):
		"""Evaluate test performance using desired metric (regression, validation, etc.)"""
		pass

	def compile(self):
		pass

	@staticmethod
	def _validate_path(path, name=None):
		if name is None:
			name = 'file or directory'
		if path is None:
			raise ValueError(f'Path to {name} not provided.')
		if not os.path.exists(path):
			raise ValueError(f'Path to {name} is invalid: {path}')

	@staticmethod
	def _validate_time_steps(t0, t1):
		"""Check that two sets of time steps are equal."""
		t0 = np.array(t0)
		t1 = np.array(t1)

		if t0.ndim != 1 or t1.ndim != 1:
			raise ValueError('Both time step arrays must be one-dimensional (provided {t0.ndim} and {t1.ndim}).')
		if t0.size != t1.size:
			raise ValueError('Both time step arrays must have an equal number of entries (provided {t0.size} and {t1.size}).')
		if np.any(t0 != t1):
			raise ValueError('Both time step arrays must have identical entries.')


class ExecutionTest(Test):
	def __init__(self, exec_path=None, sim_path=None, n=None):
		self.exec_path = exec_path
		self.sim_path = sim_path
		self.n = n

	def evaluate(self):
		"""Validate paths and run simulation."""

		# Validate paths
		self._validate_exec_path()
		self._validate_sim_path()

		# Run simulation and return error code
		command = self._get_command()
		cwd = os.getcwd()
		os.chdir(self.sim_path)
		errcode = os.system(command)
		os.chdir(cwd)

		return errcode

	def _get_command(self):
		"""Generate execution command based on OS and parallel processors."""

		# Serial execution if self.n is None
		if self.n is None:
			return self.exec_path

		# For parallel sims, include --localonly if on Windows
		operating_system = platform.system()
		if operating_system == 'Windows':
			return f'mpiexec --localonly -np {self.n} {self.exec_path}'
		elif operating_system == 'Linux':
			return f'mpiexec -np {self.n} {self.exec_path}'
		else:
			raise OSError(f'Unrecognized operating system: {operating_system}.')

	def _validate_exec_path(self):
		"""Check that executable path is valid."""
		self._validate_path(self.exec_path)

	def _validate_sim_path(self):
		"""Check that simulation path is valid."""
		self._validate_path(self.sim_path)


class RegressionTest(Test):
	BEM = 0
	FEM = 1
	PIC_TEMP = 2
	PIC_DENS = 3
	FLUID_TEMP = 4
	FLUID_DENS = 5

	def __init__(self, name=None, sim_path=None, ref_path=None):
		self.name = name
		self.sim_path = sim_path
		self.ref_path = ref_path
		self.data = {} #stores raw test data by label
		self.tests = [] #stores tuples of subtests to run
		
	@classmethod
	def _get_filename(cls, result_id):
		filenames = {
			cls.BEM: 'simple_plot.dat',
			cls.FEM: 'simple_plot_fem.dat',
			cls.PIC_TEMP: 'simple_plot_pic_temp.dat',
			cls.PIC_DENS: 'simple_plot_pic_dens.dat',
			cls.FLUID_TEMP: 'simple_plot_fluid.dat',
			cls.FLUID_DENS: 'simple_plot_density.dat'
			}
		return filenames[result_id]
	
	@classmethod
	def _get_xlabel(cls, result_id):
		xlabels = {
			cls.BEM: 'Time (s)',
			cls.FEM: 'Time (s)',
			cls.PIC_TEMP: 'Time (s)',
			cls.PIC_DENS: 'Time (s)',
			cls.FLUID_TEMP: 'Time (s)',
			cls.FLUID_DENS: 'Time (s)'
			}
		return xlabels[result_id]
	
	@classmethod
	def _get_ylabel(cls, result_id):
		ylabels = {
			cls.BEM: 'Potential (V)',
			cls.FEM: 'Potential (V)',
			cls.PIC_TEMP: 'Temperature (eV)',
			cls.PIC_DENS: 'Number density (#/m^3)',
			cls.FLUID_TEMP: 'Temperature (K)',
			cls.FLUID_DENS: 'Density (kg/m^3)'
			}
		return ylabels[result_id]
	
	@classmethod
	def _get_label_suffix(cls, result_id, index):
		if result_id in (cls.PIC_TEMP, cls.PIC_DENS):
			return f'_species{index // 3}'
		elif result_id in (cls.FLUID_TEMP, cls.FLUID_DENS):
			return f'_component{index // 3}'
		else:
			return ''
		
	@classmethod
	def _get_plot_name(cls, result_id, index):
		if result_id == cls.BEM:
			return 'BEM potential'
		elif result_id == cls.FEM:
			return 'FEM potential'
		elif result_id == cls.PIC_TEMP:
			return f'plasma temperature, species {index // 3}'
		elif result_id == cls.PIC_DENS:
			return f'plasma density, species {index // 3}'
		elif result_id == cls.FLUID_TEMP:
			return f'fluid temperature, component {index // 3}'
		elif result_id == cls.FLUID_DENS:
			return f'fluid density, component {index // 3}'
			
	@staticmethod
	def _read_simple_plot(filepath):
		contents = np.loadtxt(filepath).T
		t = contents[0]
		data = contents[1:]
		return t, data

	def _add_simple_plot(self, result_id, threshold, metric=None):
		"""Add results of type result_id to the regression test."""

		# Set default metric
		if metric is None:
			metric = calc_quality_metric
		
		# Get filename and test label
		filename = self._get_filename(result_id)
		label_base = filename.removesuffix('.dat')

		# Load simulation and reference data
		t_sim, data_sim = self._read_simple_plot(os.path.join(self.sim_path, filename)) 
		t_ref, data_ref = self._read_simple_plot(os.path.join(self.ref_path, filename))
		
		# Ensure time steps align
		self._validate_time_steps(t_ref, t_sim)
		
		# Unpack data and add tests
		for i in range(0, data_sim.shape[0], 3):
			min_sim, max_sim, mean_sim = data_sim[i:i+3]
			min_ref, max_ref, mean_ref = data_ref[i:i+3]
			
			label = label_base + self._get_label_suffix(result_id, i)
			
			self.data[label + '_sim'] = (t_sim, min_sim, mean_sim, max_sim)
			self.data[label + '_ref'] = (t_ref, min_ref, mean_ref, max_ref)
			
			plot_config = {
				'xlabel': self._get_xlabel(result_id),
				'ylabel': self._get_ylabel(result_id),
				'name': self._get_plot_name(result_id, i)
				}
			
			self.tests.append((label, t_sim, mean_sim, mean_ref, metric, threshold, plot_config))
			
	def add_simple_plot_bem(self, threshold, metric=None):
		self._add_simple_plot(self.BEM, threshold, metric)
		
	def add_simple_plot_fem(self, threshold, metric=None):
		self._add_simple_plot(self.FEM, threshold, metric)
		
	def add_simple_plot_fluid_temp(self, threshold, metric=None):
		self._add_simple_plot(self.FLUID_TEMP, threshold, metric)
	
	def add_simple_plot_fluid_dens(self, threshold, metric=None):
		self._add_simple_plot(self.FLUID_DENS, threshold, metric)
		
	def add_simple_plot_pic_temp(self, threshold, metric=None):
		self._add_simple_plot(self.PIC_TEMP, threshold, metric)
		
	def add_simple_plot_pic_dens(self, threshold, metric=None):
		self._add_simple_plot(self.PIC_DENS, threshold, metric)

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


class ValidationTest(Test):
	def __init__(self):
		pass


class ParallelizationTest(Test):
	def __init__(self):
		pass