# SPDX-License-Identifier: GPL-3.0-or-later
"""Descriptions and matching for socket-aware search. No graph traversal or bpy import."""

from dataclasses import dataclass
import re


# Only properties defining operations are expanded; other enums keep their defaults.
MODE_PROPERTIES = {
    'SvScalarMathNodeMK4': 'current_op',
    'SvVectorMathNodeMK3': 'current_op',
    'SvLogicNodeMK2': 'function_name',
    'SvColorMixNode': 'current_op',
    'ListFuncNode': 'func_',
    'SvMatrixMathNode': 'operation',
    'SvQuaternionMathNode': 'operation',
    'SvExScalarFieldMathNode': 'operation',
    'SvExVectorFieldMathNode': 'operation',
    'SvStringsToolsNodeMK2': 'current_op',
}
COMPONENT_MODES = {
    'Verts': 'vertex_mode', 'Edges': 'edge_mode', 'Faces': 'face_mode',
}
LOGIC_SEARCH_NAMES = {
    'LESS': 'Less Than (<)', 'BIG': 'Greater Than (>)',
    'EQUAL': 'Equal (==)', 'NOT_EQ': 'Not Equal (!=)',
    'LESS_EQ': 'Less Than or Equal (<=)', 'BIG_EQ': 'Greater Than or Equal (>=)',
}

# Central hints, deliberately small. Names are hints, not a replacement type system.
NAME_HINTS = {
    'edges': 'edges', 'edge': 'edges',
    'faces': 'faces', 'face': 'faces', 'polygons': 'faces', 'polygon': 'faces',
    'pols': 'faces', 'mask': 'mask', 'masks': 'mask',
}
GENERIC_NAMES = {'data', 'list', 'lists', 'item', 'items', 'datatrue', 'datafalse'}
NUMBER_NAMES = {
    'x', 'y', 'z', 'a', 'b', 'value', 'values', 'number', 'numbers',
    'factor', 'fac', 'amount', 'count', 'index', 'indices', 'radius',
    'size', 'length', 'angle', 'distance', 'scale', 'seed', 'level',
    'area', 'volume', 'perimeter', 'weight', 'weights',
}


@dataclass(frozen=True)
class SocketInfo:
    name: str
    socket_type: str
    is_output: bool
    identifier: str = ''
    index: int = 0
    semantic: str = ''
    policy: str = 'DefaultImplicitConversionPolicy'
    generic_output: bool = False


@dataclass(frozen=True)
class SearchEntry:
    node_type: str
    node_label: str
    operation: str
    settings: tuple
    socket: SocketInfo

    @property
    def label(self):
        parts = [self.node_label]
        if self.operation:
            parts.append(self.operation)
        parts.append(self.socket.name)
        return ' > '.join(parts)


def semantic_hint(name, socket_type, prop_name='', node_type=''):
    if socket_type != 'SvStringsSocket':
        return ''
    tokens = re.sub(r'([a-z])([A-Z])', r'\1 \2', name).lower()
    words = set(re.findall(r'[a-z]+', tokens))
    # "Face Mask" contains booleans, and "Edge Length" contains numbers.
    if words & {'mask', 'masks'}:
        return 'mask'
    if words & {'length', 'area', 'volume', 'perimeter', 'angle', 'count', 'distance'}:
        return 'number'
    for word, hint in NAME_HINTS.items():
        if word in words:
            return hint
    compact = ''.join(re.findall(r'[a-z]+', name.lower()))
    if compact in GENERIC_NAMES or words & {'data', 'list', 'items'}:
        return 'generic'
    if node_type in {'SvScalarMathNodeMK4', 'SvVectorMathNodeMK3'}:
        return 'number'
    if node_type == 'SvLogicNodeMK2':
        return 'mask'
    if prop_name or compact in NUMBER_NAMES:
        return 'number'
    return ''


def _adaptive_output_spec(node_class):
    """Inspect existing type-propagation code, without instantiating any node.

    The cached wrapper is installed below. No node registry or hand-maintained
    list of node IDs is needed. Fixed outputs of List Mask, Length, Index and
    Statistics are not mistaken for polymorphic data outputs.
    """
    import ast
    import inspect
    import textwrap

    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(node_class)))
    except (OSError, TypeError, SyntaxError):
        return frozenset(), frozenset(), False
    names, indices, dynamic = set(), set(), False
    list_module = any(part.startswith('list_') for part in node_class.__module__.split('.'))

    def output_collection(value):
        return (isinstance(value, ast.Attribute) and value.attr == 'outputs'
                and isinstance(value.value, ast.Name) and value.value.id == 'self')

    for method in tree.body[0].body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        assignments, aliases = {}, set()
        for statement in ast.walk(method):
            if isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        assignments.setdefault(target.id, []).append(statement.value)
            if isinstance(statement, ast.For) and output_collection(statement.iter):
                if isinstance(statement.target, ast.Name):
                    aliases.add(statement.target.id)

        def literals(value, seen=frozenset()):
            if isinstance(value, ast.Name) and value.id not in seen:
                result = []
                for assigned in assignments.get(value.id, ()):
                    result.extend(literals(assigned, seen | {value.id}))
                return result
            try:
                result = ast.literal_eval(value)
            except (ValueError, TypeError, SyntaxError):
                return []
            return list(result) if isinstance(result, (list, tuple)) else [result]

        for call in (node for node in ast.walk(method) if isinstance(node, ast.Call)):
            if (isinstance(call.func, ast.Name) and call.func.id == 'changable_sockets'
                    and len(call.args) >= 3):
                declared = [name for name in literals(call.args[2]) if isinstance(name, str)]
                names.update(declared)
                dynamic |= not bool(declared)
            elif (list_module and isinstance(call.func, ast.Attribute)
                  and call.func.attr == 'replace_socket'):
                receiver = call.func.value
                if isinstance(receiver, ast.Subscript) and output_collection(receiver.value):
                    keys = literals(receiver.slice)
                    for key in keys:
                        if isinstance(key, str):
                            names.add(key)
                        elif isinstance(key, int):
                            indices.add(key)
                    dynamic |= not bool(keys)
                elif isinstance(receiver, ast.Name) and receiver.id in aliases:
                    dynamic = True
    return frozenset(names), frozenset(indices), dynamic


