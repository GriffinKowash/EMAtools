import os
import platform
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from .metrics import calc_quality_metric, calc_error


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