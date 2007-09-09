"""
C function wrapper
"""

from copy import copy

from typehandlers.base import ForwardWrapperBase
from typehandlers import codesink
import overloading


class Function(ForwardWrapperBase):
    """
    Class that generates a wrapper to a C function.
    """

    def __init__(self, return_value, function_name, parameters, docstring=None):
        """
        return_value -- the function return value
        function_name -- name of the C function
        parameters -- the function parameters
        """
        super(Function, self).__init__(
            return_value, parameters,
            parse_error_return="return NULL;",
            error_return="return NULL;")
        self._module = None
        self.function_name = function_name
        self.wrapper_base_name = None
        self.wrapper_actual_name = None
        self.docstring = docstring
        self.self_parameter_pystruct = None

    def clone(self):
        """Creates a semi-deep copy of this function wrapper.  The returned
        function wrapper clone contains copies of all parameters, so
        they can be modified at will.
        """
        func = Function(self.return_value,
                        self.function_name,
                        [copy(param) for param in self.parameters],
                        docstring=self.docstring)
        func._module = self._module
        func.wrapper_base_name = self.wrapper_base_name
        func.wrapper_actual_name = self.wrapper_actual_name
        return func

    def get_module(self):
        """Get the Module object this function belongs to"""
        return self._module
    def set_module(self, module):
        """Set the Module object this function belongs to"""
        self._module = module
        self.wrapper_base_name = "_wrap_%s%s" % (module.prefix, self.function_name)
    module = property(get_module, set_module)
    
    def generate_call(self):
        "virtual method implementation; do not call"
        if self._module.cpp_namespace_prefix:
            namespace = self._module.cpp_namespace_prefix + '::'
        else:
            namespace = ''
        if self.return_value.ctype == 'void':
            self.before_call.write_code(
                '%s%s(%s);' % (namespace, self.function_name,
                               ", ".join(self.call_params)))
        else:
            self.before_call.write_code(
                'retval = %s%s(%s);' % (namespace, self.function_name,
                                        ", ".join(self.call_params)))

    def _before_return_hook(self):
        "hook that post-processes parameters and check for custodian=<n> CppClass parameters"
        cppclass.implement_parameter_custodians(self)

    def generate(self, code_sink, wrapper_name=None, extra_wrapper_params=()):
        """
        Generates the wrapper code
        code_sink -- a CodeSink instance that will receive the generated code
        wrapper_name -- name of wrapper function
        """
        if wrapper_name is None:
            self.wrapper_actual_name = self.wrapper_base_name
        else:
            self.wrapper_actual_name = wrapper_name
        tmp_sink = codesink.MemoryCodeSink()
        self.generate_body(tmp_sink)
        code_sink.writeln("static PyObject *")

        python_args = ''
        flags = self.get_py_method_def_flags()
        if 'METH_VARARGS' in flags:
            if self.self_parameter_pystruct is None:
                self_param = 'PyObject * PYBINDGEN_UNUSED(dummy)'
            else:
                self_param = '%s *self' % self.self_parameter_pystruct
            python_args += "%s, PyObject *args" % self_param
            if 'METH_KEYWORDS' in flags:
                python_args += ", PyObject *kwargs"

        prototype_line = "%s(%s" % (self.wrapper_actual_name, python_args)
        if extra_wrapper_params:
            prototype_line += ", " + ", ".join(extra_wrapper_params)
        prototype_line += ')'
        code_sink.writeln(prototype_line)
        code_sink.writeln('{')
        code_sink.indent()
        tmp_sink.flush_to(code_sink)
        code_sink.unindent()
        code_sink.writeln('}')
        

    def get_py_method_def(self, name):
        """Returns an array element to use in a PyMethodDef table.
         Should only be called after code generation.

        name -- python function/method name
        """
        flags = self.get_py_method_def_flags()
        return "{\"%s\", (PyCFunction) %s, %s, %s }," % \
               (name, self.wrapper_actual_name, '|'.join(flags),
                (self.docstring is None and "NULL" or ('"'+self.docstring+'"')))


class OverloadedFunction(overloading.OverloadedWrapper):
    """Adds support for overloaded functions"""
    RETURN_TYPE = 'PyObject *'
    ERROR_RETURN = 'return NULL;'

import cppclass
