# SPDX-License-Identifier: GPL-3.0-or-later
"""Existing endpoints and conservative geometry bundles for Link Search.

No node evaluation, worker threads, or persistent graph cache. Existing links
are inspected only when opening tree search and when committing a connection.
"""

from dataclasses import dataclass, replace as replace_entry
import re

from sverchok.utils.sv_link_search import (
    connection_score, describe_socket, find_socket, socket_available,
)


_ports = {}
_VERTICES = {'vertices', 'verts', 'vers', 'vertex', 'vert', 'v'}
_EDGES = {'edges', 'edge', 'edgs', 'edg', 'e'}
_POLYGONS = {'polygons', 'polygon', 'faces', 'face', 'polys', 'poly', 'pols', 'pol', 'p'}
_COMBINED = {
    'edgpol', 'edgspols', 'edgespolys', 'edgespolygons', 'polygonsedges',
    'polyedge', 'edgepol', 'edgepoly', 'edgesfaces', 'facesedges', 'edgspol',
}


def geometry_role(info):
    name = re.sub(r'[^a-z]', '', info.name.casefold())
    if info.socket_type == 'SvVerticesSocket' and name in _VERTICES:
        return 'V'
    if info.socket_type == 'SvStringsSocket':
        if name in _EDGES:
            return 'E'
        if name in _POLYGONS:
            return 'P'
        if name in _COMBINED:
            return 'EP'
    return ''


def node_ports(node, is_output, free_inputs=False):
    sockets = node.outputs if is_output else node.inputs
    return tuple(describe_socket(socket, index) for index, socket in enumerate(sockets)
                 if socket_available(socket)
                 and (is_output or not free_inputs or not socket.is_linked))


class BundlePorts(tuple):
    """Plain socket descriptions plus occupancy for companion-link planning."""

    def __new__(cls, values, occupied=()):
        result = super().__new__(cls, values)
        result.occupied = tuple(occupied)
        return result


def bundle_ports(node, is_output, anchor=None, include_occupied=False):
    """Free companion inputs, the selected input, and all geometry anchors.

    Keep occupied Vertices ports in the ambiguity check. Their presence must
    not make a node with several geometry groups look like a single group.
    """
    ports = node_ports(node, is_output)
    if is_output:
        return ports
    if node.bl_idname == 'SvComponentAnalyzerNode':
        # Linked inputs can remain visible after an operation change. Read the
        # node's own operation signature, including after those links are freed.
        from sverchok.nodes.analyzer.component_analyzer import modes_dicts
        required = modes_dicts[node.mode][node.actual_mode().replace('_', ' ')][1]
        roles = {role for key, role in (('v', 'V'), ('e', 'E'), ('p', 'P')) if key in required}
        ports = tuple(info for info in ports if geometry_role(info) in roles)
    if include_occupied:
        return BundlePorts(ports)
    return BundlePorts(
        (info for info in ports if not node.inputs[info.index].is_linked
         or node.inputs[info.index] == anchor or geometry_role(info) == 'V'),
        occupied=(info for info in ports if node.inputs[info.index].is_linked))


def remember_ports(node, settings):
    _ports[node.bl_idname, tuple(settings)] = (
        node_ports(node, False), node_ports(node, True))


def clear_metadata():
    _ports.clear()


def known_signatures(node_type):
    return {tuple((info.is_output, info.name, info.socket_type)
                  for side in ports for info in side)
            for (registered, settings), ports in _ports.items() if registered == node_type}


