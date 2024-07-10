import os
import platform
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


class RegressionTestV2:
	def __init__(self, name, sim, ref, metric, passfunc, logger, plotter):
		self.name = name
		self.sim = sim
		self.ref = ref
		self.metric = metric
		self.passfunc = passfunc
		self.logger = logger
		self.plotter = plotter

	def evaluate(self):
		error = self.metric.compute(self.sim, self.ref)
		threshold = self.passfunc.threshold(self.ref)
		passed = self.metric.evaluate(error, threshold)
		self.results = pd.concat([error, threshold, passed], axis=1)
		self.results.columns = ['error', 'threshold', 'passed']		

	def log(self):
		"""Format and print results for each subtest."""
		self.logger.log(self)

	def plot(self):
		self.plotter.plot(self)
		self.plotter.save(self)


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




class Metric(ABC):
	@abstractmethod
	def compute(self, sim, ref):
		pass

	@abstractmethod
	def evaluate(self, error, threshold):
		pass

class TanhErrorMetric(Metric):
	def compute(self, sim, ref):
		sim_y = sim['y']
		ref_y = ref['y']
		return np.tanh((sim_y - ref_y) / ref_y)

	def evaluate(self, error, threshold):
		return abs(error) < threshold

class QualityMetric(Metric):
	def compute(self, sim, ref):
		sim_y = sim['y']
		ref_y = ref['y']
		return 1 - (sim_y - ref_y)**2 / (sim_y + ref_y)**2

	def evaluate(self, error, threshold):
		return abs(error) > threshold


class DataReader(ABC):
	@abstractmethod
	def load(self, filepath):
		pass

class SimplePlotReader(DataReader):
	def load(self, filepath):
		columns = ['x', 'ymin', 'ymax', 'y']
		data = pd.read_csv(filepath, sep=' ', header=None)
		species = (len(data.columns) - 1) // 3

		if species == 1:
			data.columns = columns
			return data

		else:
			datasets = []
			for n in range(species):
				i = 3*n + 1
				species_data = pd.concat([data.iloc[:, 0], data.iloc[:, i:i+3]], axis=1)
				species_data.columns = columns
				datasets.append(species_data)

			return datasets

		


class PassFunc(ABC):
	@abstractmethod
	def threshold(self, y):
		pass

class FlatPassFunc(PassFunc):
	def __init__(self, baseline):
		self.baseline = baseline

	def threshold(self, y):
		return self.baseline

class LinearBufferPassFunc(PassFunc):
	def __init__(self, baseline, cutoff):
		self.baseline = baseline
		self.ramp_stop = cutoff
		self.ramp_start = cutoff * 10

	def threshold(self, y):
		# If DataFrame, extract 'y' column and apply
		if isinstance(y, pd.DataFrame):
			return y['y'].apply(self.threshold)

		# If Series, apply to each entry
		elif isinstance(y, pd.Series):
			return y.apply(self.threshold)

		# If value, calculate threshold
		else:
			if abs(y) > self.ramp_start:
				return self.baseline
			elif abs(y) > self.ramp_stop:
				frac = (self.ramp_start - abs(y)) / (self.ramp_start - self.ramp_stop)
				return self.baseline + frac * (1 - self.baseline)
			else:
				return 1