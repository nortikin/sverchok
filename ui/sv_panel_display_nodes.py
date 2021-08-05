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

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty, EnumProperty, PointerProperty

from sverchok.utils.context_managers import sv_preferences
from sverchok.menu import make_node_cats
from sverchok.settings import get_dpi_factor
from sverchok.utils.dummy_nodes import is_dependent
from pprint import pprint
from sverchok.utils.logging import debug
from collections import namedtuple

_node_category_cache = {}  # cache for the node categories
_spawned_nodes = {}  # cache for the spawned nodes

constrain_layout_items = [
    ("WIDTH", "Width", "", "ARROW_LEFTRIGHT", 0),
    ("HEIGHT", "Height", "", "EMPTY_SINGLE_ARROW", 1),
    ("ASPECT", "Aspect", "", "FULLSCREEN_ENTER", 2)]

node_alignment_items = [
    ("LEFT", "Left", "", "ALIGN_LEFT", 0),
    ("CENTER", "Center", "", "ALIGN_CENTER", 1),
    ("RIGHT", "Right", "", "ALIGN_RIGHT", 2)]

NodeItem = namedtuple('NodeItem', 'width height name node')


class Bin(object):
    ''' Container for items (of NodeType) that keep a running sum '''

    def __init__(self):  # start with an empty bin
        self.items = []
        self.width = 0   # current width of the bin
        self.height = 0  # current height of the bin

    def append(self, item):  # add item and update the bin's height and width
        self.items.append(item)
        self.width = max(self.width, item.width)
        self.height += item.height

    def __str__(self):
        ''' Printable representation '''
        return 'Bin(w/h=%d/%d, items=%s)' % (self.width, self.height, str(self.items))


def binpack(nodes, max_bin_height, spacing=0):
    ''' Add nodes to the bins of given max bin height and spacing '''
    if nodes:
        debug("There are %d nodes to bin pack" % (len(nodes)))
        for node in nodes:
            if node == None:
                debug("WARNING: a None node in the spawned nodes???")
    else:
        debug("WARNING: there are no nodes to bin pack!!!")
        return []

    scale = 1.0 / get_dpi_factor()  # dpi adjustment scale
    items = [NodeItem(node.dimensions.x * scale, node.dimensions.y * scale, node.bl_idname, node) for node in nodes]
    items = sorted(items, key=lambda item: item.height, reverse=True)

    bins = []
    for item in items:
        # try to fit the next item into the first bin that is not yet full
        for n, bin in enumerate(bins):  # check all the bins created so far
            if bin.height + len(bin.items) * spacing + item.height <= max_bin_height:
                # bin not full ? => add item
                debug("ADDING node <%s> to bin #%d" % (item.name, n))
                bin.append(item)
                break  # proceed to the next item
        else:  # item didn't fit into any bin ? => add it to a new bin
            debug('ADDING node <%s> to new bin' % (item.name))
            bin = Bin()
            bin.append(item)
            bins.append(bin)

    return bins


def should_display_node(name):
    if name == "separator" or '@' in name or name == "SvFormulaNodeMk5":
        # if name == "separator" or is_dependent(name) or '@' in name:
        return False
    else:
        return True


def cache_node_categories():
    """
    Cache category names, nodes and enum items

    Creates the structure:
    + categories
      + names      [ Generator, Surface, ... ]
      + items      [ ("Generator", "generator", "", 1) ...  ]
      + {category} [ All, Generators, Surfaces ...  ]
        + nodes    [ SvLine, SvTorus ... ]
    """

    if _node_category_cache:
        return

    node_categories = make_node_cats()
    categories = node_categories.keys()

    debug("categories = %s" % list(categories))

    _node_category_cache["categories"] = {}
    _node_category_cache["categories"]["names"] = list(categories)
    _node_category_cache["categories"]["names"].append("All")
    _node_category_cache["categories"]["All"] = {}
    _node_category_cache["categories"]["All"]["nodes"] = []
    for category in categories:
        debug("ADDING category: %s" % category)
        nodes = [n for l in node_categories[category] for n in l]
        nodes = list(filter(lambda node: should_display_node(node), nodes))
        _node_category_cache["categories"][category] = {}
        _node_category_cache["categories"][category]["nodes"] = nodes
        _node_category_cache["categories"]["All"]["nodes"].extend(nodes)

    category_items = []
    category_items.append(("All", "All", "", 0))
    for i, category in enumerate(categories):
        category_item = (category, category.title(), "", i + 1)
        category_items.append(category_item)

    _node_category_cache["categories"]["items"] = category_items

    # pprint(_node_category_cache)


