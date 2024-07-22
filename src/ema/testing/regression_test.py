import os
import platform
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod

from .metrics import *
from .logger import *
from .data_reader import *
from .passfunc import *
from .plotter import *


class RegressionTest:
	def __init__(self, name, sim, ref, metric, passfunc, logger, plotter, output_dir=None):
		self.name = name
		self.sim = sim
		self.ref = ref
		self.metric = metric
		self.passfunc = passfunc
		self.logger = logger
		self.plotter = plotter
		self.output_dir = output_dir

	def evaluate(self):
		error = self.metric.compute(self.sim, self.ref)
		threshold = self.passfunc.threshold(self.ref['y'])
		self.passed = self.metric.evaluate(error, threshold)
		self.results = {
			'x': self.sim['x'],
			'error': error,
			'threshold': threshold,
			'passed': self.passed
		}
		return np.all(self.passed)

	def log(self):
		"""Format and print results for each subtest."""
		self.logger.log(self)

	def plot(self, output_dir=None):
		self.plotter.plot(self.sim, self.ref, self.results, self.name)

		if output_dir is None:
			if self.output_dir is None:
				output_dir = os.getcwd()
			else:
				output_dir = self.output_dir

		self.plotter.save(output_dir, self.name)


class RegressionTestHandler:
	def __init__(self, sim_path, ref_path, output_dir=None, name=None):
		self.sim_path = sim_path
		self.ref_path = ref_path
		self.output_dir = output_dir
		self.name = 'Unnamed test' if name is None else name
		self.tests = []

	def evaluate(self):
		for test in self.tests:
			test.evaluate()
			test.log()
			test.plot()

		return np.all([test.passed for test in self.tests])

	def plot(self):
		for test in self.tests:
			test.plot()

	def add_simple_plot(self, plot_name, filename, metric, passfunc, plotter, logger):
		# Load datasets
		sim = SimplePlotReader().load(os.path.join(self.sim_path, filename))
		ref = SimplePlotReader().load(os.path.join(self.ref_path, filename))

		# Format test name
		test_name = '{} - {}'.format(self.name, plot_name)

		# If single species, create test
		if isinstance(sim, dict):
			test = RegressionTest(
				name=test_name,
				sim=sim,
				ref=ref,
				metric=metric,
				passfunc=passfunc,
				logger=logger,
				plotter=plotter,
				output_dir=self.output_dir
				)
			self.tests.append(test)

		# If multiple species, create multiple tests
		else:
			for i, (s, r) in enumerate(zip(sim, ref)):
				test_name_species = test_name + f' (species {i})'
				test = RegressionTest(
					name=test_name_species,
					sim=s,
					ref=r,
					metric=metric,
					passfunc=passfunc,
					logger=logger,
					plotter=plotter,
					output_dir=self.output_dir
					)
				self.tests.append(test)		

	def add_simple_plot_bem(self, metric, passfunc):
		plot_name = 'BEM potential'
		filename = 'simple_plot.dat'
		self.add_simple_plot(plot_name, filename, metric, passfunc, SimpleBemPlotter(), SimpleLogger())

	def add_simple_plot_fem(self, metric, passfunc):
		plot_name = 'FEM potential'
		filename = 'simple_plot_fem.dat'
		self.add_simple_plot(plot_name, filename, metric, passfunc, SimpleFemPlotter(), SimpleLogger())

	def add_simple_plot_pic_dens(self, metric, passfunc):
		plot_name = 'PIC density'
		filename = 'simple_plot_pic_dens.dat'
		self.add_simple_plot(plot_name, filename, metric, passfunc, SimplePicDensPlotter(), SimpleLogger())

	def add_simple_plot_pic_temp(self, metric, passfunc):
		plot_name = 'PIC temperature'
		filename = 'simple_plot_pic_temp.dat'
		self.add_simple_plot(plot_name, filename, metric, passfunc, SimplePicTempPlotter(), SimpleLogger())

	def add_simple_plot_fluid_dens(self, metric, passfunc):
		plot_name = 'Fluid density'
		filename = 'simple_plot_density.dat'
		self.add_simple_plot(plot_name, filename, metric, passfunc, SimpleFluidDensPlotter(), SimpleLogger())

	def add_simple_plot_fluid_temp(self, metric, passfunc):
		plot_name = 'Fluid temperature'
		filename = 'simple_plot_fluid.dat'
		self.add_simple_plot(plot_name, filename, metric, passfunc, SimpleFluidTempPlotter(), SimpleLogger())