def geometry_pairs(source, target, source_ports, target_ports):
    """Return descriptor pairs in output/input order, with the primary first.

    An unambiguous V, E, P or combined topology anchor enables companions.
    Hidden/unused operation inputs and occupied companion inputs are excluded.
    Explicit topology choices win over automatic Polygon/Edge preferences.
    """
    output, input_ = (source, target) if source.is_output else (target, source)
    pairs = [(output, input_)]
    out_role, in_role = geometry_role(output), geometry_role(input_)
    if (out_role, in_role) not in {
            ('V', 'V'), ('E', 'E'), ('P', 'P'), ('E', 'EP'), ('P', 'EP'), ('EP', 'EP')}:
        return pairs
    outputs, inputs = ((source_ports, target_ports) if source.is_output
                       else (target_ports, source_ports))

    def groups(ports):
        result = {}
        for info in ports:
            role = geometry_role(info)
            if role:
                result.setdefault(role, []).append(info)
        return result

    outs, ins = groups(outputs), groups(inputs)
    # Without one clear vertex channel on each node there is no reliable
    # geometry group to complete. Keep the explicitly requested link alone.
    if len(outs.get('V', ())) != 1 or len(ins.get('V', ())) != 1:
        return pairs
    if outs.get(out_role) != [output] or ins.get(in_role) != [input_]:
        return pairs
    occupied = getattr(inputs, 'occupied', ())
    for role in ('V', 'E', 'P'):
        if len(outs.get(role, ())) == 1 and len(ins.get(role, ())) == 1:
            target_info = ins[role][0]
            if target_info != input_ and target_info not in occupied:
                pairs.append((outs[role][0], target_info))
    # Treat combined inputs as a single topology channel, never two links to
    # the same input. Mixed signatures are ambiguous, so use dedicated ports.
    if (not ins.get('E') and not ins.get('P') and len(ins.get('EP', ())) == 1
            and ins['EP'][0] != input_ and ins['EP'][0] not in occupied):
        for role in ('P', 'E', 'EP'):
            candidates = outs.get(role, ())
            if candidates:
                if len(candidates) == 1:
                    pairs.append((candidates[0], ins['EP'][0]))
                break
    return pairs


def geometry_links(source, target, allow_primary_replace=False, replace_all=False):
    source_ports = bundle_ports(source.node, source.is_output, anchor=source, include_occupied=replace_all)
    target_ports = bundle_ports(target.node, target.is_output, anchor=target, include_occupied=replace_all)
    pairs = geometry_pairs(describe_socket(source, list(source.node.outputs if source.is_output else source.node.inputs).index(source)),
                           describe_socket(target, list(target.node.outputs if target.is_output else target.node.inputs).index(target)),
                           source_ports, target_ports)
    output_node, input_node = ((source.node, target.node) if source.is_output
                               else (target.node, source.node))
    primary_input = target if source.is_output else source
    result = []
    for out_info, in_info in pairs:
        out_socket = find_socket(output_node, out_info)
        in_socket = find_socket(input_node, in_info)
        if out_socket is None or in_socket is None:
            raise RuntimeError('A geometry socket changed or is unavailable')
        if in_socket.is_linked and not (replace_all or (allow_primary_replace and in_socket == primary_input)):
            raise RuntimeError('A geometry socket changed or is already connected')
        result.append((out_socket, in_socket))
    return result


def bundle_label(source, source_ports, entry):
    if getattr(entry, 'replace_all', False):
        source_ports = entry.source_ports
    if hasattr(entry, 'ports'):
        target_ports = entry.ports
    else:
        cached = _ports.get((entry.node_type, tuple(entry.settings)))
        if cached is None:
            return ''
        target_ports = cached[1 if entry.socket.is_output else 0]
    pairs = geometry_pairs(source, entry.socket, source_ports, target_ports)
    if len(pairs) < 2:
        return ''
    roles = []
    for output, input_ in pairs:
        role = geometry_role(input_)
        if role == 'EP':
            role = geometry_role(output)
            if role == 'EP':
                role = 'E/P'
        roles.append(role)
    order = {'V': 0, 'E': 1, 'P': 2, 'E/P': 3}
    return '+'.join(sorted(set(roles), key=lambda role: order.get(role, 4)))


@dataclass(frozen=True)
class ExistingSocketEntry:
    node_name: str
    instance_label: str
    node_label: str
    node_type: str
    node_pointer: int
    socket_pointer: int
    socket: object
    replace: bool = False
    input_links: tuple = ()
    ports: tuple = ()
    replace_all: bool = False
    source_ports: tuple = ()
    bundle_name: str = ''
    bundle_plan: tuple = ()
    bundle_inputs: tuple = ()

    @property
    def label(self):
        instance = self.node_name
        if self.instance_label and self.instance_label != instance:
            instance = '{} [{}]'.format(self.instance_label, instance)
        action = ' (Replace ' + self.bundle_name + ')' if self.replace_all else (' (Replace)' if self.replace else '')
        return instance + ' > ' + self.socket.name + action