def get_category_names():
    cache_node_categories()
    return _node_category_cache["categories"]["names"]


def get_nodes_in_category(category):
    cache_node_categories()
    return _node_category_cache["categories"][category]["nodes"]


def get_spawned_nodes():
    if not _spawned_nodes:
        _spawned_nodes["main"] = []

    return _spawned_nodes["main"]


def add_spawned_node(context, name):
    if not _spawned_nodes:
        _spawned_nodes["main"] = []

    debug("ADDING spawned node: %s" % name)

    tree = context.space_data.edit_tree

    try:
        node = tree.nodes.new(name)
        _spawned_nodes["main"].append(node)
    except:
        print("EXCEPTION: failed to spawn node with name: ", name)


def remove_spawned_nodes(context):
    # print("remove_spawned_nodes called")
    if not _spawned_nodes:
        return

    nodes = _spawned_nodes["main"]
    N = len(nodes)

    tree = context.space_data.edit_tree

    debug("There are %d previously spawned nodes to remove" % N)

    for i, node in enumerate(nodes):
        try:
            if node != None:
                debug("REMOVING spawned node %d of %d : %s" % (i+1, N, node.bl_idname))
            else:
                debug("REMOVING spawned node %d of %d : None" % (i+1, N))

        except:
            print("EXCEPTION: failed to remove spaned node (debug bad access)")

        try:
            tree.nodes.remove(node)
        except:
            print("EXCEPTION: failed to remove node from tree")

    del _spawned_nodes["main"]


class SvNavigateCategory(bpy.types.Operator):
    bl_label = "Navigate Category"
    bl_idname = "sv.navigate_category"
    bl_description = "Navigate Prev/Next category"

    direction: IntProperty(default=0)

    def execute(self, context):
        displayProps = context.space_data.node_tree.displayNodesProps
        displayProps.navigate_category(self.direction)
        self.report({'INFO'}, "Current category : " + displayProps.category)

        return {'FINISHED'}


class SvViewAllNodes(bpy.types.Operator):
    bl_label = "View All Nodes"
    bl_idname = "sv.view_all_nodes"
    bl_description = "View all the spawned nodes in the current category"

    def execute(self, context):
        bpy.ops.node.select_all(action="SELECT")
        bpy.ops.node.view_selected()
        for i in range(7):
            bpy.ops.view2d.zoom_in()
        # bpy.ops.node.select(deselect_all=True)

        return {'FINISHED'}


