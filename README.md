Microsoft Office file lossless reader and writer

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

There are modules that correspond with the XML structure of MSO files. There is one class per module. The classes therein are simply called <code>Class</code> and are renamed on import in <code>__init__.py</code> accordingly. 

There is a <code>_util</code> module for re-usable source that is not intended as part of the public API.

# Contributing

MSO files are zip files with XML files therein. The plan is to gradually change the implementation so that

<ul>

<li>At the beginning, this module just reads all XML files as a map of element trees that can be saved right back. Let's not implement any functions to manipulate the document, at this point.</li>

<li>Gradually, each XML file will be read to and written from not as an element tree but as an instance of a class that is more optimized for the XML structure. Functions to manipulate the document will act on these instances. The remaining XML files are still loaded as element trees and we don't worry about them yet.</li>

<li>At the very end (in a million years 😄), all XML files are loaded as instances of classes that are optimal for their structure. No more element trees, ever again.</li>

</ul>

# Testing

Use <code>unittest</code>. Keep all tests in module <code>project_structure.tests</code>. Read up on <a href="https://docs.python.org/3/library/unittest.html">the docs</a>.

Run

```
python -m unittest
```

from the root directory.  (For this methodology to work smoothly is why the project files are organized as they are. It allows for the tests module to relative-import <code>package</code> and it also helps the IDE - VS Code, as a good example - figure out the imports).
