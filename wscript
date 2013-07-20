## -*- python -*-
## (C) 2007-2013 Gustavo J. A. M. Carneiro

from wutils import get_version, generate_version_py

from waflib import Options
from waflib import Build

import Scripting
# Scripting.excludes.remove('Makefile')
Scripting.dist_format = 'zip'

from waflib import Configure
#Configure.autoconfig = True

from waflib import Logs

#from Params import fatal

import os
import subprocess
import shutil
import sys
import Configure
import tarfile
import re
import types

#import Task
#Task.file_deps = Task.extract_deps


APPNAME='pybindgen'
top = '.'
out = 'build'



## Add the pybindgen dir to PYTHONPATH, so that the examples and tests are properly built before pybindgen is installed.
if 'PYTHONPATH' in os.environ:
    os.environ['PYTHONPATH'] = os.pathsep.join([os.getcwd(), os.environ['PYTHONPATH']])
else:
    os.environ['PYTHONPATH'] = os.getcwd()
    

# http://coreygoldberg.blogspot.com/2009/07/python-zip-directories-recursively.html
def zipper(dir, zip_file, archive_main_folder=None):
    import zipfile
    zip = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(dir))
    for root, dirs, files in os.walk(dir):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            if archive_main_folder is not None:
                if archive_name.startswith(os.sep):
                    n = archive_name[len(os.sep):]
                else:
                    n = archive_name
                archive_name = os.path.join(archive_main_folder, n)
            zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    zip.close()



def options(opt):
    opt.tool_options('python')
    opt.tool_options('compiler_cc')
    opt.tool_options('compiler_cxx')
    opt.tool_options('cflags', tooldir="waf-tools")
    opt.sub_options('examples')


    optgrp = opt.add_option_group("PyBindGen Options")

    if os.path.isdir(".bzr"):
        optgrp.add_option('--generate-version',
                          help=('Generate a new pybindgen/version.py file from version control'
                                ' introspection.  Only works from a bzr checkout tree, and is'
                                ' meant to be used by pybindgen developers only.'),
                          action="store_true", default=False,
                          dest='generate_version')

    optgrp.add_option('--examples',
                      help=('Compile the example programs.'),
                      action="store_true", default=False,
                      dest='examples')

    optgrp.add_option('--disable-pygccxml',
                      help=('Disable pygccxml for unit tests / examples.'),
                      action="store_true", default=False,
                      dest='disable_pygccxml')

    optgrp.add_option('--valgrind',
                      help=('Run unit tests through valgrind.'),
                      action="store_true", default=False,
                      dest='valgrind')



def _check_compilation_flag(conf, flag, mode='cxx', linkflags=None):
    """
    Checks if the C++ compiler accepts a certain compilation flag or flags
    flag: can be a string or a list of strings
    """
    l = []
    if flag:
        l.append(flag)
    if isinstance(linkflags, list):
        l.extend(linkflags)
    else:
        if linkflags:
            l.append(linkflags)
    if len(l) > 1:
        flag_str = 'flags ' + ' '.join(l)
    else:
        flag_str = 'flag ' + ' '.join(l)
    if flag_str > 28:
        flag_str = flag_str[:28] + "..."

    conf.start_msg('Checking for compilation %s support' % (flag_str,))
    env = conf.env.copy()

    if mode == 'cc':
        mode = 'c'

    if mode == 'cxx':
        fname = 'test.cc'
        env.append_value('CXXFLAGS', flag)
    else:
        fname = 'test.c'
        env.append_value('CFLAGS', flag)

    if linkflags is not None:
        env.append_value("LINKFLAGS", linkflags)

    try:
        retval = conf.run_c_code(code='#include <stdio.h>\nint main() { return 0; }\n',
                                 env=env, compile_filename=fname,
                                 features=[mode, mode+'program'], execute=False)
    except Configure.ConfigurationError:
        ok = False
    else:
        ok = (retval == 0)
    conf.end_msg(ok)
    return ok


# starting with waf 1.6, conf.check() becomes fatal by default if the
# test fails, this alternative method makes the test non-fatal, as it
# was in waf <= 1.5
def _check_nonfatal(conf, *args, **kwargs):
    try:
        return conf.check(*args, **kwargs)
    except conf.errors.ConfigurationError:
        return None


