Microsoft Office file lossless reader and writer

Python ≥ v<b>3.12</b>

# Why?

Apparently, all Python modules that exist currently that deal with reading & writing MSO files may lose information on writing files back after reading them - for example, if they have figures, charts, etc. Let's change that.

# Getting around

```
project_package -> the project module, which contains the package / the module proper and the test module.
│
├───package -> the package / module proper under development.
│
└───tests -> the test module.
```

In <code>package</code>:

<ul>

<li>
  
There are modules that correspond with the XML structure of MSO files. There is one class per module.  Each class therein is simply named <code>Class</code> and it is itself disguised as the module by calling 

```
sys.modules[__name__] = Class
```

after the class' definition, so that, when (as an example) we

```
import DocX
```

, actually what is imported is <code>DocX.Class</code> (as <code>DocX</code>).

</li><li>
  
There is a <code>_util</code> module for re-usable source that is not intended as part of the public API.

</li>

</ul>

# Contributing

The plan is to gradually add functionality to this module while maintaining the property of losslessness on writing files back, so that

<ul>

<li>
  
At the beginning, this module just reads all XML files as a map of element object trees (got RAM?) that can be saved right back. Functions to manipulate the document, if any at this point, manipulate the element trees directly.

(MSO files are zip files with XML files therein, in case you didn't know.)

</li>

<li>
  
Gradually, each XML file will be read to and written from not as an element tree but as an instance of a class that is more optimized for the XML structure. Functions to manipulate the document will act on these instances.

To pull-parse the XML, use <code>xml.parsers.expat</code> from the standard library.

</li>

<li>
  
At the very end (in a million years 😄), all XML files are loaded as instances of classes that are optimal for their structure. No more element trees, ever again.

</li>

</ul>

# Testing

Use <code>unittest</code>. Run

```
python -m unittest
```

from the root directory.  To add new tests for the project, place them in module <code>project_structure.tests</code>. From inside the test scripts, import the components to be tested with

```
import ..package
from ..package import {whatever there is to import}
```

 Read up on <a href="https://docs.python.org/3/library/unittest.html">the docs</a>.
