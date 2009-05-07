Introduction
============

A docutils script converting restructured text into Beamer-flavoured LaTeX.

Beamer is a LaTeX document class for presentations. rst2beamer [#homepage]_
provides a Docutils [#docutils]_ writer that transforms restructured text
[#rst]_ into Beamer-flavoured LaTeX. and provides a commandline script for the
same. Via this script, ReST can therefore be used to prepare slides and
presentations.


Installation
============

rst2beamer can be installed in a number of ways.
setuptools [#setuptools]_ is preferred, but a manual installation will
suffice.

Via setuptools / easy_install
-----------------------------

From the commandline call::

	% easy_install rst2beamer

Superuser privileges may be required. 

Via setup.py
------------

Download a source tarball, unpack it and call setup.py to
install::

	% tar zxvf rst2beamer.tgz
	% cd rst2beamer
	% python setup.py install

Superuser privileges may be required. 

Manual
------

Download and unpack the tarball as above. Ensure Docutils is available. Copy
the script ``rst2beamer.py`` to a location it can be called from.


Usage
=====

*Depending on your platform, the scripts may be installed as ``.py`` scripts,
or some form of executable, or both.*

rst2beamer can be called::

        rst2beamer.py infile.txt > outfile.tex
        
where ``infile.txt`` contains the rst and ``outfile.tex`` contains the produced Beamer LaTeX. It can takes all the arguments that rst2latex does, save the ``documentclass`` option (which is fixed to ``beamer``) and hyperref options (which are already set in beamer). It should interpret a reasonable subset of restructured text and produce reasonable LaTeX. Not all features of beamer have been implemented, just a (large) subset that allows the quick production of good looking slides. Some examples can be found in the ``docs`` directory of the distribution.

In practice, this can be used  with ``pdflatex`` (to convert the LaTeX output to PDF), to get PDF versions of a presentation.

Limitations
-----------

Sections and subsections are supported, but frametitles must be in the lowest section level.  A section with no child sections is the lowest. Note that if
you are going to use subsections anywhere in the document but your first slide isn't in a subsection, you have to use dummy a section before your first slide::

	Introduction
	------------

	dummy
	~~~~~

	Slide 1
	========

	- Point 1
	- Point 2

Images default to being centered and having a height of 0.7\textheight (you can turn off the centering with a commandline switch). Thus::

	Slide Title
	===========

	.. image :: image_name.png
	
produces a graph centered in the middle of the slide. Simple.

The top level title is set as the presentation title while 2nd-level titles are set as slide titles (``frametitles`` in Beamer terms). While all other titles are converted as normal, Beamer ignores them. There is some problem in the production of literals. rst2latex converts them to ragged-right, noindent typewriter font in a quote. Under beamer however, this makes them appear as italics. This was solved by overriding literal production with a simpler enviroment, albeit one that occasionally produces buggy output. Options to hyperref are dropped, due to this already being used in beamer.

If the content for an individual slide is too large, it will simply overflow the edges of the slide and disappear.

Earlier versions of rst2beamer did not work with docutils 0.4, seemingly due to changes in the LaTeX writer. While this has been fixed, most work has been done with docutils snapshots from version 0.5 and up. In balance, users are recommended to update docutils.


Notes
=====

History & motivation
--------------------

While preparing a course, I (PMA) became frustrated with the length of time it took to prepare a presentation, even simple slides with bullet-pointed text and lumps of code. Preparing handouts or downloadable versions was a further problem. Given that docutils already has good LaTeX output, PDF production via the Beamer document class was a logical choice. rst2beamer started as a semi-ugly hack of docutil's LaTeX machinery, making as few modifications are possible due to (a) laziness and (b) wanting to leverage as much of an existing robust code base as possible. It isn't intended to be feature-complete: it worked with the ReST that I prepared and will probably give adequate output for 90% of other simple ReST documents.


Alternatives
------------

Other output options were considered and discarded as follows:

**ReportLab's Pythonpoint:** requires a fixed frame size and would need custom XML output. Styling is done through Reportlab stylesheets, which can be complex.

**Prosper:** Another LaTeX solution. On balance, Beamer seemed better although the point is arguable.

**AxPoint:** requires Perl.

**slides and foil:** Old LaTeX solutions that are now somewhat creaky.
Beamer is a LaTeX document class for preparing PDF-based presentations. This script takes restructured text input and processes it to get a Beamer LaTeX document which can then be converted easily into a PDF for actual use or modified to produce handouts or article-style documents.


Thanks
------

Thanks to Dale Hathaway for helping track down the docutils 0.4 bug.


References
==========

.. [#homepage] rst2beamer homepages at `agapow.net <http://www.agapow/net/software/rst2beamer>`__ and `cs.siue.edu <http://home.cs.siue.edu/rkrauss/python_website/>`__

.. [#setuptools] `Installing setuptools <http://peak.telecommunity.com/DevCenter/setuptools#installing-setuptools>`__

.. [#docutils] `Docutils homepage <http://docutils.sourceforge.net/>`__

.. [#rst] `Restructured text <http://docutils.sourceforge.net/rst.html>`__

.. [#beamer] `Beamer homepage <http://latex-beamer.sourceforge.net/>`__

