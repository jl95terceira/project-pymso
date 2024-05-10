import dataclasses
import sys
from   ._util import *

@dataclasses.dataclass
class XmlDeclaration:

    version   :str
    encoding  :str
    standalone:bool
