import os
import platform
from .test import Test

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