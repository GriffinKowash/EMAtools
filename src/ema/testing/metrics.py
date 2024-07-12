import numpy as np
from abc import ABC, abstractmethod


def calc_quality_metric(data, ref, beta=1e-16, axis=None):
    """Take in sim and reference data and calculates regression metric."""
    
    if axis is None:
        Q = 1 - np.sum((data - ref)**2 / (2*beta + np.abs(data) + np.abs(ref))**2) / data.size
       
    else:
        size = data.size / data.shape[axis]
        
        if axis == -1:
            axes = tuple(range(len(data.shape)))[:-1]
        else:
            axes = tuple(list(range(len(data.shape))).remove(axis))
            
        Q = 1 - np.sum((data - ref)**2 / (2*beta + np.abs(data) + np.abs(ref))**2, axis=axes) / size
        
    return Q


def calc_error(data, ref, axis=None):
    """Take in sim and reference data and calculates error."""
    
    error = (data - ref) / (ref + 1e-16)

    if axis is not None:
        size = data.size / data.shape[axis]
        
        if axis == -1:
            axes = tuple(range(len(data.shape)))[:-1]
        else:
            axes = tuple(list(range(len(data.shape))).remove(axis))
            
        error = np.mean(error, axis=axes)
        
    return error


def calc_asymptotic_error(data, ref, axis=None):
    """Take in sim and reference data and calculates error bounded between -1 and 1."""
    
    error = np.tanh((data - ref) / ref)

    if axis is not None:
        size = data.size / data.shape[axis]
        
        if axis == -1:
            axes = tuple(range(len(data.shape)))[:-1]
        else:
            axes = tuple(list(range(len(data.shape))).remove(axis))
            
        error = np.mean(error, axis=axes)
        
    return error



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