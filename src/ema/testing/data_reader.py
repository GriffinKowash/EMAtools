from abc import ABC, abstractmethod
import pandas as pd


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