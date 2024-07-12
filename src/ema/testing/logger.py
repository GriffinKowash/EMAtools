from abc import ABC, abstractmethod
import numpy as np


class Logger(ABC):
	@abstractmethod
	def log(self, test):
		pass
	
class SimpleLogger(Logger):
	def log(self, test):
		"""Format and print results for each subtest."""

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
		if all(passed):
			print('\tPASSED')
		else:
			print('\n\t***FAILED at the following values of the independent variable:')
			print('\t\tx\t\tref\t\tsim\t\tmetric')
			print('\t\t____\t\t____\t\t____\t\t____')
			failures = np.where(~passed)[0]
			for i in failures:
				print(f'\t\t{x[i]}\t\t{round(y_ref[i], 3)}\t\t{round(y_sim[i], 3)}\t\t{round(error[i], 3)}')
		print()