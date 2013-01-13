import pdb
#encoding: utf-8
import copy
import re

class CppType(object):

    CTYPES = ["int", "long", "double", "float", "char", "void"]
    LIBCPPTYPES = ["vector", "string", "list", "pair"]

    def __init__(self, base_type, template_args = None, is_ptr=False,
                 is_ref=False, is_unsigned = False, enum_items=None):
        self.base_type =  "void" if base_type is None else base_type
        self.is_ptr = is_ptr
        self.is_ref = is_ref
        self.is_unsigned = is_unsigned
        self.is_enum = enum_items is not None
        self.enum_items = enum_items
        self.template_args = template_args and tuple(template_args)

    def transformed(self, typemap):
        copied = self.copy()
        copied._transform(typemap, 0)
        copied.check_for_recursion()
        return copied

    def _transform(self, typemap, indent):

        aliased_t = typemap.get(self.base_type)
        if aliased_t is not None:
            if self.template_args is not None:
                if aliased_t.template_args is not None:
                    raise Exception("invalid transform")
                self._overwrite_base_type(aliased_t)
            else:
                self._overwrite_base_type(aliased_t)
                self.template_args = aliased_t.template_args
        for t in self.template_args or []:
            t._transform(typemap, indent+1)

    def _overwrite_base_type(self, other):
        if self.is_ptr and other.is_ptr:
            raise Exception("double ptr alias not supported")
        if self.is_ref and other.is_ref:
            raise Exception("double ref alias not supported")
        if self.is_ptr and other.is_ref:
            raise Exception("mixing ptr and ref not supported")
        self.base_type = other.base_type
        self.is_ptr = self.is_ptr and other.is_ptr
        self.is_ref = self.is_ref and other.is_ref
        self.is_unsigned = self.is_unsigned and other.is_unsigned

    def __hash__(self):
        """ for using Types as dict keys """
        return hash(str(self))

    def __eq__(self, other):
        """ for using Types as dict keys """
        return str(self) == str(other)

    def copy(self):
        return copy.deepcopy(self)

    def __str__(self):
        unsigned = "unsigned" if self.is_unsigned else ""
        ptr  = "*" if self.is_ptr else ""
        ref  = "&" if self.is_ref else ""
        if ptr and ref:
            raise NotImplementedError("can not handel ref and ptr together")
        if self.template_args is not None:
            inner = "[%s]" % (",".join(str(t) for t in self.template_args))
        else:
            inner = ""
        result = "%s %s%s %s" % (unsigned, self.base_type, inner, ptr or ref)
        return result.strip() # if unsigned is "" or ptr is "" and ref is ""

    def check_for_recursion(self):
        try:
            self._check_for_recursion(set())
        except Exception, e:
            if str(e) != "recursion check failed":
                raise e
            raise Exception("re check for '%s' failed" % self)

    def _check_for_recursion(self, seen_base_types):
        if self.base_type in seen_base_types:
            raise Exception("recursion check failed")
        seen_base_types.add(self.base_type)
        for t in self.template_args or []:
            # copy is needed, else checking B[X,X] would fail
            t._check_for_recursion(seen_base_types.copy())

    @staticmethod
    def from_string(str_):
        base_type, t_str = re.match("([a-zA-Z ][a-zA-Z0-9 \*&]*)(\[.*\])?", str_).groups()
        if t_str is None:
            orig_for_error_message = base_type
            base_type = base_type.strip()
            unsigned, ptr, ref = False, False, False
            if base_type.startswith("unsigned"):
                unsigned = True
                base_type = base_type[8:].lstrip()
            if base_type.endswith("*"):
                ptr = True
                base_type= base_type[:-1].rstrip()
            elif base_type.endswith("&"):
                ref = True
                base_type= base_type[:-1].rstrip()
            if base_type.endswith("*") or base_type.endswith("&"):
                raise Exception("can not parse %s" % orig_for_error_message)
            if base_type.startswith("unsigned"):
                raise Exception("can not parse %s" % orig_for_error_message)
            if " " in base_type:
                raise Exception("can not parse %s" % orig_for_error_message)
            return CppType(base_type,
                           is_unsigned=unsigned,
                           is_ptr=ptr,
                           is_ref=ref)

        t_args = t_str[1:-1].split(",")
        t_types = [ CppType.from_string(t.strip()) for t in t_args ]
        return CppType(base_type, t_types)


def _x__cy_repr(type_):
    """ returns cython type representation """

    if type_.is_enum:
        rv = "enum "
    else:
        rv = ""
    if type_.base_type in CppType.CTYPES or \
        type_.base_type in CppType.LIBCPPTYPES:
        if type_.is_unsigned:
           rv += "unsigned "
        rv += type_.base_type
    else:
        rv += "_" + type_.base_type
    if type_.template_args is not None:
        rv += "[%s]" % ",".join(cy_repr(t) for t in type_.template_args)

    if type_.is_ptr:
        rv += " * "
    elif type_.is_ref:
        rv += " & "
    return rv


def _x_cpp_repr(type_):
    """ returns C++ type representation """

    if type_.is_enum:
        rv = "enum "
    else:
        rv = ""

    if type_.is_unsigned:
        rv += "unsigned "
    rv += type_.base_type
    if type_.template_args is not None:
        rv += "<%s>" % ",".join(cpp_repr(t) for t in type_.template_args)

    if type_.is_ptr:
        rv += " * "
    elif type_.is_ref:
        rv += " & "
    return rv


def _x__py_name(type_):
    """ returns Python representation, that is the name the module
        will expose to its users """
    return type_.base_type

def _x__py_type_for_cpp_type(type_):

    if type_.matches("char", is_ptr=True):
            return CppType("str")

    if type_.is_ptr:
        return None

    if type_.is_enum:
            return CppType("int")

    if type_.matches("long"):
            type_.base_type = "int" # preserve unsignedt...
            return type_

    if type_.matches("int"):
            return type_

    if type_.matches("bool"):
            return CppType("int")

    if type_.matches("float"):
            return type_

    if type_.matches("double"):
            return CppType("float")

    if type_.matches("string"):
            return CppType("str")

    if type_.matches("vector") or type_.matches("list"):
        return CppType("list")

    if type_.matches("pair"):
        return CppType("tuple")

    return type_

def __x_cy_decl(type_):

    type_ = py_type_for_cpp_type(type_)
    if type_ is None: return
    if type_.matches(None):
       return ""

    return ("unsigned " if type_.is_unsigned else "")  + type_.base_type + ("*" if type_.is_ptr  else "")


def _x__pysig_for_cpp_type(type_):

    pybase = py_type_for_cpp_type(type_).base_type
    if type_.template_args is None:
        return pybase

    else:
        pyargs = [pysig_for_cpp_type(t) for t in type_.template_args]
