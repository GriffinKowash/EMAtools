import os
import platform
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from .metrics import *
from .logger import *
from .data_reader import *
from .passfunc import *


class RegressionTestV2:
	def __init__(self, name, sim, ref, metric, passfunc, logger, plotter, output_dir=None):
		self.name = name
		self.sim = sim
		self.ref = ref
		self.metric = metric
		self.passfunc = passfunc
		self.logger = logger
		self.plotter = plotter
		self.output_dir = None

	def evaluate(self):
		x = self.sim['x']
		error = self.metric.compute(self.sim, self.ref)
		threshold = self.passfunc.threshold(self.ref)
		passed = self.metric.evaluate(error, threshold)
		self.results = pd.concat([x, error, threshold, passed], axis=1)
		self.results.columns = ['x', 'error', 'threshold', 'passed']

	def log(self):
		"""Format and print results for each subtest."""
		self.logger.log(self)

	def plot(self, output_dir=None):
		self.plotter.plot(self.sim, self.ref, self.results)

		if output_dir is None:
			if self.output_dir is None:
				output_dir = os.getcwd()
			else:
				output_dir = self.output_dir

		self.plotter.save(output_dir)


class RegressionTestHandler:
	def __init__(self, sim_path, ref_path):
		self.sim_path = sim_path
		self.ref_path = ref_path
		self.tests = []

	def add_simple_plot_bem(self, metric, passfunc):
		# Load datasets
		sim = SimplePlotReader().load(SIM_PATH)
		ref = SimplePlotReader().load(REF_PATH)

		# Create logger and plotter
		logger = SimpleLogger()
		plotter = SimpleFemPlotter('FEM regression test')

		# Create test
		test = RegressionTestV2(
			name='FEM regression test',
			sim=sim,
			ref=ref,
			metric=metric,
			passfunc=passfunc,
			logger=logger,
			plotter=plotter
			)