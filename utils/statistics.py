from ..base import Haplotype
import pandas as pd
import numpy as np
import scipy
from scipy import stats
import os 
import subprocess as sp

DEFAULT_WINDOW_SIZE = 50
DEFAULT_SAMPLE_SIZE = 50


def get_configuration_number(haplotype, window_size=DEFAULT_WINDOW_SIZE):
    genotype_matrix = haplotype.matrix
    nhap, nsite = genotype_matrix.shape
    result = []
    combos = [[0,0], [0,1], [1,0], [1,1]]
    for site in range(nsite):
        vecs = []
        for i in range(site-window_size, site+window_size+1):
            if i < 0 or i >= nsite:
                vecs += [0,0,0,0]
                continue
            two_cols = genotype_matrix[:, (site, i)]
            for combo in combos:
                vecs.append((two_cols==combo).all(axis=1).sum())
        result.append(vecs)
    return np.array(result)


def linkage_disequilibrium_window(haplotype, window_size=DEFAULT_WINDOW_SIZE):
    """
        LDs between a specific SNP and each of its neighbor SNPs in a given length. 
    """
    genotype_matrix = haplotype.matrix
    nhap, nsite = genotype_matrix.shape
    result = []
    af = genotype_matrix.sum(axis=0) / nhap
    for site in range(nsite):
        vecs = []
        for i in range(site-window_size, site+window_size+1):
            if i < 0 or i >= nsite:
                vecs.append(0.0) # missing alleles are suppose to be linkage equilibirum, or may be improved by using values other than 0.
                continue
            two_cols = genotype_matrix[:, (site, i)]
            x00 = (two_cols==[0,0]).all(axis=1).sum() / nhap
            r2 = (x00-(1-af[site])*(1-af[i]))**2 / (af[site]*af[i]*(1-af[site])*(1-af[i]))
            vecs.append(r2)
        result.append(vecs)
    return np.array(result)


def map_to_nearby_snp(positions, index, window_size, step_size):
    nsites = len(positions)
    half_window = window_size // 2
    focal_loc = positions[index]
    cursor = focal_loc
    i = index
    res = {}
    while abs(cursor-focal_loc) <= half_window:
        while i > 0 and cursor <= positions[i-1]:
            i -= 1
        if i <= 0:
            res[cursor] = positions[0]
        else:
            if abs(positions[i]-cursor) <= abs(positions[i-1]-cursor):
                res[cursor] = positions[i]
            else:
                res[cursor] = positions[i-1]
        cursor -= step_size
    
    cursor = focal_loc
    i = index
    while abs(cursor-focal_loc) <= half_window:
        while i < nsites-1 and cursor >= positions[i+1]:
            i += 1
        if i >= nsites-1:
            res[cursor] = positions[-1]
        else:
            if abs(positions[i]-cursor) <= abs(positions[i+1]-cursor):
                res[cursor] = positions[i]
            else:
                res[cursor] = positions[i+1]
        cursor += step_size
    return res
    

def linkage_disequilibrium_bp_window(haplotype, window_size, step_size):
    """
        LDs between a specific SNP and each of its neighbor SNPs within a given physical length.
    """
    nsites = haplotype.nsites
    genotype_matrix = haplotype.matrix
    positions = haplotype.positions
    nhap, nsite = genotype_matrix.shape
    half_window = window_size // 2
    af = genotype_matrix.sum(axis=0) / nhap
    results = []
    for site in range(nsite):
        rmap = {}
        step = 0
        vec = []
        while site-step>=0 and abs(positions[site-step]-positions[site]) <= half_window:
            two_cols = genotype_matrix[:, (site, site-step)]
            x00 = (two_cols==[0,0]).all(axis=1).sum() / nhap
            r2 = (x00-(1-af[site])*(1-af[site-step]))**2 / (af[site]*af[site-step]*(1-af[site])*(1-af[site-step]))
            rmap[positions[site-step]] = r2
            step += 1
        if site-step>=0:
            two_cols = genotype_matrix[:, (site, site-step)]
            x00 = (two_cols==[0,0]).all(axis=1).sum() / nhap
            r2 = (x00-(1-af[site])*(1-af[site-step]))**2 / (af[site]*af[site-step]*(1-af[site])*(1-af[site-step]))
            rmap[positions[site-step]] = r2
        step = 0
        while site+step<nsites and abs(positions[site+step]-positions[site]) <= half_window:
            two_cols = genotype_matrix[:, (site, site+step)]
            x00 = (two_cols==[0,0]).all(axis=1).sum() / nhap
            r2 = (x00-(1-af[site])*(1-af[site+step]))**2 / (af[site]*af[site+step]*(1-af[site])*(1-af[site+step]))
            rmap[positions[site+step]] = r2
            step += 1
        if site+step<nsites:
            two_cols = genotype_matrix[:, (site, site+step)]
            x00 = (two_cols==[0,0]).all(axis=1).sum() / nhap
            r2 = (x00-(1-af[site])*(1-af[site+step]))**2 / (af[site]*af[site+step]*(1-af[site])*(1-af[site+step]))
            rmap[positions[site+step]] = r2
        neaby_map = map_to_nearby_snp(positions=positions, index=site, window_size=window_size, step_size=step_size)
        for loc in sorted(neaby_map.values()):
            vec.append(rmap[loc])
        results.append(vec)
    return np.array(results)


