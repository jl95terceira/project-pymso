import dataclasses
import sys
from   ._util import *

@dataclasses.dataclass
class Class:

    version   :str
    encoding  :str
    standalone:bool

sys.modules[__name__] = Class