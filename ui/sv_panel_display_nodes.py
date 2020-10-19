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

from pprint import pprint

DEBUG = False

_all_categories = {}  # cache for the node categories
_spawned_nodes = {}  # cache for the spawned nodes

constrainLayoutItems = [
    ("WIDTH", "Width", "", "", 0),
    ("HEIGHT", "Height", "", "", 1),
    ("ASPECT", "Aspect", "", "", 2)]


class Bin(object):
    ''' Container for items that keep a running sum '''

    def __init__(self):
        self.items = []
        self.width = 0
        self.height = 0

    def append(self, item):
        self.items.append(item)
        self.width = max(self.width, item[0][0])
        self.height += item[0][1]

    def __str__(self):
        ''' Printable representation '''
        return 'Bin(w/h=%d/%d, items=%s)' % (self.width, self.height, str(self.items))


def binpack(nodes, maxValue):
    if nodes:
        # print("there are %d nodes to bin pack" % (len(nodes)))
        for node in nodes:
            if node == None:
                print("WOW. a None node in the spawned nodes???")
    else:
        print("there are no nodes to bin pack")
        return []

    # first, sort the items in the decreasing height order
    items = [(node.dimensions, node.bl_idname, node) for node in nodes]
    items = sorted(items, key=lambda x: x[0][1], reverse=True)

    bins = []
    for item in items:
        # try to fit the item into the first bin that is not full
        for bin in bins:
            if bin.height + item[0][1] <= maxValue:  # bin not full ? => add item
                # print 'Adding', item, 'to', bin
                bin.append(item)
                break
        else:  # item didn't fit into any bin, start a new bin
            # print 'Making new bin for', item
            bin = Bin()
            bin.append(item)
            bins.append(bin)

    return bins


def cache_node_categories():
    ''' Cache category names, nodes and enum items '''
    if _all_categories:
        return

    node_categories = make_node_cats()
    categories = node_categories.keys()
    _all_categories["categories"] = {}
    _all_categories["categories"]["names"] = list(categories)
    _all_categories["categories"]["names"].append("All")
    _all_categories["categories"]["All"] = {}
    _all_categories["categories"]["All"]["nodes"] = []
    for category in categories:
        # print("adding category: ", category)
        nodes = [n for l in node_categories[category] for n in l]
        _all_categories["categories"][category] = {}
        _all_categories["categories"][category]["nodes"] = nodes
        _all_categories["categories"]["All"]["nodes"].extend(nodes)

    categoryItems = []
    categoryItems.append(("All", "All", "", 0))
    for i, category in enumerate(categories):
        categoryItem = (category, category.title(), "", i + 1)
        categoryItems.append(categoryItem)

    _all_categories["categories"]["items"] = categoryItems

    # pprint(_all_categories)


def get_category_names():
    cache_node_categories()
    return _all_categories["categories"]["names"]


def get_nodes_in_category(category):
    cache_node_categories()
    return _all_categories["categories"][category]["nodes"]


def get_spawned_nodes():
    if not _spawned_nodes:
        _spawned_nodes["main"] = []

    return _spawned_nodes["main"]


def add_spawned_node(context, name):
    if not _spawned_nodes:
        _spawned_nodes["main"] = []

    # print("adding spawned node: ", name)
    tree = context.space_data.edit_tree
    node = tree.nodes.new(name)

    _spawned_nodes["main"].append(node)

    return node


def remove_spawned_nodes(context):
    # print("remove_spawned_nodes called")
    if not _spawned_nodes:
        return

    nodes = _spawned_nodes["main"]

    tree = context.space_data.edit_tree

    if DEBUG:
        print("There are %d previously spawned nodes to remove" % (len(nodes)))

    for node in nodes:
        if DEBUG:
            print("removing spawned node")
        try:
            tree.nodes.remove(node)
        except:
            print("exception: failed to remove node from tree")

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