def cycle_blocked_nodes(tree, source_node, source_output):
    """Ancestors when dragging an output, descendants when dragging an input."""
    adjacency = {}
    for link in tree.links:
        start, end = (link.to_node, link.from_node) if source_output else (link.from_node, link.to_node)
        adjacency.setdefault(start.as_pointer(), set()).add(end.as_pointer())
    blocked = {source_node.as_pointer()}
    pending = list(blocked)
    while pending:
        for pointer in adjacency.get(pending.pop(), ()):
            if pointer not in blocked:
                blocked.add(pointer)
                pending.append(pointer)
    return blocked


def existing_entries(tree, source):
    if not source.is_output and source.is_linked:
        return []
    sockets = source.node.outputs if source.is_output else source.node.inputs
    source_info = describe_socket(source, list(sockets).index(source))
    blocked = cycle_blocked_nodes(tree, source.node, source.is_output)
    results = []
    for node in tree.nodes:
        if node.as_pointer() in blocked:
            continue
        candidates = node.inputs if source.is_output else node.outputs
        for index, socket in enumerate(candidates):
            if not socket_available(socket):
                continue
            info = describe_socket(socket, index)
            score = connection_score(source_info, info)
            if score is None:
                continue
            search_label = node.bl_label
            if node.bl_idname == 'SvComponentAnalyzerNode':
                search_label += ' ' + node.mode + ' ' + node.actual_mode().replace('_', ' ')
            entry = ExistingSocketEntry(node.name, node.label, search_label,
                                        node.bl_idname, node.as_pointer(), socket.as_pointer(), info,
                                        replace=not socket.is_output and socket.is_linked,
                                        input_links=_input_link_ids(socket) if not socket.is_output else (),
                                        ports=bundle_ports(node, socket.is_output, anchor=socket))
            results.append((score, entry))
            full_pairs = geometry_links(source, socket, allow_primary_replace=entry.replace, replace_all=True)
            if len(full_pairs) > 1 and any(input_.is_linked for output, input_ in full_pairs[1:]):
                full = replace_entry(entry, replace_all=True,
                    ports=bundle_ports(node, socket.is_output, anchor=socket, include_occupied=True),
                    source_ports=bundle_ports(source.node, source.is_output, anchor=source, include_occupied=True),
                    bundle_plan=tuple((output.as_pointer(), input_.as_pointer()) for output, input_ in full_pairs),
                    bundle_inputs=tuple((input_.as_pointer(), _input_link_ids(input_)) for output, input_ in full_pairs))
                full = replace_entry(full, bundle_name=bundle_label(source_info, full.source_ports, full))
                results.append((score, full))
    return [entry for score, entry in sorted(results, key=lambda item: (
        item[0], item[1].replace_all, item[1].replace, item[1].label.casefold()))]


def _input_link_ids(socket):
    return tuple(sorted((link.from_node.as_pointer(), link.from_socket.as_pointer(),
                         link.to_node.as_pointer(), link.to_socket.as_pointer())
                        for link in socket.links))


def _update_connected_tree(tree, input_node):
    if callable(getattr(input_node, 'update', None)):
        input_node.update()
    tree.update()


def _apply_existing_links(tree, pairs, primary_input, replace=False, replace_inputs=()):
    """Change only this operation's links; restore replacements on failure."""
    replacing = {socket.as_pointer(): socket for socket in replace_inputs}
    if replace:
        replacing[primary_input.as_pointer()] = primary_input
    previous = [(link, link.from_socket, link.to_socket, link.is_muted)
                for socket in replacing.values() for link in socket.links]
    added = []
    removed = []
    try:
        with tree.init_tree():
            for link, output, input_, muted in previous:
                tree.links.remove(link)
                removed.append((output, input_, muted))
            for output, input_ in pairs:
                if input_.is_linked:
                    raise RuntimeError('A companion input is already connected')
                added.append(tree.links.new(output, input_))
        _update_connected_tree(tree, primary_input.node)
    except Exception:
        with tree.init_tree():
            for link in reversed(added):
                try:
                    tree.links.remove(link)
                except (ReferenceError, RuntimeError):
                    pass  # A dynamic socket update may already have removed it.
            for output, input_, muted in removed:
                restored = tree.links.new(output, input_, verify_limits=False)
                if muted:
                    restored.is_muted = True
        tree.update()
        raise


