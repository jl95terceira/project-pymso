Microsoft Office file lossless reader and writer

Python ≥ v<b>3.12</b>

# Why?

Apparently, all Python modules that exist currently that deal with reading & writing MSO files may lose information on writing files back after reading them - for example, if they have figures, charts, etc. Let's change that.

# Getting around

```
project_package -> the project module, which contains the the module proper and the test module
│
├─package -> the module proper under development
│
└─tests   -> the test module
```

In <code>package</code>:

<ul>

<li>
  
There are modules that contain classes that correspond with the internal structure of MSO files. 

<code>DocX</code> is intended as the class of the root object i.e. the object that contains all the data from the MSO doc (Word) file.

<i>To do: develop <code>XlsX</code> class for xl (Excel) files</i>

</li><li>
  
There is a <code>_util</code> module for re-usable source that is not intended as part of the public API.

</li>

</ul>

# Contributing

The plan is to gradually add functionality to this module while maintaining the property of losslessness on writing files back, so that

<ul>

<li>
  
At the beginning, this module just reads all XML files as a map of element object trees (got RAM?) that can be saved right back. Functions to manipulate the document, if any at this point, manipulate the element trees directly.

<i>MSO files are zip files with XML files therein, in case you didn't know.</i>

</li>

<li>
  
Gradually, each XML file will be read to and written from not as an element tree but as an instance of a class that is more optimized for the XML structure. Functions to manipulate the document will act on these instances.

To pull-parse the XML, use <code><a href="https://docs.python.org/3/library/pyexpat.html">xml.parsers.expat</code></a>.

</li>

<li>
  
At the very end, all XML files are loaded as instances of classes that are optimal for their structure. No more element trees, ever again.

</li>

</ul>

# Testing

Use <code><a href="https://docs.python.org/3/library/unittest.html">unittest</a></code>. Run

```
python -m unittest
```

from the root directory (outside of <code>project_package</code>). 

To add new tests for the project, place them in module <code>project_structure.tests</code>. From inside the test scripts, import the components to be tested with

```
import ..package
from ..package import {whatever there is to import}
```
