from ..base import Haplotype
import numpy as np
import jpype
import jpype.imports
from jpype.types import *
from labwu.rentplus.main import MPRentPlus
from labwu.py import RFDistance
from labwu.py import TripletDistance


def to_ragged(array): # return a regular array or a ragged array automatically 
    len0 = len(array)
    len1 = len(array[0])
    if len0 != len1:  
        return [np.array(a) for a in array]
    return np.array(array)


def rentplus(haps, num_thread=1, infer_branch=False):
    """
        API for inferring local genealogies from haplotypes. The original software was developed by Sajad Mirzaei (
        https://github.com/SajadMirzaei/RentPlus) A slightly different version was implemented in JAVA which introduces
        parallel computing and be capable of calling directly from python
        Input: a list of Haplotype object or a Haplotype object
        Return: a list of inferred local genealogical trees represented in Newick format
    """
    matrices = []
    positions = []
    if isinstance(haps, Haplotype):
        matrices.append(haps.matrix)
        positions.append(haps.positions) # use scaled_positions? 
    elif isinstance(haps, list):
        for hap in haps:
            matrices.append(hap.matrix)
            positions.append(hap.positions)
    # matrices = np.array(matrices, np.int)
    # positions = np.array(positions, np.int)
    matrices_java = JInt[:][:][:](matrices)
    positions_java = JInt[:][:](positions)
    rent_res = MPRentPlus.pythonMultiProcess(matrices_java, positions_java, num_thread, infer_branch)
    if isinstance(haps, Haplotype):
        return rent_res[0]
    return rent_res


def rf_dist(newicks, num_thread=10):
    """
        API for calculating Robinson-Foulds distance.
        The parallel speeding algorithm was implemented in JAVA, time complexity is O(n)
        Input: a list of trees that are represented in Newick format (https://en.wikipedia.org/wiki/Newick_format)
        Return: pairwise RF distance among those trees
    """
    dist = RFDistance.rfDistance(newicks, num_thread)
    return to_ragged(dist)


def rf_dist_window(newicks, window_size=50, which='fast', num_thread=10):
    """
        RFDistance.java -> (public static double[][][] rfDistanceWindow(String[][] newicks, int windowSize, int cpuCount, String which))
    """
    dist = RFDistance.rfDistanceWindow(newicks, window_size, num_thread, which)
    return to_ragged(dist)


def rf_dist_bp_window(newicks, positions, window_size=1000, step_size=10, num_thread=10):
    """
        RFDistance.java -> public static double[][][] rfDistanceBPWindow(String[][] newicks, int[][] positions, int windowSize, int stepSize, int cpuCount)
    """
    dist = RFDistance.rfDistanceBPWindow(newicks, positions, window_size, step_size, num_thread)
    return to_ragged(dist)


def triplet_dist(newicks, num_thread=10):
    """
        API for calculating triplet distance.
        The parallel speeding algorithm was implemented in JAVA, time complexity is O(n^2)
        Input: a list of trees that are represented in Newick format (https://en.wikipedia.org/wiki/Newick_format)
        Return: pairwise triplet distance among those trees
    """
    dist = TripletDistance.tripletDistance(newicks, num_thread)
    return to_ragged(dist)


def triplet_dist_window(newicks, window_size=50, num_thread=10):
    dist = TripletDistance.tripletDistsWindow(newicks, window_size, num_thread)
    return to_ragged(dist)