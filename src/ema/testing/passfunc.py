from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class PassFunc(ABC):
	@abstractmethod
	def threshold(self, y):
		pass

	@abstractmethod
	def _calc(self, y):
		pass

class FlatPassFunc(PassFunc):
	def __init__(self, baseline):
		self.baseline = baseline

	def threshold(self, y):
		return self._calc(y)

	def _calc(self, y):
		return self.baseline

class LinearRampPassFunc(PassFunc):
	def __init__(self, baseline, cutoff):
		self.baseline = baseline
		self.ramp_stop = cutoff
		self.ramp_start = cutoff * 10

	def threshold(self, y):
		# If array, apply vectorized _calc method
		if np.iterable(y):
			return np.vectorize(self._calc, otypes='f')(y)

		# If single value, call _calc directly
		else:
			return self._calc(y)

	def _calc(self, y):
		if abs(y) > self.ramp_start:
			return self.baseline
		elif abs(y) > self.ramp_stop:
			frac = (self.ramp_start - abs(y)) / (self.ramp_start - self.ramp_stop)
			return self.baseline + frac * (1 - self.baseline)
		else:
			return 1