from functools import lru_cache as _lru_cache
_adaptive_output_spec = _lru_cache(maxsize=512)(_adaptive_output_spec)


def _generic_output(socket, index):
    if not socket.is_output or socket.bl_idname != 'SvStringsSocket':
        return False
    names, indices, dynamic = _adaptive_output_spec(type(socket.node))
    if socket.name in names or index in indices:
        return True
    # Dynamic output names such as Data 0 / data[0]. The class must first have
    # proved that it propagates socket types; a name alone is insufficient.
    compact = re.sub(r'[^a-z]', '', socket.name.casefold())
    return dynamic and compact in {
        'data', 'item', 'items', 'other', 'list', 'slice', 'split',
        'first', 'last', 'middl', 'datatrue', 'datafalse',
    }


def describe_socket(socket, index):
    # Read only metadata, never sv_get(): searching must not evaluate a tree.
    return SocketInfo(
        socket.name, socket.bl_idname, socket.is_output,
        socket.identifier, index,
        semantic_hint(socket.name, socket.bl_idname,
                      getattr(socket, 'prop_name', ''), socket.node.bl_idname),
        getattr(socket, 'default_conversion_name', 'DefaultImplicitConversionPolicy'),
        _generic_output(socket, index),
    )


def socket_available(socket):
    return (socket.bl_idname not in {'NodeSocketVirtual', 'SvDummySocket'}
            and getattr(socket, 'enabled', True)
            and not getattr(socket, 'hide', False)
            and not getattr(socket, 'is_unavailable', False))


def connection_score(source, destination):
    """Lower is better; None means deliberately not suggested in version 1.

    Conservative: same types, generic list sockets and a small set of known
    conversions. Runtime values and custom per-link conversion policies are not
    inspected, so this cannot promise that a downstream node can process data.
    """
    if source.is_output == destination.is_output:
        return None
    output, input_ = (source, destination) if source.is_output else (destination, source)
    out_type, in_type = output.socket_type, input_.socket_type
    a, b = output.semantic, input_.semantic
    topology = {'edges', 'faces'}
    if out_type == in_type:
        if out_type == 'SvStringsSocket':
            if a in topology and b in topology and a != b:
                return None
            if (a in topology and b in {'number', 'mask'}) or (
                    b in topology and a in {'number', 'mask'}):
                return None
            if a and a == b and a != 'generic':
                return 0
            return 15 if 'generic' in {a, b} else 10
        return 0
    # Adaptive list data outputs can eventually carry the requested type when
    # their upstream input is connected. This is distinct from numeric Strings
    # outputs: Length, Index, masks and statistics remain excluded.
    if (out_type == 'SvStringsSocket' and output.generic_output
            and in_type not in {'SvLoopControlSocket', 'SvDummySocket'}):
        return 20
    # The default policy accepts arbitrary data into a Strings socket. Restrict
    # that suggestion to inputs with no more specific numeric/topology meaning.
    if in_type == 'SvStringsSocket' and b in {'', 'generic'}:
        return 20
    if input_.policy == 'LenientImplicitConversionPolicy':
        return 25
    conversions = {
        ('SvVerticesSocket', 'SvMatrixSocket'),
        ('SvMatrixSocket', 'SvVerticesSocket'),
        ('SvMatrixSocket', 'SvQuaternionSocket'),
        ('SvQuaternionSocket', 'SvMatrixSocket'),
        ('SvVerticesSocket', 'SvColorSocket'),
    }
    if (out_type, in_type) in conversions:
        return 30
    if (input_.policy == 'FieldImplicitConversionPolicy'
            and (out_type, in_type) in {
                ('SvMatrixSocket', 'SvVectorFieldSocket'),
                ('SvVerticesSocket', 'SvVectorFieldSocket'),
                ('SvStringsSocket', 'SvScalarFieldSocket')}):
        return 30 if a not in topology else None
    return None