class SvDisplayNodePanelProperties(bpy.types.PropertyGroup):

    def navigate_category(self, direction):
        ''' Navigate to Prev or Next category '''
        if DEBUG:
            print("Navigate to PREV or NEXT category")

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
        return _all_categories["categories"]["items"]

    def arrange_nodes(self, context):
        ''' Arrange the nodes in current category (using bin-packing) '''
        try:
            nodes = get_spawned_nodes()
            if DEBUG:
                print("arranging %d nodes" % (len(nodes)))

            max_node_width = 0
            max_node_height = 0
            max_node_area = 0
            for node in nodes:
                w = node.dimensions[0]
                h = node.dimensions[1]
                max_node_width = max(max_node_width, w)
                max_node_height = max(max_node_height, h)
                max_node_area = max(max_node_height, w * h)

            if self.constrain_layout == "HEIGHT":
                bins = binpack(nodes, self.grid_height)

            elif self.constrain_layout == "WIDTH":
                # find the height that has total width less than max width
                found = False
                height = 100
                while not found:
                    bins = binpack(nodes, height)
                    # find max width for current layout
                    totalWidth = 0
                    for bin in bins:
                        totalWidth = totalWidth + bin.width

                    if DEBUG:
                        print("For height= %d total width = %d" % (height, totalWidth))

                    if totalWidth > max(max_node_width, self.grid_width):
                        height = height + 10
                        # try again with larger height
                    else:  # found it
                        found = True
            else:
                # find the height and width closest to the user aspect ratio
                target_aspect = self.grid_width / self.grid_height

                found = False
                height = 100
                while not found:
                    bins = binpack(nodes, height)
                    # find max width for current layout
                    totalWidth = 0
                    for bin in bins:
                        totalWidth = totalWidth + bin.width

                    if DEBUG:
                        print("For height= %d total width = %d" % (height, totalWidth))

                    current_aspect = totalWidth / height

                    if current_aspect > target_aspect:
                        height = height + 10
                        # try again with larger height
                    else:  # found it
                        found = True

            # arrange the nodes in the bins on the grid
            x = 0
            for bin in bins:
                max_x_width = max([item[0][0] for item in bin.items])
                y = 0
                for item in bin.items:
                    node_width = item[0][0]
                    node_height = item[0][1]
                    node_name = item[1]
                    node = item[2]
                    if DEBUG:
                        print("node = ", node_name, " : ", node_width, " x ", node_height)
                    node.location[0] = x + 0.5 * (max_x_width - node_width)
                    node.location[1] = y
                    y = y - node_height - self.grid_y_space
                x = x + max_x_width + self.grid_x_space
        except Exception as e:
            print('well.. some exception occurred:', str(e))

    def create_nodes(self, context):
        # remove the previously spawned nodes
        remove_spawned_nodes(context)

        node_names = get_nodes_in_category(self.category)

        if DEBUG:
            print("* current category : ", self.category)
            print("* nodes in category : ", node_names)

        N = len(node_names)

        # print('There are <%d> nodes in this category' % (N))
        if N == 0:
            return

        for i, node_name in enumerate(node_names):
            name = node_name
            if name == "separator":
                continue

            if DEBUG:
                print("Spawning Node %d : %s" % (i, name))

            node = add_spawned_node(context, name)

        # force redraw to update the node dimensions
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    def update_category(self, context):
        '''
            Spawn all nodes in the selected category
            note: all previously spawned nodes are removed first
        '''
        self.create_nodes(context)
        self.arrange_nodes(context)

    constrain_layout: EnumProperty(
        name="Constrain Layout", default="ASPECT",
        items=constrainLayoutItems, update=arrange_nodes)

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
        split = layout.split(factor=0.7, align=True)
        c1 = split.column(align=True)
        c2 = split.column(align=True)
        c1.prop(displayProps, "category", text="")
        row = c2.row(align=True)
        row.operator("sv.navigate_category", icon="PLAY_REVERSE", text=" ").direction = 0
        row.operator("sv.navigate_category", icon="PLAY", text=" ").direction = 1
        row = layout.row()
        row.prop(displayProps, 'constrain_layout', expand=True)
        col = layout.column(align=True)
        col.prop(displayProps, 'grid_width')
        col.prop(displayProps, 'grid_height')
        col = layout.column(align=True)
        col.prop(displayProps, 'grid_x_space')
        col.prop(displayProps, 'grid_y_space')


def register():
    bpy.utils.register_class(SvNavigateCategory)
    bpy.utils.register_class(SV_PT_DisplayNodesPanel)
    bpy.utils.register_class(SvDisplayNodePanelProperties)
    bpy.types.NodeTree.displayNodesProps = PointerProperty(
        name="displayNodesProps", type=SvDisplayNodePanelProperties)
    cache_node_categories()


def unregister():
    del bpy.types.NodeTree.displayNodesProps
    bpy.utils.unregister_class(SV_PT_DisplayNodesPanel)
    bpy.utils.unregister_class(SvDisplayNodePanelProperties)
    bpy.utils.unregister_class(SvNavigateCategory)
