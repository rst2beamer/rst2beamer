#!/usr/bin/env python
# encoding: utf-8
"""
A docutils script converting restructured text into Beamer-flavoured LaTeX.

Beamer is a LaTeX document class for presentations. Via this script, ReST can
be used to prepare slides. It can be called::

        rst2beamer.py infile.txt > outfile.tex
        
where ``infile.txt`` contains the rst and ``outfile.tex`` contains the
Beamer-flavoured LaTeX.

See <http:www.agapow.net/software/rst2beamer> for more details.

"""
# TODO: modifications for handout sections?
# TOOD: sections and subsections?
# TODO: convert document metadata to front page fields?
# TODO: toc-conversion?
# TODO: fix descriptions
# TODO: 'r2b' or 'beamer' as identifying prefix?


# This file has been modified by Ryan Krauss starting on 2009-03-25.
# Please contact him if it is broken: ryanwkrauss@gmail.com

__docformat__ = 'restructuredtext en'
__author__ = "Ryan Krauss <ryanwkrauss@gmail.com> & Paul-Michael Agapow <agapow@bbsrc.ac.uk>"
__version__ = "0.6.4"


### IMPORTS ###

try:
    locale.setlocale (locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description
from docutils.writers.latex2e import Writer as Latex2eWriter
from docutils.writers.latex2e import LaTeXTranslator, DocumentClass
from docutils import nodes
from docutils.nodes import fully_normalize_name as normalize_name
from docutils.parsers.rst import directives, Directive


## CONSTANTS & DEFINES ###

SHOWNOTES_FALSE = 'false'
SHOWNOTES_TRUE = 'true'
SHOWNOTES_ONLY = 'only'
SHOWNOTES_LEFT = 'left'
SHOWNOTES_RIGHT = 'right'
SHOWNOTES_TOP = 'top'
SHOWNOTES_BOTTOM = 'bottom'

SHOWNOTES_OPTIONS = [
    SHOWNOTES_FALSE,
    SHOWNOTES_TRUE,
    SHOWNOTES_ONLY,
    SHOWNOTES_LEFT,
    SHOWNOTES_RIGHT,
    SHOWNOTES_TOP,
    SHOWNOTES_BOTTOM,
]

BEAMER_SPEC =   (
    'Beamer options',
    'These are derived almost entirely from the LaTeX2e options',
    tuple (
        [
            (
                'Specify theme.',
                ['--theme'],
                {'default': 'Warsaw', }
            ),
            (
                'Overlay bulleted items. Put [<+-| alert@+>] at the end of '
                '\\begin{itemize} so that Beamer creats an overlay for each '
                'bulleted item and the presentation reveals one bullet at a time',
                ['--overlaybullets'],
                {'default': True, }
            ),
            (
                'Center figures.  All includegraphics statements will be put '
                'inside center environments.',
                ['--centerfigs'],
                {'default': True, }
            ),                        
            (
                # TODO: this doesn't seem to do anything ...
                'Specify document options. Multiple options can be given, '
                'separated by commas.  Default is "10pt,a4paper".',
                ['--documentoptions'],
                {'default': '', }
            ),
            (
                "Print embedded notes along with the slides. Possible "
                    "arguments include 'false' (don't show), 'only' (show "
                    "only notes), 'left', 'right', 'top', 'bottom' (show in "
                    "relation to the annotated slide).",
                ['--shownotes'],
                {
                    'action':    "store",
                    'type':      'choice',
                    'dest':      'shownotes',
                    'choices':   SHOWNOTES_OPTIONS,
                    'default':   SHOWNOTES_FALSE,
                }
            ),
        ] + list (Latex2eWriter.settings_spec[2][2:])
    ),
)

BEAMER_DEFAULTS = {
    'use_latex_toc': True,
    'output_encoding': 'latin-1',
    'documentclass': 'beamer',
    'documentoptions': 't',#text is at the top of each slide rather than centered.  Changing to 'c' centers the text on each slide (vertically)
}


bool_strs = ['false','true','0','1']
bool_vals = [False, True, False, True]
bool_dict = dict (zip (bool_strs, bool_vals))
    

### IMPLEMENTATION ###

### UTILS

# Python 2.5 or 2.4
def index (seq, f, fail=None):
    """
    Return the index of the first item in seq where f(item) is True.
    
    :Parameters:
        seq
            A sequence or iterable
        f
            A boolean function an element of `seq`, e.g. `lambda x: x==4`
        fail
            The value to return if no item is found in seq.
            
    While this could be written in a neater fashion in Python 2.6, this method
    maintains compatiability with earlier version.
    """
    for index in (i for i in xrange (len (seq)) if f (seq[i])):
        return index
    return fail
        

def node_has_class (node, classes):
    """
    Does the node have one of these classes?
    
    :Parameters:
        node
            A docutils node
        class
            A class name or list of class names.
            
    :Returns:
        A boolean indicating membership.
            
    A convenience function, 
    """
    ## Preconditions & preparation:
    # wrap single name in list
    if (not (issubclass (type (classes), list))):
        classes = [classes]
    ## Main:
    for cname in classes:
        if cname in node['classes']:
            return True
    return False


def wrap_children_in_columns (par_node, children, width=None):
    """
    Replace this node's children with columns containing the passed children.
    
    :Parameters:
        par_node
            The node whose children are to be replaced.
        children
            The new child nodes, to be wrapped in columns and added to the
            parent.
        width
            The width to be assigned to the columns.

    In constructing columns for beamer using either 'simplecolumns' approach,
    we have to wrap the original elements in column nodes, giving them an
    appropriate width. Note that this mutates parent node.
    """
    ## Preconditions & preparation:
    # TODO: check for children and raise error if not?
    width = width or 0.90
    ## Main:
    # calc width of child columns
    child_cnt = len (children)
    col_width = width / child_cnt
    # set each element of content in a column and add to column set
    new_children = []
    for child in children:
        col = column()
        col.width = col_width
        col.append (child)
        new_children.append (col)
    par_node.children = new_children


def has_sub_sections (node):
    """Test whether or not a section node has children with the
    tagname section.  The function is going to be used to assess
    whether or not a certain section is the lowest level.  Sections
    that have not sub-sections (i.e. no children with the tagname
    section) are assumed to be Beamer slides"""
    for child in node.children:
        if child.tagname == 'section':
            return True
    return False


def string_to_bool (stringin, default=True):
    """
    Turn a commandline arguement string into a boolean value.
    """
    if type (stringin) == bool:
        return stringin
    temp = stringin.lower()
    if temp not in bool_strs:
        return default
    else:
        return bool_dict[temp]


### NODES ###
# Special nodes for marking up beamer layout

class columnset (nodes.container):
    """
    A group of columns to display on one slide.
    
    Named as per docutils standards.
    """
    # NOTE: a simple container, has no attributes.


class column (nodes.container):
    """
    A single column, grouping content.

    Named as per docutils standards.
    """
    # TODO: should really init width in a c'tor

class beamer_note (nodes.container):
    """
    Annotations for a beamer presentation.

    Named as per docutils standards and to distinguish it from core docutils
    node type.
    """
    pass


### DIRECTIVES

class SimpleColsDirective (Directive):
    """
    A directive that wraps all contained nodes in beamer columns.
    
    Accept 'width' as an optional argument for total width of contained
    columns.
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {'width': float}

    def run (self):
        ## Preconditions:
        self.assert_has_content()
        # get width
        width = self.options.get ('width', 0.9)
        if (width <= 0.0) or (1.0 < width):
            raise self.error ("columnset width '%f' must be between 0.0 and 1.0" % width)
        ## Main:
        # parse content of columnset
        dummy = nodes.Element()
        self.state.nested_parse (self.content, self.content_offset,
            dummy)
        # make columnset
        text = '\n'.join (self.content)
        cset = columnset (text)
        # wrap children in columns & set widths
        wrap_children_in_columns (cset, dummy.children, width)
        ## Postconditions & return:
        return [cset]


directives.register_directive ('r2b_simplecolumns', SimpleColsDirective)


class ColumnSetDirective (Directive):
    """
    A directive that encloses explicit columns in a 'columns' environment.

    Within this, columns are explcitly set with the column directive. There is
    a single optional argument 'width' to determine the total width of
    columns on the page, expressed as a fraction of textwidth. If no width is
    given, it defaults to 0.90.
    
    Contained columns may have an assigned width. If not, the remaining width
    is divided amongst them. Contained columns can 'overassign' width,
    provided all column widths are defined.
    
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {'width': float}

    def run (self):
        ## Preconditions:
        self.assert_has_content()
        # get and check width of column set
        width = self.options.get ('width', 0.9)
        if ((width <= 0.0) or (1.0 < width)):
            raise self.error ( \
                "columnset width '%f' must be between 0.0 and 1.0" % width)
        ## Main:
        # make columnset
        text = '\n'.join (self.content)
        cset = columnset (text)
        # parse content of columnset
        self.state.nested_parse (self.content, self.content_offset, cset)
        # survey widths
        used_width = 0.0
        unsized_cols = []
        for child in cset:
            child_width = getattr (child, 'width', None)
            if (child_width):
                used_width += child_width
            else:
                unsized_cols.append (child)

        if (1.0 < used_width):
           raise self.error ( \
            "cumulative column width '%f' exceeds 1.0" % used_width)
        # set unsized widths
        if (unsized_cols):
            excess_width = width - used_width
            if (excess_width <= 0.0):
                raise self.error ( \
                    "no room for unsized columns '%f'" % excess_width)
            col_width = excess_width / len (unsized_cols)
            for child in unsized_cols:
                child.width = col_width
        elif (width < used_width):
            # TODO: should post a warning?
            pass
        ## Postconditions & return:
        return [cset]


directives.register_directive ('r2b_columnset', ColumnSetDirective)


class ColumnDirective (Directive):
    """
    A directive to explicitly create an individual column.
    
    This can only be used within the columnset directive. It can takes a
    single optional argument 'width' to determine the column width on page.
    If no width is given, it is recorded as None and should be later assigned
    by the enclosing columnset.
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {'width': float}

    def run (self):
        ## Preconditions:
        self.assert_has_content()
        # get width
        width = self.options.get ('width', None)
        if (width is not None):
            if (width <= 0.0) or (1.0 < width):
                raise self.error ("columnset width '%f' must be between 0.0 and 1.0" % width)
        ## Main:
        # make columnset
        text = '\n'.join (self.content)
        col = column (text)
        col.width = width
        # parse content of column
        self.state.nested_parse (self.content, self.content_offset, col)
        # adjust widths
        ## Postconditions & return:
        return [col]


directives.register_directive ('r2b_column', ColumnDirective)


class NoteDirective (Directive):
    """
    A directive to include notes within a beamer presentation.
    
    """
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True
    option_spec = {}

    def run (self):
        ## Preconditions:
        self.assert_has_content()
        ## Main:
        ## Preconditions:
        # make columnset
        text = '\n'.join (self.content)
        note_node = beamer_note (text)
        # parse content of note
        self.state.nested_parse (self.content, self.content_offset, note_node)
        ## Postconditions & return:
        return [note_node]


directives.register_directive ('r2b_note', NoteDirective)


class beamer_section (Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run (self):
        title = self.arguments[0]

        section_text = '\\section{%s}' % title
        text_node = nodes.Text (title)
        text_nodes = [text_node]
        title_node = nodes.title (title, '', *text_nodes)
        name = normalize_name (title_node.astext())

        section_node = nodes.section(rawsource=self.block_text)
        section_node['names'].append(name)
        section_node += title_node
        messages = []
        title_messages = []
        section_node += messages
        section_node += title_messages
        section_node.tagname = 'beamer_section'
        return [section_node]


directives.register_directive ('beamer_section', beamer_section)
directives.register_directive ('r2b_section', beamer_section)


### WRITER

class BeamerTranslator (LaTeXTranslator):
    """
    A converter for docutils elements to beamer-flavoured latex.
    """

    def __init__ (self, document):
        LaTeXTranslator.__init__ (self, document)
        self.head_prefix = [x for x in self.head_prefix
            if ('{typearea}' not in x)]
        #hyperref_posn = [i for i in range (len (self.head_prefix))
        #    if ('{hyperref}' in self.head_prefix[i])]
        hyperref_posn = index (self.head_prefix,
            lambda x: '{hyperref}\n' in x)
        if (hyperref_posn is None):
            self.head_prefix.extend ([
                '\\usepackage{hyperref}\n'
            ])
        #self.head_prefix[hyperref_posn[0]] = '\\usepackage{hyperref}\n'
        self.head_prefix.extend ([
            '\\definecolor{rrblitbackground}{rgb}{0.55, 0.3, 0.1}\n',
            '\\newenvironment{rtbliteral}{\n',
            '\\begin{ttfamily}\n',
            '\\color{rrblitbackground}\n',
            '}{\n',
            '\\end{ttfamily}\n',
            '}\n',
        ])

        # set appropriate header options for theming
        theme = document.settings.theme
        if theme:
            self.head_prefix.append('\\usetheme{%s}\n' % theme)

        # set appropriate header options for note display
        shownotes = document.settings.shownotes
        use_pgfpages = True
        if (shownotes == SHOWNOTES_FALSE):
            option_str = 'hide notes'
            use_pgfpages = False
        elif (shownotes == SHOWNOTES_ONLY):
            option_str = 'show only notes'
        else:
            if (shownotes == SHOWNOTES_LEFT):
                notes_posn = 'left'
            elif (shownotes in [SHOWNOTES_RIGHT, SHOWNOTES_TRUE]):
                notes_posn = 'right'                 
            elif (shownotes == SHOWNOTES_TOP):
                notes_posn = 'top'                 
            elif (shownotes == SHOWNOTES_BOTTOM):
                notes_posn = 'bottom'
            else:
                # TODO: better error handling
                assert False, "unrecognised option for shownotes '%s'" % shownotes      
            option_str = 'show notes on second screen=%s' % notes_posn
        if use_pgfpages:
            self.head_prefix.append ('\\usepackage{pgfpages}\n')
        self.head_prefix.append ('\\setbeameroption{%s}\n' % option_str)

        self.overlay_bullets = string_to_bool (document.settings.overlaybullets, False)
        #using a False default because
        #True is the actual default.  If you are trying to pass in a value
        #and I can't determine what you really meant, I am assuming you
        #want something other than the actual default.
        self.centerfigs = string_to_bool(document.settings.centerfigs, False)#same reasoning as above
        self.in_columnset = False
        self.in_column = False
        self.in_note = False
        self.frame_level = 0

        # this fixes the hardcoded section titles in docutils 0.4
        self.d_class = DocumentClass ('article')

    def visit_Text (self, node):
        self.body.append(self.encode(node.astext()))

    def depart_Text(self, node):
        pass

    def begin_frametag (self):
        return '\n\\begin{frame}\n'

    def end_frametag (self):
        return '\\end{frame}\n'

    def visit_section (self, node):
        if has_sub_sections(node):
            temp = self.section_level + 1
            if temp > self.frame_level:
                self.frame_level = temp
                #print('self.frame_level=%s' % self.frame_level)
        else:
            self.body.append (self.begin_frametag())
        LaTeXTranslator.visit_section (self, node)
            

    def bookmark (self, node):
        """I think beamer alread handles bookmarks well, so I
        don't want duplicates."""
        return ''

    def depart_section (self, node):
        # Remove counter for potential subsections:
        LaTeXTranslator.depart_section (self, node)
        if (self.section_level == self.frame_level):#0
            self.body.append (self.end_frametag())
                    

    def visit_title (self, node):
        if node.astext() == 'dummy':
            raise nodes.SkipNode
        if (self.section_level == self.frame_level+1):#1
                self.body.append ('\\frametitle{%s}\n\n' % \
                                  self.encode(node.astext()))
                raise nodes.SkipNode
        else:
                LaTeXTranslator.visit_title (self, node)

    def depart_title (self, node):
        if (self.section_level != self.frame_level+1):#1
                LaTeXTranslator.depart_title (self, node)


    def visit_literal_block (self, node):
        # FIX: the purpose of this method is unclear, but it causes parsed
        # literals in docutils 0.6 to lose indenting. Thus we've solve the
        # problem be just getting rid of it. [PMA 20091020]
        
       # working due to changes in docutils and Beamer setting the quote font to
          #italic. It should
          
        self.body.append ( '\\setbeamerfont{quote}{parent={}}\n' )
        
        LaTeXTranslator.visit_literal_block (self, node)
        #if not self.active_table.is_open():
        #         self.body.append('\n\n\\smallskip\n\\begin{rtbliteral}\n')
        #         self.context.append('\\end{rtbliteral}\n\\smallskip\n\n')
        #else:
        #         self.body.append('\n')
        #         self.context.append('\n')
        #if (self.settings.use_verbatim_when_possible and (len(node) == 1)
        #    # in case of a parsed-literal containing just a "**bold**" word:
        #                and isinstance(node[0], nodes.Text)):
        #         self.verbatim = 1
        #         self.body.append('\\begin{verbatim}\n')
        #else:
        #         self.literal_block = 1
        #         self.insert_none_breaking_blanks = 1

    def depart_literal_block (self, node):
        # FIX: see `visit_literal_block`
        LaTeXTranslator.depart_literal_block (self, node)
        self.body.append ( '\\setbeamerfont{quote}{parent=quotation}\n' )

        #if self.verbatim:
        #        self.body.append('\n\\end{verbatim}\n')
        #        self.verbatim = 0
        #else:
        #        self.body.append('\n')
        #        self.insert_none_breaking_blanks = 0
        #        self.literal_block = 0
        #self.body.append(self.context.pop())


    def visit_bullet_list (self, node):
        # NOTE: required by the loss of 'topic_classes' is docutils 0.6
        # TODO: so what replaces it?
        if (hasattr (self, 'topic_classes') and
            ('contents' in self.topic_classes)):
            if self.use_latex_toc:
                raise nodes.SkipNode
            self.body.append( '\\begin{list}{}{}\n' )
        else:
            begin_str = '\\begin{itemize}'
            if self.overlay_bullets:
                begin_str += '[<+-| alert@+>]'
            begin_str += '\n'
            self.body.append (begin_str) 


    def depart_bullet_list (self, node):
        # NOTE: see `visit_bullet_list`
        if (hasattr (self, 'topic_classes') and
            ('contents' in self.topic_classes)):
            self.body.append( '\\end{list}\n' )
        else:
            self.body.append( '\\end{itemize}\n' )

##         def latex_image_length(self, width_str):
##             if ('\\textheight' in width_str) or ('\\textwidth' in width_str):
##                 return width_str
##             else:
##                 return LaTeXTranslator.latex_image_length(self, width_str)

    def visit_enumerated_list (self, node):
        #LaTeXTranslator has a very complicated
        #visit_enumerated_list that throws out much of what latex
        #does to handle them for us.  I am going back to relying
        #on latex.
        if 'contents' in self.topic_classes:
            if self.use_latex_toc:
                raise nodes.SkipNode
            self.body.append( '\\begin{list}{}{}\n' )
        else:
            begin_str = '\\begin{enumerate}'
            if self.overlay_bullets:
                begin_str += '[<+-| alert@+>]'
            begin_str += '\n'
            self.body.append(begin_str)
            if node.has_key('start'):
                self.body.append('\\addtocounter{enumi}{%d}\n' \
                                 % (node['start']-1))
            


    def depart_enumerated_list (self, node):
        if 'contents' in self.topic_classes:
            self.body.append( '\\end{list}\n' )
        else:
            self.body.append( '\\end{enumerate}\n' )


    def visit_image (self, node):
        if self.centerfigs:
            self.body.append('\\begin{center}\n')
        attrs = node.attributes
        # Add image URI to dependency list, assuming that it's
        # referring to a local file.
        self.settings.record_dependencies.add(attrs['uri'])
        pre = []                        # in reverse order
        post = []
        include_graphics_options = []
        inline = isinstance(node.parent, nodes.TextElement)
        if 'scale' in attrs:
            # Could also be done with ``scale`` option to
            # ``\includegraphics``; doing it this way for consistency.
            pre.append('\\scalebox{%f}{' % (attrs['scale'] / 100.0,))
            post.append('}')
        if 'width' in attrs:
            include_graphics_options.append('width=%s' % (
                            self.latex_image_length(attrs['width']), ))
        if 'height' in attrs:
            include_graphics_options.append('height=%s' % (
                            self.latex_image_length(attrs['height']), ))
        if ('height' not in attrs) and ('width' not in attrs):
            include_graphics_options.append('height=0.75\\textheight')

        if 'align' in attrs:
            align_prepost = {
                # By default latex aligns the bottom of an image.
                (1, 'bottom'): ('', ''),
                (1, 'middle'): ('\\raisebox{-0.5\\height}{', '}'),
                (1, 'top'): ('\\raisebox{-\\height}{', '}'),
                (0, 'center'): ('{\\hfill', '\\hfill}'),
                # These 2 don't exactly do the right thing.  The image should
                # be floated alongside the paragraph.  See
                # http://www.w3.org/TR/html4/struct/objects.html#adef-align-IMG
                (0, 'left'): ('{', '\\hfill}'),
                (0, 'right'): ('{\\hfill', '}'),}
            try:
                pre.append(align_prepost[inline, attrs['align']][0])
                post.append(align_prepost[inline, attrs['align']][1])
            except KeyError:
                pass                    # XXX complain here?
        if not inline:
            pre.append('\n')
            post.append('\n')
        pre.reverse()
        self.body.extend( pre )
        options = ''
        if len(include_graphics_options)>0:
            options = '[%s]' % (','.join(include_graphics_options))
        self.body.append( '\\includegraphics%s{%s}' % (
                            options, attrs['uri'] ) )
        self.body.extend( post )


    def depart_image (self, node):
        if self.centerfigs:
            self.body.append('\\end{center}\n')


    def astext (self):
        if self.pdfinfo is not None and self.pdfauthor:
            self.pdfinfo.append ('pdfauthor={%s}' % self.pdfauthor)
        if self.pdfinfo:
            pdfinfo = '\\hypersetup{\n' + ',\n'.join(self.pdfinfo) + '\n}\n'
        else:
            pdfinfo = ''
        head = '\\title{%s}\n' % self.title
        if self.auth_stack:
            auth_head = '\\author{%s}\n' % ' \\and\n'.join (\
                ['~\\\\\n'.join (auth_lines) for auth_lines in self.auth_stack])
            head +=  auth_head
        if self.date:
            date_head = '\\date{%s}\n' % self.date
            head += date_head
        return ''.join (self.head_prefix + [head] + self.head + [pdfinfo]
                        + self.body_prefix  + self.body + self.body_suffix)


    def visit_docinfo (self, node):
        """
        Docinfo is ignored for Beamer documents.
        """
        pass

    def depart_docinfo (self, node):
        # see visit_docinfo
        pass

    def visit_columnset (self, node):
        assert not self.in_columnset, \
            "already in column set, which cannot be nested"
        self.in_columnset = True
        self.body.append ('\\begin{columns}[T]\n')

    def depart_columnset (self, node):
        assert self.in_columnset, "not in column set"
        self.in_columnset = False
        self.body.append ('\\end{columns}\n')

    def visit_column (self, node):
        assert not self.in_column, "already in column, which cannot be nested"
        self.in_column = True
        self.body.append ('\\column{%.2f\\textwidth}\n' % node.width)

    def depart_column (self, node):
        self.in_column = False
        self.body.append ('\n')

    def visit_beamer_note (self, node):
        assert not self.in_note, "already in note, which cannot be nested"
        self.in_note = True
        self.body.append ('\\note{\n')

    def depart_beamer_note (self, node):
        self.in_note = False
        self.body.append ('}\n')

    def visit_container (self, node):
        """
        Handle containers with 'special' names, ignore the rest.
        """
        # NOTE: theres something wierd here where ReST seems to translate
        # underscores in container identifiers into hyphens. So for the
        # moment we'll allow both.
        if (node_has_class (node, ['r2b-simplecolumns', 'r2b_simplecolumns'])):
           self.visit_columnset (node)
           wrap_children_in_columns (node, node.children)
        elif (node_has_class (node, ['r2b-note', 'r2b_note'])):
           self.visit_beamer_note (node)
        else:
            # currently the LaTeXTranslator does nothing, but just in case
            LaTeXTranslator.visit_container (self, node)

    def depart_container (self, node):
        if (node_has_class (node, ['r2b-simplecolumns', 'r2b_simplecolumns'])):
            self.depart_columnset (node) 
        elif (node_has_class (node, ['r2b-note', 'r2b_note'])):
            self.depart_beamer_note (node)
        else:
            # currently the LaTeXTranslator does nothing, but just in case
            LaTeXTranslator.depart_container (self, node)


class BeamerWriter (Latex2eWriter):
        """
        A docutils writer that produces Beamer-flavoured LaTeX.
        """
        settings_spec = BEAMER_SPEC
        settings_defaults = BEAMER_DEFAULTS

        def __init__(self):
            Latex2eWriter.__init__(self)
            self.translator_class = BeamerTranslator


### TEST & DEBUG ###
# TODO: should really move to a test file or dir

def test_with_file (fpath, args=[]):
    """
    Call rst2beamer on the given file with the given args.
    
    During development, it's handy to be able to easily call the writer from
    within Python. This is a convenience function that wraps the docutils
    functions to do so.
    """
    return publish_cmdline (writer=BeamerWriter(), argv=args+[fpath])


### MAIN ###

def main ():
    description = (
        "Generates Beamer-flavoured LaTeX for PDF-based presentations." +
         default_description)
    publish_cmdline (writer=BeamerWriter(), description=description)


if __name__ == '__main__':
    main()


### END ###

