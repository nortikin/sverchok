# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
EisenScript language support for Sverchok.

EisenScript is a procedural geometry scripting language based on L-systems.
It defines rules with transformations and primitives that generate
parametric 3D geometry through recursive rule expansion.

See: https://github.com/massivetrees/eisen
"""

from sverchok.utils.modules.eisenscript.ast import *
from sverchok.utils.modules.eisenscript.parser import parse
from sverchok.utils.modules.eisenscript.to_xml import (
    ast_to_xml,
    eisenscript_to_xml,
    xml_to_string,
)
from sverchok.utils.modules.eisenscript.from_xml import xml_to_ast
from sverchok.utils.modules.eisenscript.interpreter import (
    Interpreter,
    InterpreterResult,
)
