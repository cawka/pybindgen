#! /usr/bin/env python

import sys

import pybindgen
from pybindgen import (ReturnValue, Parameter, Module, Function, FileCodeSink)
from pybindgen import (CppMethod, CppConstructor, CppClass, Enum)


def my_module_gen(out_file):
    pybindgen.write_preamble(FileCodeSink(out_file))

    mod = Module('e')
    mod.add_include('"e.h"')

    E = mod.add_class('E', decref_method='Unref', incref_method='Ref')
    if 1:
        E.add_constructor(Function(ReturnValue.new("E*", caller_owns_return=True), "E::CreateWithRef", []))
    else:
        ## alternative:
        E.add_constructor(Function(ReturnValue.new("E*", caller_owns_return=False), "E::CreateWithoutRef", []))
    E.add_method(CppMethod(ReturnValue.new('void'), "Do", []))


    mod.generate(FileCodeSink(out_file) )

if __name__ == '__main__':
    my_module_gen(sys.stdout)
