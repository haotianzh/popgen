"""

Author: Haotian Z

POPGEN is a library for research in Population Genetics.
Specifically, for computational ops on tree structures.

"""
import importlib
class LazyLoader:
    """
        LazyLoader for loading modules when they are called at the first time.
    """
    def __init__(self, lib_name):
        self.lib_name = lib_name
        self._mod = None
    def __getattr__(self, name):
        if self._mod is None:
            self._mod = importlib.import_module(self.lib_name)
        return getattr(self._mod, name)
from .utils.simulator import Simulator
from .base import Node, Haplotype, Replicate, BaseTree
from .version import __version__

