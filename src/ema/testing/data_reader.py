import sys
import os
from abc import ABC, abstractmethod
import numpy as np

from ..results import load_charge_results


class DataReader(ABC):
	@abstractmethod
	def load(self, filepath):
		pass

class SimplePlotReader(DataReader):
	def load(self, filepath):
		columns = ['x', 'ymin', 'ymax', 'y']
		data = np.loadtxt(filepath).T
		species = (data.shape[0] - 1) // 3

		if species == 1:
			data_dict = {
				'x': data[0],
				'ymin': data[1],
				'ymax': data[2],
				'y': data[3]
			}
			return data_dict

		else:
			data_dicts = []
			for n in range(species):
				i = 3*n + 1
				data_dict = {
					'x': data[0],
					'ymin': data[i],
					'ymax': data[i+1],
					'y': data[i+2]
				}
				data_dicts.append(data_dict)

			return data_dicts

class FEMReader(DataReader):
	def load(self, filepath):
		# Load time steps and field data
		t, data_dict = load_charge_results(filepath)
		return {field : {'x': t,
						 'y': data_dict[field],
						 'ymin': np.min(data_dict[field], axis=0),
						 'ymean': np.mean(data_dict[field], axis=0),
						 'ymax': np.max(data_dict[field], axis=0)
						 } for field in data_dict}