def configure(conf):

    conf.check_compilation_flag = types.MethodType(_check_compilation_flag, conf)
    conf.check_nonfatal = types.MethodType(_check_nonfatal, conf)

    ## Write a pybindgen/version.py file containing the project version
    generate_version_py()

    conf.check_tool('command', tooldir="waf-tools")
    conf.check_tool('python')
    conf.check_python_version((2,3))

    try:
        conf.check_tool('compiler_cc')
        conf.check_tool('compiler_cxx')
    except Configure.ConfigurationError:
        Logs.warn("C/C++ compiler not detected.  Unit tests and examples will not be compiled.")
        conf.env['CXX'] = ''
    else:
        conf.check_tool('cflags')
        conf.check_python_headers()

        if not Options.options.disable_pygccxml:
            gccxml = conf.find_program('gccxml')
            if not gccxml:
                conf.env['ENABLE_PYGCCXML'] = False
            else:
                try:
                    conf.check_python_module('pygccxml')
                except Configure.ConfigurationError:
                    conf.env['ENABLE_PYGCCXML'] = False
                else:
                    conf.env['ENABLE_PYGCCXML'] = True

        # -fvisibility=hidden optimization
        if (conf.env['CXX_NAME'] == 'gcc' and [int(x) for x in conf.env['CC_VERSION']] >= [4,0,0]
            and conf.check_compilation_flag('-fvisibility=hidden')):
            conf.env.append_value('CXXFLAGS_PYEXT', '-fvisibility=hidden')
            conf.env.append_value('CCFLAGS_PYEXT', '-fvisibility=hidden')

        # Add include path for our stdint.h replacement, if needed (pstdint.h)
        if not conf.check_nonfatal(header_name='stdint.h'):
            conf.env.append_value('CPPPATH', os.path.join(conf.curdir, 'include'))

    if conf.check_nonfatal(header_name='boost/shared_ptr.hpp'):
        conf.env['ENABLE_BOOST_SHARED_PTR'] = True

    conf.sub_config('benchmarks')
    conf.sub_config('examples')


def build(bld):
    #global g_bld
    #g_bld = bld
    if getattr(Options.options, 'generate_version', False):
        generate_version_py(force=True)

    bld.add_subdirs('pybindgen')

    if bld.cmd == 'check':
        bld.add_subdirs('tests')

    if Options.options.examples:
        bld.add_subdirs('examples')

    if 0: # FIXME

        if Options.commands.get('bench', False) or Options.commands['clean']:
            bld.add_subdirs('benchmarks')


check_context = Build.BuildContext
def bench(bld):
    "run the benchmarks; requires many tools, used by maintainers only"
    Scripting.build(bld)
    env = g_bld.env

    print "Running benchmarks..."
    retval = subprocess.Popen([env['PYTHON'], '-O', 'benchmarks/bench.py',
                               "build/default/benchmarks/results.xml", ' '.join(env['CXXFLAGS_PYEXT'] + env['CXXFLAGS'])]).wait()
    if retval:
        raise SystemExit(retval)

    print "Generating benchmarks report..."
    retval = subprocess.Popen([env['PYTHON'], '-O', 'benchmarks/plotresults.py',
                               "build/default/benchmarks/results.xml",
                               "build/default/benchmarks/results"]).wait()
    if retval:
        raise SystemExit(retval)


