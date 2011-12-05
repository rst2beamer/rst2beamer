"""My plan to automate the testing is to have an expected tex output
body for each test.  The main test script will have a list of input
file names.  These filenames will not have any extensions.  For each
item in the list, a .rst will be added to form the input filename and
_expected.tex will be added to form the expected output filename.  In
order to minimize trivial failures, I plan to chop off the header and
only check everything between \\begin{document} and \\end{document}.
I am utilizing a small module I have written for working with text
files called txt_mixin.  I have added a symlink to this module to the
rst2beamer repo.

Note that many .tex files will be generated as a result of this
testing.  I am using

git update-index --assume-unchanged output_file.tex

to ask git not to track changes to these files.
"""

#################################
#
# To Do:
#
#  - add automated tests for any rst files in this dir that aren't
#    represented here
#  - add tests for various commandline options
#
#################################


from optparse import OptionParser

usage = 'usage: %prog [options]'
parser = OptionParser(usage)

parser.add_option("-t","--traceback", action="store_true", dest="traceback", \
                  help="run rst2beamer.py with traceback option.")

parser.add_option("-r","--runlatex", action="store_true", dest="runlatex", \
                  help="boolean option to run pdflatex for all the test files.")

parser.set_defaults(traceback=False)

(options, args) = parser.parse_args()

import txt_mixin, os


testing_files = ['simple_slide_test', \
                 'overlay_test',\
                 'sectioning_test', \
                 'figure_centering_test', \
                 ]

cmd_pat = 'rst2beamer.py %s %s'

def test_one_file(actual_tex_name, expected_tex_name):
    """Load actual_tex_name and extract its body, i.e. that which is
    between \\begin{document} and \\end{document}.  Then compare this
    body to expected_tex_name."""
    actual = txt_mixin.txt_file_with_list(actual_tex_name)
    expected = txt_mixin.txt_file_with_list(expected_tex_name)
    inds1 = actual.findall('\\begin{document}')
    assert len(inds1) == 1, 'Did not find exactly one instance of \\begin{document}'
    startind = inds1[0] + 1
    inds2 = actual.findall('\\end{document}')
    assert len(inds2) == 1, 'Did not find exactly one instance of \\end{document}'
    stopind = inds2[0]
    actual_body = actual.list[startind:stopind]
    expected_body = expected.list
    #strip empty lines from beginning and end of both lists
    while not actual_body[0]:
        actual_body.pop(0)
    while not actual_body[-1]:
        actual_body.pop(-1)
    while not expected_body[0]:
        expected_body.pop(0)
    while not expected_body[-1]:
        expected_body.pop(-1)

    failure = False

    if len(actual_body) != len(expected_body):
        failure = True
        print('actual_body and expected_body are not the same length:')
        print('len(actual_body) = %i' % len(actual_body))
        print('len(expected_body) = %i' % len(expected_body))

    for act_line, exp_line in zip(actual_body, expected_body):
        if act_line != exp_line:
            failure = True
            print('-'*30)
            print('failure:')
            print('act_line = %s' % act_line)
            print('exp_line = %s' % exp_line)

    return failure
        
    
failures = 0
passed = 0

for item in testing_files:
    rst_name = item + '.rst'
    expected_out_name = item + '_expected.tex'
    tex_name = item + '.tex'
    if os.path.exists(tex_name):
        os.remove(tex_name)#if the tex file is left laying around and
                           #rst2beamer fails to translate, the test
                           #could falsely pass
    cmd = cmd_pat % (rst_name, tex_name)
    if options.traceback:
        cmd += ' --traceback'
        
    print(cmd)
    os.system(cmd)

    assert os.path.exists(tex_name), "%s does not exist.  rst translation probably failes" % tex_name
    cur_fail = test_one_file(tex_name, expected_out_name)
    failures += cur_fail

    if cur_fail == False:
        passed += 1

    if options.runlatex:
        pdfcmd = 'pdflatex %s' % tex_name
        os.system(pdfcmd)
        

print('='*30)
print('tests passed = %i' % passed)
print('total failures = %i' % failures)


    
