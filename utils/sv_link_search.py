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


def describe_socket(socket, index):
    # Read only metadata, never sv_get(): searching must not evaluate a tree.
    return SocketInfo(
        socket.name, socket.bl_idname, socket.is_output,
        socket.identifier, index,
        semantic_hint(socket.name, socket.bl_idname,
                      getattr(socket, 'prop_name', ''), socket.node.bl_idname),
        getattr(socket, 'default_conversion_name', 'DefaultImplicitConversionPolicy'),
    )


def socket_available(socket):
    return (getattr(socket, 'enabled', True)
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
    if node.bl_idname in {'SvScalarMathNodeMK4', 'SvVectorMathNodeMK3'}:
        node.update_sockets()
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