def connect_existing(tree, source, entry, single_link=False):
    node = tree.nodes.get(entry.node_name)
    if node is None or node.as_pointer() != entry.node_pointer:
        raise RuntimeError('The chosen node was removed or replaced')
    target = find_socket(node, entry.socket)
    if target is None or target.as_pointer() != entry.socket_pointer:
        raise RuntimeError('The chosen socket was removed or changed')
    output, input_ = (source, target) if source.is_output else (target, source)
    if not socket_available(source) or not socket_available(target):
        raise RuntimeError('The chosen socket is hidden or unavailable')
    if input_.is_linked:
        if not entry.replace or _input_link_ids(input_) != entry.input_links:
            raise RuntimeError('The connection changed after opening search; repeat the search')
    source_sockets = source.node.outputs if source.is_output else source.node.inputs
    if connection_score(describe_socket(source, list(source_sockets).index(source)),
                        describe_socket(target, entry.socket.index)) is None:
        raise RuntimeError('The socket types are no longer compatible')
    if node.as_pointer() in cycle_blocked_nodes(tree, source.node, source.is_output):
        raise RuntimeError('This connection would create a cycle')
    pairs = ([(output, input_)] if single_link else
             geometry_links(source, target, allow_primary_replace=entry.replace, replace_all=entry.replace_all))
    if entry.replace_all and not single_link:
        plan = tuple((out.as_pointer(), inp.as_pointer()) for out, inp in pairs)
        state = tuple((inp.as_pointer(), _input_link_ids(inp)) for out, inp in pairs)
        if plan != entry.bundle_plan or state != entry.bundle_inputs:
            raise RuntimeError('The geometry bundle changed after opening search; repeat the search')
    _apply_existing_links(tree, pairs, input_, replace=entry.replace,
                          replace_inputs=[inp for out, inp in pairs] if entry.replace_all and not single_link else ())
    return len(pairs)

# ----------------------------------------------------------------------------
# File-local groups and configured interfaces
# ----------------------------------------------------------------------------

from dataclasses import dataclass

from sverchok.utils.sv_link_search import SocketInfo, describe_socket, semantic_hint, socket_available


def interface_signature(tree):
    return tuple((item.identifier, item.name, item.in_out, item.socket_type)
                 for item in tree.interface.items_tree if item.item_type == 'SOCKET')


def group_allowed(group, destination):
    """Reject self containment and already-recursive group graphs."""
    stack = [(group, False)]
    visiting, complete = set(), set()
    while stack:
        tree, leaving = stack.pop()
        pointer = tree.as_pointer()
        if leaving:
            visiting.discard(pointer)
            complete.add(pointer)
            continue
        if pointer == destination.as_pointer() or pointer in visiting:
            return False
        if pointer in complete:
            continue
        visiting.add(pointer)
        stack.append((tree, True))
        for node in tree.nodes:
            nested = getattr(node, 'node_tree', None)
            if nested is not None and nested.bl_idname == 'SvGroupTree':
                stack.append((nested, False))
    return True


def _interface_ports(tree, interface_node=False):
    import bpy
    positions = {False: 0, True: 0}
    for identifier, name, direction, socket_type in interface_signature(tree):
        is_output = (direction == 'INPUT') if interface_node else (direction == 'OUTPUT')
        index = positions[is_output]
        positions[is_output] += 1
        cls = bpy.types.NodeSocket.bl_rna_get_subclass_py(socket_type)
        policy = getattr(cls, 'default_conversion_name', 'DefaultImplicitConversionPolicy')
        yield SocketInfo(name, socket_type, is_output, identifier, index,
                         semantic_hint(name, socket_type), policy)


@dataclass(frozen=True)
class GroupEntry:
    node_type: str
    node_label: str
    group_name: str
    group_pointer: int
    signature: tuple
    socket: SocketInfo
    ports: tuple = ()
    interface_node: bool = False
    triggers: str = ''
    operation: str = 'Group'
    settings: tuple = ()

    @property
    def label(self):
        return self.node_label + ' > ' + self.socket.name


