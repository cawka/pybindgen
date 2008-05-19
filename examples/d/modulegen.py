#! /usr/bin/env python

import sys

import pybindgen
from pybindgen import (ReturnValue, Parameter, Module, Function, FileCodeSink)
from pybindgen import (CppMethod, CppConstructor, CppClass, Enum)


def my_module_gen(out_file):
    pybindgen.write_preamble(FileCodeSink(out_file))

    mod = Module('d')
    mod.add_include('"d.h"')

    D = mod.add_class('D', free_function='DDestroy')
    D.add_instance_attribute('d', ReturnValue.new('bool'))
    D.add_function_as_constructor("DCreate", ReturnValue.new("D*", caller_owns_return=True), [])
    mod.add_function('DDoA', None, [Parameter.new('D*', 'd', transfer_ownership=False)])
    mod.add_function('DDoB', None, [Parameter.new('D&', 'd', direction=Parameter.DIRECTION_IN)])
    mod.add_function('DDoC', None, [Parameter.new('D&', 'd',
                                                  direction=Parameter.DIRECTION_IN,
                                                  is_const=True)])


    mod.generate(FileCodeSink(out_file) )

if __name__ == '__main__':
    my_module_gen(sys.stdout)
