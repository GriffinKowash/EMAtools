from abc import ABC, abstractmethod
import numpy as np


class Logger(ABC):
	@abstractmethod
	def log(self, test):
		pass
	
class SimpleLogger(Logger):
	def log(self, test):
		"""Format and print results for simple 1D arrays."""

		# Unpack test contents
		name = test.name
		error = test.results['error']
		passed = test.results['passed']
		x = test.sim['x']
		y_sim = test.sim['y']
		y_ref = test.ref['y']

		# Print test header
		print(f'\n_______Test name: {name}_______')

		# Print results
		if np.all(passed):
			print('\tPASSED')
		else:
			print('\n\t***FAILED at the following values of the independent variable:')
			print('\t\tx\t\tref\t\tsim\t\tmetric')
			print('\t\t____\t\t____\t\t____\t\t____')
			failures = np.where(~passed)[0]
			for i in failures:
				print(f'\t\t{x[i]}\t\t{round(y_ref[i], 3)}\t\t{round(y_sim[i], 3)}\t\t{round(error[i], 3)}')
		print()


class FEMLogger(Logger):
	def log(self, test):
		"""Format and print results for 2D FEM results."""

		# Unpack test contents
		name = test.name
		error = test.results['error']
		passed = test.results['passed']
		x = test.sim['x']
		y_sim = test.sim['y']
		y_ref = test.ref['y']

		# Print test header
		print(f'\n_______Test name: {name}_______')

		# Print results
		if np.all(passed):
			print('\tPASSED')
		else:
			print('\n\t***FAILED at the following time steps and nodes:')
			print('\t\tt\t\tNode\t\tref\t\tsim\t\tmetric')
			print('\t\t____\t\t____\t\t____\t\t____\t\t____')
			fail_rows, fail_cols = np.where(~passed)
			for i, j in zip(fail_rows, fail_cols):
				print(f'\t\t{x[j]}\t\t{i}\t\t{round(y_ref[i,j], 3)}\t\t{round(y_sim[i,j], 3)}\t\t{round(error[i,j], 3)}')
		print()