def linkage_disequilibrium(haplotypes):
    assert isinstance(haplotypes, list)
    lds = [pairwise_ld(hap) for hap in haplotypes]
    return lds


def pairwise_ld(haplotype):
    """
        Compute pairwise r^2 of LD.
        Input: a Haplotype object or a numpy ndarray
        Return: a 2d numpy array
    """
    if isinstance(haplotype, Haplotype):
        matrix = haplotype.matrix
    elif isinstance(haplotype, np.ndarray):
        matrix = haplotype
    else:
        Exception('Input should be an instance of either Haplotype or numpy.ndarray')
    rows, cols = matrix.shape
    freq_vec_1 = np.sum(matrix, axis=0) / rows
    freq_vec_0 = 1 - freq_vec_1
    freq_vec_1 = freq_vec_1[:, np.newaxis]
    freq_vec_0 = freq_vec_0[:, np.newaxis]
    product = np.dot(matrix.T, matrix) / rows
    p1q1 = np.dot(freq_vec_1, freq_vec_1.T)
    p0q0 = np.dot(freq_vec_0, freq_vec_0.T)
    ld = product - p1q1
    with np.errstate(divide='ignore', invalid='ignore'):
        ld = np.nan_to_num(ld ** 2 / (p1q1 * p0q0))
    return ld


def cluster_ld(matrix):
    """
        Clustering based on precomputed pairwise LD matrix.
        Input: pairwise LD matrix (numpy.array)
        Return: clustering matrix (numpy.array)
    """
    mat = matrix.copy()
    i = 0
    rows = matrix.shape[0]
    while i < rows:
        j = rows
        while j > i:
            temp = matrix[i:j, i:j]
            if np.sum(temp) / ((j - i) ** 2) > 0.1:  # threshold is 0.1 (may change here)
                mat[i:j, i:j] = 1
                i = j - 1
                break
            j = j - 1
        i = i + 1
    return mat


def stat(rates, pos, sequence_length, ne=1e5, window_size=DEFAULT_WINDOW_SIZE, step_size=DEFAULT_WINDOW_SIZE, bin_width=1e4, ploidy=1):
    """
        Formatting window-based scaled estimation to per-base recombination rates.
        Input: deeprho estimates, SNPs positions, sequence length, effective population size, window size, step size, statistical resolution, ploidy
        Return: scaledY --> per-base recombination rate in an individual window.
                bounds --> start and end of window.
                (bin_edges[:-1], v) plotting parameters.
    """
    snpsites = len(pos)
    rates = rates.reshape(-1)
    centers = []
    lens = []
    bounds = []
    for i in range(len(rates)):
        # take central point in each interval
        centers.append(pos[int(i*step_size+ window_size/2)])
        bounds.append((pos[i*step_size], pos[min(i*step_size+window_size, len(pos)-1)]))
        if i*step_size + window_size >= snpsites:
            last = len(rates)-1
        else:
            last = i*step_size + window_size
        lens.append(pos[last] - pos[i*step_size])
    lens = np.array(lens)
    scaledY = rates / lens / 2 / ploidy / ne
    v, bin_edges, _ = scipy.stats.binned_statistic(centers, scaledY, bins=sequence_length//bin_width) # range=(0,chrLength)
    return scaledY, bounds, (bin_edges[:-1], v)


def calculate_average_ne(file):
    demography = pd.read_csv(file)
    times = demography['x'].to_numpy()
    sizes = demography['y'].to_numpy()
    return _calculate_average_ne(times, sizes)


def _calculate_average_ne(times, sizes):
    """
        Calculate effective population size given demographic history.
        Formula: Ne = T / (T_1/N_1 + T_2/N_2 + ... + T_k/N_k)
        Input: a list or a ndarray of time points, a list or a ndarray of population size
        Return: Ne
    """
    assert len(times) == len(sizes), 'time and size should be in 1-to-1 correspondence'
    weighted_sum = 0
    for i in range(1, len(times)):
        weighted_sum += (times[i] - times[i-1]) / sizes[i]
    return (times[-1]-times[0]) / weighted_sum
