import os
import jpype
import jpype.imports
from jpype.types import *
# from ... import popgen
from .treeutils import *
from .utils import *
from .readers import *
from .simulator import *
from .statistics import *
import numpy as np 
# not sure why, but calling numpy right before starting JVM is important, otherwise there will be segfault.
# issue: https://github.com/jpype-project/jpype/issues/808
# might be the conflicts between openblas and jvm multithreading.
# set OMP_NUM_THREADS=1 also makes it work.
tmp = np.linalg.inv(np.random.rand(2400, 2400))  
# package_dirname = os.path.dirname(popgen.__file__)
package_dirname = os.path.dirname(os.path.dirname(__file__))
# start JVM to import .jar libs

if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[os.path.join(package_dirname, 'libs/*')])

from .javautils import *

from .scistree import ScisTree2




