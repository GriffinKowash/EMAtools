from abc import ABC, abstractmethod
import pandas as pd

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