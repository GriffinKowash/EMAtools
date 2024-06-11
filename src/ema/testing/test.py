import os
import platform
import subprocess
import numpy as np
import matplotlib.pyplot as plt

from .metrics import calc_quality_metric, calc_error

try:
	import seaborn
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
	def __init__(self, name=None, sim_path=None, ref_path=None):
		self.name = name
		self.sim_path = sim_path
		self.ref_path = ref_path
		self.data = {} #stores raw test data by label
		self.tests = [] #stores tuples of subtests to run

	def add_simple_plot(self, threshold, metric=None):
		if metric is None:
			metric = calc_quality_metric
		label = 'simple_plot'
		filename = 'simple_plot.dat'

		# Load simulation and reference data
		t_ref, min_ref, max_ref, mean_ref = np.loadtxt(os.path.join(self.ref_path, filename)).T
		t_sim, min_sim, max_sim, mean_sim = np.loadtxt(os.path.join(self.sim_path, filename)).T
		self.data[label + '_sim'] = (t_sim, min_sim, mean_sim, max_sim)
		self.data[label + '_ref'] = (t_ref, min_ref, mean_ref, max_ref)

		# Ensure time steps align
		self._validate_time_steps(t_ref, t_sim)

		# Add subtest to queue
		self.tests.append((label, t_sim, mean_sim, mean_ref, metric, threshold))

	def evaluate(self):
		# Evaluate regression for each subtest
		results = {}
		for label, x, sim, ref, metric, threshold in self.tests:
			value = metric(sim, ref, axis=-1)

			if metric is calc_quality_metric:
				# Store boolean "passed" and indices "failures" of failure points
				passed = np.all(value >= threshold)
				failures = np.where(value < threshold)
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
			print('value, x, sim, ref shapes:', value.shape, x.shape, sim.shape, ref.shape)
			print(f'Subtest: {label}')

			if passed:
				print('\tPASSED')
			else:
				print('\t***FAILED at the following values of the independent variable:')
				print('\t\tx\tref\tsim\tQ')
				print('\t\t____\t____\t____\t____')

				for i in failures:
					print(f'\t\t{x[i][0]}\t{ref[i]}\t{sim[i]}\t{value[i]}')

	def output_simple_plot(self, output_dir):
		t_ref, min_ref, mean_ref, max_ref = self.data['simple_plot_ref']
		t_sim, min_sim, mean_sim, max_sim = self.data['simple_plot_sim']

		error = calc_error(mean_sim, mean_ref, axis=-1)
		error_percent = 100 * error

		fig1, ax1 = plt.subplots()
		ax1.plot(t_sim, mean_sim, color='C0', label='Simulation')
		ax1.fill_between(t_sim, min_sim, max_sim, color='C0', alpha=0.4)
		ax1.plot(t_ref, mean_ref, color='C1', label='Reference')
		ax1.fill_between(t_ref, min_ref, max_ref, color='C1', alpha=0.4)
		ax1.legend()
		ax1.set_xlabel('Time (s)')
		ax1.set_ylabel('Potential (V)')
		fig1.suptitle(f'{self.name} - simulation and reference potentials')

		fig2, ax2 = plt.subplots()
		ax2.plot(t_ref, error_percent, label='Error')
		ax2.legend()
		ax2.set_xlabel('Time (s)')
		ax2.set_ylabel('Error (%)')
		fig2.suptitle(f'{self.name} - percent error against reference')

		fig1.savefig(os.path.join(output_dir, 'BEM_sphere_results.png'))
		fig2.savefig(os.path.join(output_dir, 'BEM_sphere_error.png'))


class ValidationTest(Test):
	def __init__(self):
		pass


class ParallelizationTest(Test):
	def __init__(self):
		pass