class SvDisplayNodePanelProperties(bpy.types.PropertyGroup):

    def navigate_category(self, direction):
        ''' Navigate to PREV or NEXT category '''
        debug("Navigate to PREV or NEXT category")

        categories = get_category_names()

        for i, category in enumerate(categories):
            if self.category == category:
                # prev or next category (cycle around)
                new_index = (i + 2 * direction - 1) % len(categories)
                new_category = categories[new_index]
                self.category = new_category
                break

    def category_items(self, context):
        ''' Get the items to display in the category enum property '''
        cache_node_categories()
        return _node_category_cache["categories"]["items"]

    def arrange_nodes(self, context):
        ''' Arrange the nodes in current category (using bin-packing) '''
        try:
            nodes = get_spawned_nodes()

            debug("ARRANGING %d nodes constrained by %s" % (len(nodes), self.constrain_layout))

            scale = 1.0 / get_dpi_factor()  # dpi adjustment scale

            max_node_width = max([node.dimensions.x * scale for node in nodes])

            if self.constrain_layout == "HEIGHT":
                # prioritize the layout height to fit all nodes => variable width
                bins = binpack(nodes, self.grid_height, self.grid_y_space)

            elif self.constrain_layout == "WIDTH":
                # find the height that gives the desired width
                max_tries = 11
                num_steps = 0
                min_h = 0
                max_h = 2 * (sum([node.dimensions.y * scale for node in nodes]) + (len(nodes)-1)*self.grid_height)
                while num_steps < max_tries:
                    num_steps = num_steps + 1

                    bin_height = 0.5 * (min_h + max_h)  # middle of the height interval

                    # get the packed bins for the next bin height
                    bins = binpack(nodes, bin_height, self.grid_y_space)

                    # find the total width for current bin layout
                    totalWidth = sum([bin.width for bin in bins])
                    # add the spacing between bins
                    totalWidth = totalWidth + self.grid_x_space * (len(bins)-1)

                    debug("{0} : min_h = {1:.2f} : max_h = {2:.2f}".format(num_steps, min_h, max_h))
                    debug("For bin height = %d total width = %d (%d bins)" % (bin_height, totalWidth, len(bins)))

                    delta = abs((self.grid_width - totalWidth)/self.grid_width)

                    debug("{0} : target = {1:.2f} : current = {2:.2f} : delta % = {3:.2f}".format(
                        num_steps,  self.grid_width, totalWidth,  delta))

                    if delta < 0.1:  # converged ?
                        break

                    else:  # not found ? => binary search
                        if self.grid_width < totalWidth:  # W < w (make h bigger)
                            min_h = bin_height
                        else:  # W > w (make h smaller)
                            max_h = bin_height

                debug("*** FOUND solution in %d steps" % num_steps)
                debug("* {} bins of height {} : width {} : space {} ".format(len(bins),
                                                                             int(bin_height),
                                                                             int(totalWidth),
                                                                             (len(bins)-1)*self.grid_x_space
                                                                             ))

            else:  # self.constrain_layout == "ASPECT"
                # find the height and width closest to the grid aspect ratio
                target_aspect = self.grid_width / self.grid_height

                max_tries = 11
                num_steps = 0
                min_h = 0
                max_h = 2 * sum([node.dimensions.y * scale for node in nodes])
                while num_steps < max_tries:
                    num_steps = num_steps + 1

                    bin_height = 0.5 * (min_h + max_h)  # middle of the height interval

                    # get the packed bins for the next bin height
                    bins = binpack(nodes, bin_height, self.grid_y_space)

                    # find the max width for current layout
                    totalWidth = sum([bin.width for bin in bins])
                    # add the spacing between bins
                    totalWidth = totalWidth + self.grid_x_space * (len(bins)-1)

                    debug("{0} : min_h = {1:.2f} : max_h = {2:.2f}".format(num_steps, min_h, max_h))
                    debug("For bin height = %d total width = %d" % (bin_height, totalWidth))

                    current_aspect = totalWidth / bin_height

                    delta_aspect = abs(current_aspect - target_aspect)

                    debug("{0} : target = {1:.2f} : current = {2:.2f} : delta = {3:.2f}".format(
                        num_steps, target_aspect, current_aspect, delta_aspect))

                    if delta_aspect < 0.1:  # converged ?
                        break

                    else:  # not found ? => binary search
                        if target_aspect < current_aspect:  # W/H < w/h (make h bigger)
                            min_h = bin_height
                        else:  # W/H > w/h (make h smaller)
                            max_h = bin_height

                debug("*** FOUND solution in %d steps" % num_steps)
                debug("* {} bins of height {} : width {} : space {} ".format(len(bins),
                                                                             int(bin_height),
                                                                             int(totalWidth),
                                                                             (len(bins)-1)*self.grid_x_space
                                                                             ))

            max_idname = max([len(node.bl_idname) for node in nodes])

            # ARRANGE the nodes in the bins on the grid
            x = 0
            for bin in bins:
                y = 0
                for item in bin.items:
                    node_width = item.width
                    node_height = item.height
                    node_name = item.name
                    node = item.node
                    if self.node_alignment == "LEFT":
                        node.location[0] = x
                    elif self.node_alignment == "RIGHT":
                        node.location[0] = x + (bin.width - node_width)
                    else:  # CENTER
                        node.location[0] = x + 0.5 * (bin.width - node_width)
                    node.location[1] = y

                    debug("node = {0:>{x}} : W, H ({1:.1f}, {2:.1f})  &  X, Y ({3:.1f}, {4:.1f})".format(
                        node_name,
                        node.dimensions.x * scale, node.dimensions.y * scale,
                        node.location.x, node.location.y,
                        x=max_idname))

                    y = y - (item.height + self.grid_y_space)
                x = x + (bin.width + self.grid_x_space)

        except Exception as e:
            print('EXCEPTION: arranging nodes failed:', str(e))

    def create_nodes(self, context):
        # remove the previously spawned nodes
        remove_spawned_nodes(context)

        node_names = get_nodes_in_category(self.category)
        node_names.sort(reverse=False)

        debug("* current category : %s" % self.category)
        debug("* nodes in category : %s" % node_names)

        N = len(node_names)

        debug('There are <%d> nodes in category <%s>' % (N, self.category))

        if N == 0:
            return

        for i, name in enumerate(node_names):
            if name == "separator":
                debug("SKIPPING separator node")
                continue
            if is_dependent(name):
                debug("SKIPPING dependent node %d of %d : %s" % (i+1, N, name))
                continue
            if '@' in name:
                debug("SKIPPING subcategory node: %s" % name)
                continue

            debug("SPAWNING node %d of %d : %s" % (i+1, N, name))

            add_spawned_node(context, name)

        # force redraw to update the node dimensions
        bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)
        bpy.context.area.tag_redraw()

    def update_category(self, context):
        """
        Spawn all nodes in the selected category
        note: all previously spawned nodes are removed first
        """
        self.create_nodes(context)
        self.arrange_nodes(context)

        # update the total/hidden node count (e.g. nodes with dependency are hidden)
        node_names = get_nodes_in_category(self.category)
        self.total_num_nodes = len(node_names)
        other_node_names = [name for name in node_names if is_dependent(name)]
        self.hidden_num_nodes = len(other_node_names)

    constrain_layout: EnumProperty(
        name="Constrain Layout", default="ASPECT",
        items=constrain_layout_items, update=arrange_nodes)

    node_alignment: EnumProperty(
        name="Node Alignment", default="CENTER",
        items=node_alignment_items, update=arrange_nodes)

    category: EnumProperty(
        name="Category",
        items=category_items, update=update_category)

    grid_width: IntProperty(
        name="Grid Width",
        default=700, update=arrange_nodes)

    grid_height: IntProperty(
        name="Grid Height",
        default=500, update=arrange_nodes)

    grid_x_space: IntProperty(
        name="Grid X spacing",
        default=20, update=arrange_nodes)

    grid_y_space: IntProperty(
        name="Grid Y spacing",
        default=20, update=arrange_nodes)

    total_num_nodes: IntProperty(
        name="Total number of nodes",
        description="Total number of nodes in the current category",
        default=0)

    hidden_num_nodes: IntProperty(
        name="Hidden number of nodes",
        description="Number of nodes hidden in the current category",
        default=0)