from waflib import Context, Build, Scripting
class CheckContext(Context.Context):
    """run the unit tests"""
    cmd = 'check'

    def execute(self):

        # first we execute the build
	bld = Context.create_context("build")
	bld.options = Options.options # provided for convenience
	bld.cmd = "check"
	bld.execute()


        if Options.options.verbose:
            verbosity = ['-v']
        else:
            verbosity = []

        if Options.options.valgrind:
            valgrind = ['valgrind', '--leak-check=full', '--leak-resolution=low']
        else:
            valgrind = []

        print "Running pure python unit tests..."
        python = bld.env['PYTHON'][0]
        retval1 = subprocess.Popen([python, 'tests/test.py'] + verbosity).wait()

        env = bld.env

        retvals = []

        if env['CXX']:
            print "Running manual module generation unit tests (module foo)..."
            retvals.append(subprocess.Popen(valgrind + [python, 'tests/footest.py', '1'] + verbosity).wait())
        else:
            print "Skipping manual module generation unit tests (no C/C++ compiler)..."

        if env['ENABLE_PYGCCXML']:
            print "Running automatically scanned module generation unit tests (module foo2)..."
            retvals.append(subprocess.Popen(valgrind + [python, 'tests/footest.py', '2'] + verbosity).wait())

            print "Running module generated by automatically generated python script unit tests (module foo3)..."
            retvals.append(subprocess.Popen(valgrind + [python, 'tests/footest.py', '3'] + verbosity).wait())

            print "Running module generated by generated and split python script unit tests  (module foo4)..."
            retvals.append(subprocess.Popen(valgrind + [python, 'tests/footest.py', '4'] + verbosity).wait())

            print "Running semi-automatically scanned c-hello module ('hello')..."
            retvals.append(subprocess.Popen(valgrind + [python, 'tests/c-hello/hellotest.py'] + verbosity).wait())
        else:
            print "Skipping automatically scanned module generation unit tests (pygccxml missing)..."
            print "Skipping module generated by automatically generated python script unit tests (pygccxml missing)..."
            print "Skipping module generated by generated and split python script unit tests  (pygccxml missing)..."
            print "Skipping semi-automatically scanned c-hello module (pygccxml missing)..."

        if env['ENABLE_BOOST_SHARED_PTR']:
            print "Running boost::shared_ptr unit tests..."
            retvals.append(subprocess.Popen(valgrind + [python, 'tests/boost/bartest.py'] + verbosity).wait())
        else:
            print "Skipping boost::shared_ptr unit tests (boost headers not found)..."

        if any(retvals):
            Logs.error("Unit test failures")
            raise SystemExit(2)



class DistContext(Scripting.Dist):

    cmd = 'dist'
    def get_base_name(self):
        srcdir = '.'
        version = get_version(srcdir)
        return "pybindgen-" + version


    def execute(self):
        blddir = './build'
        srcdir = '.'
        version = get_version(srcdir)
        subprocess.Popen([os.path.join(srcdir, "generate-ChangeLog")],  shell=True).wait()
        try:
            os.chmod(os.path.join(srcdir, "ChangeLog"), 0644)
        except OSError:
            pass

        ## Write a pybindgen/version.py file containing the project version
        generate_version_py(force=True, path=srcdir)


        ## Package the api docs in a separate tarball

        # generate the docs first
        r = subprocess.Popen(["make", "html"], cwd='doc').wait()
        if r:
            raise SystemExit(r)

        apidocs = 'apidocs'
        if not os.path.isdir('doc/_build/html'):
            Logs.warn("Not creating docs archive: the `doc/_build/html' directory does not exist")
        else:
            zipper('doc/_build/html', "pybindgen-%s-docs.zip" % version)


        try:
            os.unlink('waf-light')
        except OSError:
            pass

        super(DistContext, self).execute() # -----------------------------

    def get_excl(self):
        return super(DistContext, self).get_excl() + ' *.zip doc/_build .shelf *.pstat'



def docs(ctx):
    "generate API documentation, using epydoc"
    generate_version_py(force=True)
    retval = subprocess.Popen(["make", "html"], cwd='doc').wait()
    if retval:
        Logs.error("make returned with code %i" % retval)
        raise SystemExit(2)


#
# FIXME: Remove this when upgrading beyond WAF 1.6.11; this here is
# only to fix a bug in WAF...
#
from waflib.Tools import python
from waflib import TaskGen
@TaskGen.feature('pyext')
@TaskGen.before_method('propagate_uselib_vars', 'apply_link')
@TaskGen.after_method('apply_bundle')
def init_pyext(self):
    """
    Change the values of *cshlib_PATTERN* and *cxxshlib_PATTERN* to remove the
    *lib* prefix from library names.
    """
    self.uselib = self.to_list(getattr(self, 'uselib', []))
    if not 'PYEXT' in self.uselib:
        self.uselib.append('PYEXT')
    # override shlib_PATTERN set by the osx module
    self.env['cshlib_PATTERN'] = self.env['cxxshlib_PATTERN'] = self.env['macbundle_PATTERN'] = self.env['pyext_PATTERN']

    try:
        if not self.install_path:
            return
    except AttributeError:
        self.install_path = '${PYTHONARCHDIR}'