def ranked_entries(source, entries):
    results = [(connection_score(source, item.socket), item) for item in entries]
    return [item for score, item in sorted(
        ((score, item) for score, item in results if score is not None),
        key=lambda pair: (pair[0], pair[1].label.casefold(), pair[1].socket.index))]


def enum_options(node, property_name):
    prop = node.bl_rna.properties[property_name]
    return [(item.identifier, item.name) for item in prop.enum_items if item.identifier]


def operation_variants(node):
    """Read the node's existing RNA enums; no duplicate list of operations."""
    if node.bl_idname == 'SvComponentAnalyzerNode':
        for component, label in enum_options(node, 'mode'):
            prop_name = COMPONENT_MODES.get(component)
            if prop_name:
                for operation, op_label in enum_options(node, prop_name):
                    yield ((('mode', component), (prop_name, operation)),
                           label + ' > ' + op_label)
    elif node.bl_idname in MODE_PROPERTIES:
        prop_name = MODE_PROPERTIES[node.bl_idname]
        for value, label in enum_options(node, prop_name):
            if node.bl_idname == 'SvLogicNodeMK2':
                label = LOGIC_SEARCH_NAMES.get(value, label)
            yield (((prop_name, value),), label)
    else:
        yield ((), '')


def configure_node(node, settings):
    for key, value in settings:
        setattr(node, key, value)
    # Some default values do not trigger a callback; normalize the socket layout.
    if node.bl_idname in {
            'SvScalarMathNodeMK4', 'SvVectorMathNodeMK3', 'SvMatrixMathNode',
            'SvQuaternionMathNode', 'SvStringsToolsNodeMK2'}:
        node.update_sockets()
    elif node.bl_idname in {'SvExScalarFieldMathNode', 'SvExVectorFieldMathNode'}:
        node.update_sockets(None)
    elif node.bl_idname == 'SvLogicNodeMK2':
        node.change_function(None)
    elif node.bl_idname == 'SvComponentAnalyzerNode':
        # Its callback hides unused outputs but doesn't unhide previously hidden
        # ones when a new operation uses more outputs. Normalize this new node.
        for socket in node.outputs:
            socket.hide = False
        node.update_mode(None)


def find_socket(node, info):
    sockets = node.outputs if info.is_output else node.inputs
    # Dynamic sockets may receive a new identifier on every creation. Match by
    # identifier, then by position AND name/type; never silently pick another.
    for socket in sockets:
        if (socket.identifier == info.identifier and socket.name == info.name
                and socket.bl_idname == info.socket_type and socket_available(socket)):
            return socket
    if info.index < len(sockets):
        socket = sockets[info.index]
        if (socket.name == info.name and socket.bl_idname == info.socket_type
                and socket_available(socket)):
            return socket
    return None

# ----------------------------------------------------------------------------
# Text relevance and aliases
# ----------------------------------------------------------------------------

import re
import unicodedata
from functools import lru_cache


_SYNONYMS = {
    'addition': 'add', 'sum': 'add', 'plus': 'add',
    'subtract': 'sub', 'subtraction': 'sub', 'minus': 'sub',
    'multiplication': 'mul', 'multiply': 'mul', 'mult': 'mul',
    'divide': 'div', 'division': 'div',
    'inverse': 'invert', 'inversion': 'invert',
    'average': 'avg', 'mean': 'avg',
    'minimum': 'min', 'maximum': 'max',
    'sine': 'sin', 'cosine': 'cos', 'tangent': 'tan',
    'verts': 'vertices', 'vers': 'vertices', 'vertex': 'vertices',
    'edgs': 'edges', 'edge': 'edges',
    'pols': 'polygons', 'polys': 'polygons', 'faces': 'polygons', 'face': 'polygons',
    'normalise': 'normalize', 'normalization': 'normalize',
    'remap': 'map',
}


@lru_cache(maxsize=8192)
def words(text):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = unicodedata.normalize('NFKD', text.casefold())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('square root', 'sqrt')
    return tuple(re.findall(r'[\w]+|[<>!=]+', text))


def _one_edit(a, b):
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        different = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        return len(different) <= 1 or (len(different) == 2
            and different[1] == different[0] + 1
            and a[different[0]] == b[different[1]] and a[different[1]] == b[different[0]])
    short, long = (a, b) if len(a) < len(b) else (b, a)
    return any(short == long[:i] + long[i + 1:] for i in range(len(long)))


@lru_cache(maxsize=32768)
def query_score(query, text):
    """Lower ranks first; None means no match. Allow one typo in longer words."""
    wanted, available = words(query), words(text)
    if not wanted:
        return 0
    total = 0
    for token in wanted:
        canonical = _SYNONYMS.get(token, token)
        best = None
        for word in available:
            if token == word:
                cost = 0
            elif canonical == _SYNONYMS.get(word, word):
                cost = 1
            elif word.startswith(token):
                cost = 2
            elif len(token) >= 2 and token in word:
                cost = 3
            elif len(token) >= 4 and len(word) >= 4 and _one_edit(token, word):
                cost = 5
            else:
                continue
            best = cost if best is None else min(best, cost)
        if best is None:
            return None
        total += best
    return total