def group_entries(destination):
    import bpy
    entries = []
    for group in bpy.data.node_groups:
        if group.bl_idname != 'SvGroupTree' or not group_allowed(group, destination):
            continue
        signature = interface_signature(group)
        description = getattr(group, 'description', '').splitlines()
        ports = tuple(_interface_ports(group))
        for info in ports:
            entries.append(GroupEntry('SvGroupTreeNode', 'Group: ' + group.name,
                group.name, group.as_pointer(), signature, info,
                ports=tuple(port for port in ports if port.is_output == info.is_output),
                triggers=description[0] if description else 'Group'))
    if destination.bl_idname == 'SvGroupTree':
        signature = interface_signature(destination)
        for info in _interface_ports(destination, interface_node=True):
            node_type = 'NodeGroupInput' if info.is_output else 'NodeGroupOutput'
            label = 'Group Input' if info.is_output else 'Group Output'
            entries.append(GroupEntry(node_type, label, destination.name,
                destination.as_pointer(), signature, info, interface_node=True,
                triggers='Current group interface'))
    return entries


def node_signature(node):
    return tuple((socket.is_output, socket.name, socket.bl_idname)
                 for sockets in (node.inputs, node.outputs) for socket in sockets
                 if socket_available(socket))


@dataclass(frozen=True)
class ConfiguredEntry:
    node_type: str
    node_label: str
    template_name: str
    template_pointer: int
    signature: tuple
    socket: SocketInfo
    ports: tuple = ()
    operation: str = 'Configured copy'
    settings: tuple = ()
    triggers: str = 'Copy configured interface'

    @property
    def label(self):
        return '{} [{} copy] > {}'.format(self.node_label, self.template_name, self.socket.name)


def configured_entries(tree):
    entries = []
    excluded = {'NodeFrame', 'NodeReroute', 'NodeGroupInput', 'NodeGroupOutput', 'SvGroupTreeNode'}
    for node in tree.nodes:
        if node.bl_idname in excluded:
            continue
        signature = node_signature(node)
        if not signature:
            continue
        defaults = known_signatures(node.bl_idname)
        if not defaults or signature in defaults:
            continue
        for sockets in (node.inputs, node.outputs):
            for index, socket in enumerate(sockets):
                if socket_available(socket):
                    entries.append(ConfiguredEntry(node.bl_idname, node.bl_label,
                        node.name, node.as_pointer(), signature, describe_socket(socket, index),
                        ports=tuple(describe_socket(port, i) for i, port in enumerate(sockets)
                                    if socket_available(port))))
    return entries


def create_context_node(context, tree, entry):
    import bpy
    if isinstance(entry, GroupEntry):
        group = bpy.data.node_groups.get(entry.group_name)
        if (group is None or group.as_pointer() != entry.group_pointer
                or interface_signature(group) != entry.signature):
            raise RuntimeError('The group interface changed; repeat the search')
        if entry.interface_node:
            if group != tree:
                raise RuntimeError('The edited group changed; repeat the search')
        elif not group_allowed(group, tree):
            raise RuntimeError('This group would create recursive containment')
        node = tree.nodes.new(entry.node_type)
        if not entry.interface_node:
            node.group_tree = group
            # The creator batches changes under init_tree(), suppressing the
            # wrapper update callback. Materialize this configured interface.
            node.sv_update()
        return node
    if isinstance(entry, ConfiguredEntry):
        template = tree.nodes.get(entry.template_name)
        if (template is None or template.as_pointer() != entry.template_pointer
                or node_signature(template) != entry.signature):
            raise RuntimeError('The configured template changed; repeat the search')
        before = {node.as_pointer() for node in tree.nodes}
        for node in tree.nodes:
            node.select = node == template
        tree.nodes.active = template
        result = bpy.ops.node.duplicate('EXEC_DEFAULT', keep_inputs=False, linked=False)
        if 'FINISHED' not in result:
            raise RuntimeError('Could not duplicate the configured template')
        node = tree.nodes.active
        if node is None or node.as_pointer() in before or node.bl_idname != entry.node_type:
            raise RuntimeError('The configured copy is unavailable')
        node.parent = None
        return node
    return None