class SV_PT_DisplayNodesPanel(bpy.types.Panel):
    bl_idname = "SV_PT_DisplayNodesPanel"
    bl_label = "SV Display Nodes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    bl_order = 9

    @classmethod
    def poll(cls, context):
        # do not show if there is no node tree
        if not context.space_data.node_tree:
            return False

        # do not show if the tree is not a sverchock node tree
        if not context.space_data.tree_type == 'SverchCustomTreeType':
            return False

        # only show up if developer_mode has been set to True
        with sv_preferences() as prefs:
            return prefs.developer_mode

    def draw(self, context):
        layout = self.layout
        displayProps = context.space_data.node_tree.displayNodesProps
        box = layout.box()
        split = box.split(factor=0.7, align=True)
        c1 = split.column(align=True)
        c2 = split.column(align=True)
        c1.prop(displayProps, "category", text="")
        row = c2.row(align=True)
        row.operator("sv.navigate_category", icon="PLAY_REVERSE", text=" ").direction = 0
        row.operator("sv.navigate_category", icon="PLAY", text=" ").direction = 1
        row = box.row()
        row.operator("sv.view_all_nodes")
        # node count info
        label = "Total: {} - Shown: {} - Hidden: {}".format(displayProps.total_num_nodes,
                                                            displayProps.total_num_nodes -
                                                            displayProps.hidden_num_nodes,
                                                            displayProps.hidden_num_nodes)
        box.label(text=label)
        # grid settings
        box = layout.box()
        col = box.column(align=True)
        row = col.row()
        row.prop(displayProps, 'constrain_layout', expand=True)
        row = col.row()
        row.prop(displayProps, 'node_alignment', expand=True)
        col = box.column(align=True)
        col.prop(displayProps, 'grid_width')
        col.prop(displayProps, 'grid_height')
        col = box.column(align=True)
        col.prop(displayProps, 'grid_x_space')
        col.prop(displayProps, 'grid_y_space')


classes = [SvNavigateCategory, SvViewAllNodes, SV_PT_DisplayNodesPanel, SvDisplayNodePanelProperties]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.NodeTree.displayNodesProps = PointerProperty(
        name="displayNodesProps", type=SvDisplayNodePanelProperties)

    cache_node_categories()


def unregister():
    del bpy.types.NodeTree.displayNodesProps

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
