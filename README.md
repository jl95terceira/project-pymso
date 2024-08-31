Microsoft Office file lossless reader and writer

Python ≥ v<b>3.12</b>

___
We already have some working public API methods!
- <code>DocX.load_from_file(f)</code> - get a <code>DocX</code> object that corresponds with a Word file, given as a file handler or by name as <code>str</code>
- <code>DocX.save_file(f)</code> - save the <code>DocX</code> object to a Word file, given as a file handler or by name as <code>str</code>
- <code>DocX.paragraphs()</code> - yield <code>Paragraph</code> objects
- <code>Paragraph.runs()</code> - yield <code>Run</code> objects
  
  A "<code>Run</code>" is a part of a paragraph with its own formatting / style, which may differ from other parts of the same paragraph.
  
- <code>Run.text()</code> - get the text of the paragraph's run as a <code>str</code>
- <code>Paragraph.text()</code> - get the joined text of all of the paragraph's runs i.e. the text of the whole paragraph as a <code>str</code>

*TODO: It probably would be a good idea to document the API in the wiki, instead, not to have it here polluting the readme.*
___

# Why?

Apparently, all Python modules that exist currently that deal with reading & writing MSO files may lose information on writing files back after reading them - for example, if they have figures, charts, etc. Let's change that.

# Getting around

```
project -> the project module, which contains the the module proper and the test module
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

*TODO: develop <code>XlsX</code> class for xl (Excel) files*

</li><li>
  
There is a <code>_util</code> module for re-usable source that is not intended as part of the public API.

</li>

</ul>

# Contributing

The plan is to gradually add functionality to this module while maintaining the property of losslessness for loading / saving, from the beginning to the end (?) of the development of this module, so that

<ul>

<li>
  
At the beginning, this module just reads all XML files as a map of generic element object trees (got RAM?) that can be saved right back. Methods to inspect or to manipulate the document, if any at this point, manipulate the element trees directly.

*MSO files are zip files with XML files therein, in case you didn't know.*

</li>

<li>
  
Gradually, each XML file will be read to and written from not as a generic element tree but as an instance of a class that is optimized for the XML structure. Methods to inspect or to manipulate the document will act on these instances.

To stream-parse the XML, use <code><a href="https://docs.python.org/3/library/pyexpat.html">xml.parsers.expat</code></a>.

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

from the top directory (the repository's, outside of <code>project</code>).

To add new tests for the project, place them in module <code>project.tests</code>. From inside the test scripts, import the components to be tested with

```
import ..package
from ..package import {whatever}
```
