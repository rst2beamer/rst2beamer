========================================
Highlighted blocks of code in rst2beamer
========================================

Usage
-----

The LaTeX source for the corresponding Beamer example can be produced::

	rst2beamer codeblocks.rst codeblocks.tex
	
If Pygments is available, syntax highlighting can be used::

	rst2beamer --usepygments codeblocks.rst codeblocks_hilite.tex


Simple columns
--------------

The ``code-block`` (or ``sourcecode``) directive can be used to format blocks of source code. Note that the language must passed as an option. Normally this is represented as a literal block, but if Pygments is activated, the syntax will be highlighted:


.. code-block:: python

	def myfunc (arg1, arg2='foo'):
		global baz
		bar = unicode (quux)
		return 25


Containers as codeblocks
------------------------

dsfsdfdsf
