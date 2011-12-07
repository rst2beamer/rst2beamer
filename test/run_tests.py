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

import txt_mixin, os

cmd_pat = 'rst2beamer.py %s %s'


def compare_two_bodies(actual_body, expected_body):
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


    
def test_one_file(actual_tex_name, expected_tex_name, \
                  cut_header=True):
    """Load actual_tex_name and extract its body, i.e. that which is
    between \\begin{document} and \\end{document}.  Then compare this
    body to expected_tex_name."""
    actual = txt_mixin.txt_file_with_list(actual_tex_name)
    expected = txt_mixin.txt_file_with_list(expected_tex_name)
    if cut_header:
        inds1 = actual.findall('\\begin{document}')
        assert len(inds1) == 1, 'Did not find exactly one instance of \\begin{document}'
        startind = inds1[0] + 1
        inds2 = actual.findall('\\end{document}')
        assert len(inds2) == 1, 'Did not find exactly one instance of \\end{document}'
        stopind = inds2[0]
        actual_body = actual.list[startind:stopind]
    else:
        actual_body = actual.list
        
    expected_body = expected.list
    
    return compare_two_bodies(actual_body, expected_body)



class tester(object):
    """A class to try and make it easy to run different rst2beamer
    tests.  For now, the primary question is how to handle cases that
    want to also test the header and cases that want to cut it off."""
    def __init__(self, basename, cut_header=True):
        self.basename = basename
        self.rst_name = basename + '.rst'
        self.expected_out_name = basename + '_expected.tex'
        self.tex_name = basename + '.tex'
        self.cut_header = cut_header


    def run_test(self):
        if os.path.exists(self.tex_name):
            os.remove(self.tex_name)#if the tex file is left laying around and
                                    #rst2beamer fails to translate, the test
                                    #could falsely pass
        cmd = cmd_pat % (self.rst_name, self.tex_name)
        if options.traceback:
            cmd += ' --traceback'

        print(cmd)
        os.system(cmd)

        assert os.path.exists(self.tex_name), "%s does not exist.  rst translation probably failes" % self.tex_name
        self.result = test_one_file(self.tex_name, self.expected_out_name, \
                                    cut_header=self.cut_header)
        return self.result



if __name__ == '__main__':
    from optparse import OptionParser

    usage = 'usage: %prog [options]'
    parser = OptionParser(usage)

    parser.add_option("-t","--traceback", action="store_true", dest="traceback", \
                      help="run rst2beamer.py with traceback option.")

    parser.add_option("-r","--runlatex", action="store_true", dest="runlatex", \
                      help="boolean option to run pdflatex for all the test files.")

    parser.set_defaults(traceback=False)

    (options, args) = parser.parse_args()


    testing_files = ['simple_slide_test', \
                     'overlay_test',\
                     'sectioning_test', \
                     'figure_centering_test', \
                     ]


    cut_header_tests = [tester(basename) for basename in testing_files]

    keep_header_list = ['hyperlink_color', \
                        ]

    keep_header_tests = [tester(basename, cut_header=False) for basename \
                         in keep_header_list]

    failures = 0
    passed = 0

    all_tests = cut_header_tests + keep_header_tests

    for test in all_tests:
        cur_fail = test.run_test()

        if cur_fail == False:
            passed += 1
        else:
            failures += 1

        if options.runlatex:
            pdfcmd = 'pdflatex %s' % test.tex_name
            os.system(pdfcmd)



    print('='*30)
    print('tests passed = %i' % passed)
    print('total failures = %i' % failures)



