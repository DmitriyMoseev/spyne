
#
# spyne - Copyright (C) Spyne contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#

import logging
logger = logging.getLogger(__name__)

import os

from collections import defaultdict

from spyne.model import SimpleModel
from spyne.model.complex import XmlModifier
from spyne.model.complex import XmlData
from spyne.model.complex import XmlAttribute
from spyne.model.complex import Array
from spyne.model.complex import ComplexModelBase
from spyne.model.complex import ComplexModelMeta



class CodeGenerator(object):
    def __init__(self):
        self.imports = set()
        self.classes = set()
        self.pending = defaultdict(list)

    def gen_modifier(self, t):
        return '%s(%s)' % (t.get_type_name(), self.gen_dispatch(t.type))

    def gen_simple(self, t):
        return t.__name__

    def gen_complex(self, t):
        retval = []
        retval.append("""

# %r
class %s(_ComplexBase):
    _type_info = [""" % (t, t.get_type_name()))

        for k,v in t._type_info.items():
            if not issubclass(v, ComplexModelBase) or \
                            v.get_namespace() != self.tns or v in self.classes:
                retval.append("        ('%s', %s)," % (k, self.gen_dispatch(v)))
            else:
                self.pending[v.get_type_name()].append((k, t.get_type_name()))

        retval.append("    ]")

        self.classes.add(t)

        for k,orig_t in self.pending[t.get_type_name()]:
            retval.append('%s._type_info["%s"] = %s' % (orig_t, k, t.get_type_name()))

        return retval

    def gen_dispatch(self, t):
        if issubclass(t, XmlModifier):
            return self.gen_modifier(t)

        if issubclass(t, SimpleModel):
            return self.gen_simple(t)

        if t.get_namespace() == self.tns:
            return t.get_type_name()

        i = gen_fn_from_tns(t.get_namespace())
        self.imports.add(i)
        return "%s.%s" % (i, t.get_type_name())

    def genpy(self, tns, s):
        self.tns = tns

        retval = [u"""# encoding: utf8

# Automatically generated by Spyne. Modify at your own risk.

from spyne.model import *

    """,
    "", # imports
    """

class _ComplexBase(ComplexModelBase):
    __namespace__ = '%s'
    __metaclass__ = ComplexModelMeta""" % tns]

        for n, t in s.types.items():
            if issubclass(t, ComplexModelBase):
                retval.extend(self.gen_complex(t))
            else:
                retval.append('%s = %s' % (n, self.gen_dispatch(t)))

        for i in self.imports:
            retval.insert(1, "import %s" % i)

        retval.append("")
        return '\n'.join(retval)

def gen_fn_from_tns(tns):
    return tns \
        .replace('http://', '') \
        .replace('https://', '') \
        .replace('/', '') \
        .replace('.', '_') \
        .replace(':', '_') \
        .replace('#', '') \
        .replace('-', '_') \
