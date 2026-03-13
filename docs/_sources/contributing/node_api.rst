========
Node API
========

This page claims to define all aspects of node creation. A brief introduction
to node creation is represented :doc:`on this page <add_new_node>`. Api
documentation of base class of all nodes can be found
`here <http://nortikin.github.io/sverchok/apidocs/sverchok/node_tree.html>`_.
Also read the `Alpha/Beta Node State`_ section before creating new node.

The Code of a new node should be created in a separate file. The file should be placed in
one of the available categories in the ``nodes`` folder.

Usually the structure of the file looks like:

.. code-block:: python

    # This file is part of project Sverchok. It's copyrighted by the contributors
    # recorded in the version control history of the file, available from
    # its original location https://github.com/nortikin/sverchok/commit/master
    #
    # SPDX-License-Identifier: GPL3
    # License-Filename: LICENSE

    import bpy

    class Node:
        ...

    def register():
        ...

    def unregister():
        ...


Class Definition
----------------

To create a node in Sverchok means to create a node class. The naming convention for
node classes is ``SV + name of the node + Node``

Standard Mix-ins for all node classes are
``sverchok.node_tree.SverchCustomTreeNode`` and ``bpy.types.Node``

Optional Mix-ins can be found in ``sverchok.utils.nodes_mixins``

The Node class documentation string serves two purposes:

  1. Adding key words for searching
  2. Adding a tool tip into the "Add Node" menu

There are two mandatory class variables:

  1. ``bl_idname`` should repeat the name of the class
  2. ``bl_label`` is the common name of the node, used in the Node header and in the "Add Node" menus 

.. tip::
   Node label can be defined dynamically in the ``draw_label`` method which
   should return a string.

Also the class can define an optional ``bl_icon`` variable with a string of a
standard Blender icon for the node. To find all standard icons the Icon
Viewer add-on can be used, which is included in Blender by default.

It's possible to define custom icons by including an ``sv_icon``
variable. All custom icons are stored in the ``sverchok.ui.icons`` folder in png
format. The variable value should repeat the png file name without extension
and in upper case.

.. code-block:: python

    class SvSetMeshAttributeNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: set mesh attribute
        Tooltip: It adds an attribute to a mesh
        """
        bl_idname = 'SvSetMeshAttributeNode'
        bl_label = 'Set Mesh Attribute'
        bl_icon = 'SORTALPHA'

        def draw_label(self):
            return "Label1" if self.prop else "Label2"


Creating Node Custom Properties
-------------------------------

Properties are created in the same way as other areas of Blender.
`Blender documentation <https://docs.blender.org/api/current/bpy.props.html>`_

After properties are added they can be used as node buttons or socket
properties. Also they can be used for internal usage but it's usually better to
use Custom properties (``node['prop_name']``) instead.

.. note::
   Using node properties for displaying on sockets is deprecated. Usually
   sockets can define their own properties.

To make a node react to property changes they should define the update argument.
If no extra logic is required the argument can be defined thus
``update=data_structure.updateNode``. 

In the case that a property change should cause sockets to be changed (created, removed..etc)
this can be done by creating a custom update method (usually in the node class) and passing a reference 
to it in the update argument of the property. 
The method expects to get the ``self`` and ``context`` parameters.

.. tip::
   Also there is a direct method to update the node but it can't be passed as
   an argument to the update parameter directly. Instead it's possible to use
   lambda expression:
   ``update=lambda self, context: self.process_node(context)``

.. code-block:: python

    class NodeClass:

        # ...

        def update_type(self, context):
            # some logic
            updateNode(self, context)

        some_mode: bpy.props.BoolProperty(update=updateNode)
        another_mode: bpy.props.BoolProperty(update=update_type)


Draft Properties
^^^^^^^^^^^^^^^^

Nodes can have draft properties which will be used instead of normal ones in
draft mode of a tree. Draft properties are defined in the same way as normal
ones. Also the node should use ``DraftMode`` mix-in, define
``draft_properties_mapping`` class variable with mapping between standard
properties and draft ones, and ``does_support_draft_mode`` method which should
return boolean value.

.. code-block:: python

    class NodeClass(sverchok.utils.nodes_mixins.DraftMode):

        # ...

        some_mode: bpy.props.BoolProperty(update=updateNode)
        some_mode_draft: bpy.props.BoolProperty(name='[D] Some Mode', update=updateNode)

        draft_properties_mapping = dict(some_mode = 'some_mode_draft')

        def does_support_draft_mode(self):
            return True


Enum Properties
^^^^^^^^^^^^^^^

Enums are created in the same way as in other Blender UI parts. In case Enums
are generated dynamically they always should be stored somewhere in Python
memory. There are `known cases`_ when Blender crashes during rendering when UI
expose dynamic enums which do not store their content.

.. _known cases: https://github.com/nortikin/sverchok/issues/4316

.. tip::
   There is now ``utils.handle_blender_data.keep_enum_reference`` decorator
   which can be used with dynamic enums. The decorator assign enum items to a
   Python variable what solves the problem above.

Enum items can have custom icons. Custom icons should be stored in the
``sverchok.ui.icons`` folder. To use custom icons the ``ui.sv_icons.custom_icon``
function should be used. It expects the name of the file in upper case without
extension and returns the index of the icon.


Dynamic Properties
^^^^^^^^^^^^^^^^^^

There are several nodes which generate dynamic properties - List Levels and
Switcher nodes. Dynamic properties are properties which are generated
depending on the size of input data. The best way to generate dynamic properties
is to use PropertyGroups together with Collection properties. Displaying
such properties is possible with for loop inside UI code. The right place to upgrade
properties is in the ``process`` method.

.. warning::

   Dynamic properties should always store values changed by the user, even if they
   are not displayed anymore. Otherwise it will lead to degradation of node
   tree "code". Otherwise, whenever properties are removed and restored a user would always
   be forced to repeat choices - this is quite unexpected and time consuming.

   In the future the generation of properties (currently done from inside ``process`` method) should
   move to some other method because the ``process`` method itself should become an
   abstract method.


Creating Node Buttons
---------------------

There are 4 places where a node can show its properties:

  1. Node interface
  2. Node tab of the Property panel of the Node editor
  3. Tool tab of the Property panel of the 3d Viewport editor
  4. Context menu

The Node interface is the appropriate place for adding properties which are used
regularly during work with a node tree. They should be defined in
``sv_draw_buttons`` method which expects ``context`` and ``layout`` arguments.

The Property panel of the Node editor is a good place for showing properties which
are rarely changed or should be changed only once. To make properties appear on that panel 
place them inside a ``sv_draw_buttons_ext`` method, this method also expects ``context`` and ``layout``
arguments.


.. code-block:: python

    class Node:
        value: IntProperty()
        mode: BoolProperty()

        def sv_draw_buttons(self, context, layout):
            layout.prop(self, "value")

        def sv_draw_buttons_ext(self, context, layout):
            layout.prop(self, "mode")


There are some nodes for which it is useful to see properties from the 3D Viewport editor.
Node with such properties should use ``utils.nodes_mixins.Show3DProperties``
mix-in. UI code should be placed in ``draw_buttons_3dpanel`` method. It expects
``layout`` argument and the optional ``in_menu`` argument which is False by default.
UI should obtain only one string. It's possible to show UI on several lines but
in this case ``utils.node_mixins.Popup3DMenu`` operator should be used. The
operator calls the same ``draw_buttons_3dpanel`` method but with ``in_menu``
argument as True.

.. code-block:: python

    class Node(Show3DProperties):

        def draw_buttons_3dpanel(self, layout, in_menu=None):
            if not in_menu:
                menu = layout.row(align=True).operator('node.popup_3d_menu', text=f'Show: "{self.label or self.name}"')
                menu.tree_name = self.id_data.name
                menu.node_name = self.name
            else:
                row.prop(self, 'mode1')
                row.prop(self, 'mode2')


Also optionally nodes can show their properties in the context menu. The Node class should
override the ``rclick_menu`` method which expects ``context`` and ``layout`` arguments.


Node Sockets
------------

Node sockets are created in ``sv_init`` method. ``new`` method of input and
output collections of sockets should be used. It expects name of a socket type
and name socket itself. These names are shown in UI and also usually are used
as identifiers. Whole list of available socket types can be found in
``core.sockets`` module. The new method returns newly created socket which
can be used for setting its extra parameters.

Usually sockets expose their default parameters. By default they are switched
off. The proper way to make to show its property is to assign True value to
``use_prop`` attribute of the socket. Default value can be changed in
``default_property`` attribute.

``SvStringsSocket`` type has two types of default values. Current type stored
in ``default_property_type`` attribute which can receive either 'float' or
'int' values. Default values are stored in ``default_float_property`` and
``default_int_property`` attributes.

.. code-block:: python

    class Node:
        def sv_init(self, context):
            socket = self.inputs.new('SvStringsSocket', "Size")
            socket.use_prop = True
            socket.default_float_property = 1.0
            self.outputs.new('SvVerticesSocket', "Verts")

.. tip::
   Alternative way of creating input sockets is using ``sv_new_input`` method.

   .. code-block:: python

      class Node:
          def sv_init(self, context):
              self.sv_new_input('SvStringsSocket', "Size", use_prop=True,
                                default_float_property=1)

Dynamic Sockets
^^^^^^^^^^^^^^^

Dynamic sockets are shown only on certain conditions. There are 3 categories
of them:

  1. Socket is shown if a node has certain properties.
  2. Socket is shown if other socket is connected.
  3. Socket is shown if node has appropriate input data.

There are many ways to show / hide sockets. First of all it's possible to use
Blender standard API for adding and removing sockets. Most resent nodes use
``hide_safe`` attribute of sockets. Disadvantage of this method is that sockets
are not really deleted and can be shown with `Ctrl+h` by user. The proper
way now is to use standard Blender ``enabled`` attribute.

When type of a socket should be changed it's possible to use
``data_structure.changable_sockets`` function or ``replace_socket`` method of a
socket. First function changes type of output sockets dependently on type of
a socket connected to input one. With the second method you have to define new
type of a socket by yourself.

.. warning::
   Change type of a socket is tricky part. Because it's related with removing,
   adding, moving sockets and links in a tree. Also it can be quite inefficient
   because Blender does not expose API which would allow to search connected
   neighbour sockets efficiently. But usually it's not a bottle neck in such
   cases.

To generate sockets upon changes of node properties is possible in ``update``
method of properties.

To generate sockets upon changes in node connections is possible in
``sv_update`` method of nodes. This method can be called quite intensively so
it's wise to expense resources carefully.

To generate sockets upon changes of input data of a node was quite controversial
idea. Now it's only used in Dictionary output node. The problem is that this can
easily lead to losses of user connections what breaks node setups. For example
in Geometry Nodes project there was a decision that sockets should be
independent to data layer. So to generate such nodes is not recommended now.
If there is no way but to have this functionality possible solution could be
to add a button to a node which would recreate sockets explicitly.

.. code-block:: python

    class Node:
        def mode_update(self, context):
            self.inputs['Value'].enabled = self.mode
            self.process_node()

        mode: BoolProperty(update=mode_update)

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Value").use_prop = True
            self.outputs.new('SvStringsSocket', "Value")

        def sv_update(self)
            data_structure.changable_sockets(self, "Value", ["Value"])

Socket Properties
^^^^^^^^^^^^^^^^^

label
  Expects a string which is used instead of a socket name in UI.

use_prop
  Expects boolean value. If true the socket will display its default property.

.. image:: https://user-images.githubusercontent.com/28003269/180741280-683987fa-e10c-47e1-91e0-807311697fea.png
   :align: right

show_property_type (SvStringsSocket)
  It adds icon to switch default type of the string socket

custom_draw
  Expects name of a method of the node of the socket. If defined the method
  will be used draw UI elements for the socket.

  .. code-block:: python

     class Node:
         def custom_draw_socket(self, socket, context, layout):
             layout.prop(self, "node_property")


quick_link_to_node
  Expects a string of node `bl_idname``. This will add an operator which can
  create quick link to the given node.

link_menu_handler
  Expects a string of class name defined inside node of the socket. This only
  works when displaying quick links is in multiple values mode. In the class
  its possible to define extra nodes for connections. This is analog of
  creating nodes during dragging a link from a socket in Blender 3.1.

  .. code-block:: python

     class Node:
         class MenuHandler:
             @classmethod
             def get_items(cls, socket, context):
                 """Return list of extra options for the menu"""
                 return [('KEY', "Name", "Description"), ]

             @classmethod
             def on_selected(cls, tree, node, socket, key, context):
                 """In this method the node should be created and linked to the socket"""
                 if key == 'KEY':
                     print("Hello world!")

prop_name
  Expects name of a node property to display in UI of the socket.

  .. warning::
     This is deprecated way to display default properties for sockets. Use
     ``use_prop`` attribute instead.

object_kinds (SvObjectSocket)
  Expects string value of object type to socket to display as possible choice.
  Its also possible to pass several types which should be separate by only
  comma: ‘MESH,CURVE,SURFACE,META,FONT,VOLUME,EMPTY,CAMERA,LIGHT’

expanded (SvVerticesSocket, SvQuaternionSocket, SvColorSocket)
  Expects boolean value. It's responsible for the way of the socket to display
  the socket value.

Socket Vectorization Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Vectorization system is on
:ref:`experimental stage <experimental_vectorization>`

is_mandatory
  Expects boolean value. If True the node can't perform its function without
  data from the socket.

nesting_level
  Expects integer value. Describes the expected shape of input data.

  * 3 for vectors lists (Default for Vertices Socket)
  * 2 for number lists (Default)
  * 1 for single item

default_mode
  Expects one of the next strings:

  * 'NONE' to leave empty
  * 'EMPTY_LIST' for [[]] (Default)
  * 'MATRIX' for Matrix()
  * 'MASK' for [[True]]

pre_processing
  Expects one of the next strings:

  * 'ONE_ITEM' for values like the number of subdivision (one value per object).
    It will match one value per object independently if the list is [[1,2]]
    or [[1],[2]]. In case of more complex inputs no preprocessing will be made.
  * 'NONE' not doing any preprocessing. (Default)


Business logic
--------------

The main work of the node is happening inside ``process`` method which does
not expect any arguments.

The whole process can be split into 3 steps:

  1. Extract data from sockets.
  2. Handle the data.
  3. Record result into output sockets.

.. note::
   In future it is planned to convert the method into abstract one. In this case
   a node will get parameters via some arguments.

For reading data from sockets their ``sv_get`` method can be used.
It has tow important parameters. ``default`` parameter expects any
data which will be returned in case if input socket does not have any external
data. ``deepcopy`` parameter expects False value if input data is not modified
by the node. The node can work quite more efficient if deepcopy is False. But
if a node do modify the data the parameter should be with default value,
otherwise other nodes which use the same data will get unexpected results.

.. note::
   Many nodes on this stage also do such optimization as checking connection of
   their output sockets and if they are not connected cancel their father
   execution. Really it's not recommended in new nodes. The right place for
   such optimization is execution system.

After handling input data ``sv_set`` method of sockets can be used for
saving result. It expects only one parameter - data.

.. code-block:: python

    class Node:
        def process(self):
            data = self.inputs['My Socket'].sv_get(default=[], deepcopy=False)

            result = handle_data(data)

            self.outputs['My Socket'].sv_set(result)

.. important::
   Sometimes node does not have enough data to perform its function in this case
   it should pass available data to output sockets unmodified. It's important
   because the whole node tree will stop working otherwise.

.. tip::
   Also ``sv_get`` method has third parameter - ``implicit_conversions``. It
   expects one of the values of ``core.socket_conversions.ConversionPolicies``
   enum. It's purpose is to convert format of output data of previous nodes to
   format of input data of current node. For example via Conversion Policy
   conversion simple values to vectors is happening. Usually such settings are
   applied globally to all sockets but sometimes it can be useful to override
   them via the parameter (not single node do this currently though).

Data vectorization
^^^^^^^^^^^^^^^^^^

All nodes should be designed in a way that they can handle not only one object
but multiple of them. That is called vectorization in Sverchok. For example if
a node works with vertices of an object it should handle list of lists of
vertices.

It can happen that some input data has one number of objects and another
input data has another number of objects. In this case a node should perform
data matching operation. Usually it means that data with shorter number of
objects should repeat them to match them to number of objects of the longest
data. Repeating objects usually happens in two ways.

  1. Last object fills all missing ones. For example: ``[1, 2, 3]`` will be
     converted into ``[1, 2, 3, 3 ,3 ,3]`` if number of required objects is 6.
  2. Objects start to repeat from start of a list (cycling). For example:
     ``[1, 2, 3]`` will be converted into ``[1, 2, 3, 1, 2, 3]`` if number of
     required objects is 6.

Usually number of objects is determined by the longest input data. Sometimes
the number can be limited by some particular input in case it does not have
sense to repeat it.

There are helping functions / generators to perform data matching in
``data_structure`` module. Generators are preferable before functions.

.. code-block:: python

    class Node:
        def process(self):
            params = [s.sv_get(deepcopy=False, default=[[]]) for s in self.inputs]
            max_len = max(map(len, params))
            out = []
            for _, v, e, f, fd, m, t, d  in zip(range(max_len), *make_repeaters(params)):
                out.append(handle_data(v, f, t, d, e, fd, m))

            out_verts, out_edges, out_faces, out_face_data, out_mask = zip(*out)
            self.outputs['Verts'].sv_set(out_verts)
            self.outputs['Edges'].sv_set(out_edges)
            self.outputs['Faces'].sv_set(out_faces)
            self.outputs['Face data'].sv_set(out_face_data)
            self.outputs['Mask'].sv_set(out_mask)

.. _experimental_vectorization:

.. note::
   There are two experimental approaches to automate data matching. One can
   be found in ``utils.nodes_mixins.recursive_nodes`` and another in
   ``utils.vectorize`` modules. Both of them can handle not only list of
   objects but and nested to each other lists of objects with arbitrary
   nestedness and shape. It leads to two disadvantages:

     1. It make the code difficult to understand, to support and to debug.
        Even for user its more difficult to handle data with complex shape.
     2. Vectorization itself is very expensive thing because it uses pure
        Python loops. And such complex vectorization system is even more
        expensive.

   Also any vectorization can be performed with loop nodes which can create
   more clear representation data handling. So this modules should prove first
   which problems they are going to solve which can't be tackled in another way
   and so they can't be recommended for use for now.

.. note::
   In future vectorization should leave the nodes area and arrive to execution
   system. In this case nodes only have to add information to sockets to give to
   execution system to know how to match data.

Data structure
^^^^^^^^^^^^^^

Sverchok can operate on vide variation of data structures. The most important
one is mesh data structure. Sverchok uses *Face-vertex* representation of them.
Representation is a simple list of vertices, and a set of edges and polygons
that point to the vertices they use.

.. note::
   Usually list of vertices, edges and polygons are ordinary Python lists.
   Vertices can be represented as numpy arrays. If a node is generator it can
   have an option in which format to output vertices. If a node has vertices as
   an input it should output them in the same format in which they came.

   For edges and polygons it was decided not to use numpy arrays due little
   performance benefit and in case of n-gons it's not trivial how to store and
   handle them as numpy arrays.

.. code-block:: python

    # simple triangle
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    edges = [(0, 1), (1, 2), (0, 2)]
    polygons = [[0, 1, 2], ]

For vertices there is ``SvVerticesSocket`` socket type. For edges and faces
there is ``SvStringsSocket`` socket type. The last one is also used for lists
of numbers (floats, integers).

For storing mesh attributes Sverchok uses simple numbers or more complex data
as colors, texts and vectors. Such lists should store values per mesh element.
Color data passes via ``SvColorSocket``, number via ``SvStringsSocket``, strings
via ``SvTextSocket``.

For orienting meshes in space Blender Matrix and Quaternions are used.
Historically they has next format - ``[matrix, matrix, ...]`` but this format
can move only whole mesh. For this reason some nodes also support such format -
``[[matrix, matrix, ...], [matrix, ...]]``. In this cases matrix can be used
for moving separate elements of a mesh. Socket types for them are
``SvMatrixSocket`` and ``SvQuaternionSocket``.

Sverchok has family of mathematical objects such as Curves, Surfaces,
Feilds, Solids. All of them, except Solids, are defined as Python classes.
Solids are used from FreeCAD library. They all have dedicated to them sockets
in the ``core.sockets`` module.

Also there are some other data structures as Blender objects, File paths, svg,
Pulga forces, Dictionaries.

.. note::
   Dictionary has rather experimental stage and should prove in which area
   they can be used efficiently.

BMesh data structure
^^^^^^^^^^^^^^^^^^^^

For performing operations over geometry it's possible to create you own
algorithms. But also Blender has a library of some basic geometry operations.
This library uses special BMesh data structure. It's similar to Half-edge
data structure. To convert data from Sverchok format to BMesh and vice versa
there is ``utils.sv_bmesh_utils`` module.

Tests
^^^^^

Ideally nodes should go with some tests. But currently there is no framework
for automation of tests creation. So it's optional now. More about tests in the
separate section :doc:`testing`.

Performance
^^^^^^^^^^^

.. figure::  https://user-images.githubusercontent.com/28003269/167471557-e10fb5f4-af31-47a2-86f2-e826a253fd06.png
   :align: right
   :width: 300px

   Dot graph https://github.com/jrfonseca/gprof2dot

.. figure:: https://user-images.githubusercontent.com/28003269/167472803-225b8fd9-4584-4eb5-b7e8-f0ce9695f604.png
   :align: right
   :width: 300px

   Icicle style https://github.com/jiffyclub/snakeviz

Performance of the nodes is very important and quite a big problem in Sverchok
currently. Using pure Python is quite weak solution. First step to improve
performance is to rewrite code with numpy library if it's possible.

Sverchok has tool with UI to measure performance of separate nodes or a whole
tree. It's located in the Tree Profiling panel in Sverchok tab of Property
panel. It only appears if the Developer mode is enabled in the add-on settings.

In Node Tree Update mode the performance of a whole tree will be measured. To
measure performance of separate nodes their process method should be marked with
``utils.profile.profile`` decorator.

After measuring the performance the result can be outputted in the console which
is standard output of cProfile Python module. Also the result can be saved in
separate file which can be visualized with another tools.

Printing / Logging
^^^^^^^^^^^^^^^^^^

.. figure:: https://user-images.githubusercontent.com/28003269/180702647-c25d8b58-ed2d-4a7b-98ce-d6aaa594d475.png
   :align: right
   :width: 400px

   Logging level can be set in the add-on settings.

Printing and profiling are very expensive operations. Also console can fastly
turn into unreadable mess. So it's better to avoid using them inside node code.
During debugging it's valid to use print function but it should removed in the
end.

Usually logging can be don in some operators in this case you can use loggers
from ``utils.logging`` module or by using ``node.debug``, ``node.info`` and
other aliases.

If a node rises an error it will appear in console in next format: ``data and
time [logging level] module name:line number : error name``

Traceback is switch off for all logging levels except debug one. If you need it
make sure that you have appropriate logging level in the settings.

Node Registration
-----------------

After a node was created it should be registered to appear in Blender interface.
It can be done in function with ``register`` name in the same module with node
class. This function will be called whenever the add-on is enabled. For the
class registration standard Blender function is used.

.. code-block:: python

    class Node:
        ...

    def register():
        bpy.utils.register_class(Node)

Also node should be placed in some existing category by adding its ``bl_idname``
to the ``index.md`` file.

.. tip::
   In case new node should obtain new category it's possible to create it in
   ``ui/nodeview_space_menu`` module. Here is example of adding a category
   with name Test.

   .. code-block:: python

      menu_structure = [
          ...,
          ["NODEVIEW_MT_AddTest", 'ICON_NAME'],
          ...,
          ]

      classes = [
          ...,
          make_class('Test', "Test"),
          ...,
          ]

   Also the category should be added to ``index.md`` file similar to other
   categories.

When the add-on is disabled or reloaded its classes should be unregister. To
unregister a node is possible in function with name ``unregister`` in the same
module with Node class.


Documentation
-------------

When new node is added it's strongly recommended to add its documentation.
Without it, in most cases, users will hardly able to use the node and also
it can be difficult to distinguish a bug because the desired behaviour was not
proclaimed.

To add documentation to a node file with documentation (name_of_the_node.rst)
should be added to the ``docs.nodes.node_category`` folder.

For generating documentation `Sphinx library`_ is used. Also
`Read the Docs`_ Sphinx theme is used. So both libraries should be available
if you want to build documentation locally. There is ``docs/make.bat`` file
which builds the documentation into ``docs/_build`` (excluded from git) folder.

.. _Sphinx library: https://www.sphinx-doc.org/en/master/
.. _Read the Docs: https://github.com/readthedocs/sphinx_rtd_theme

There is action which will automatically build and publish documentation on the
next address - http://nortikin.github.io/sverchok/docs/main.html, whenever
changes will be introduced in master on GitHub.


Animation
---------

There are nodes which should be updated upon frame change. Usually they read
some data from a Blender scene. To make a node to be updated every frame it's
enough to override ``is_animation_dependent`` node attribute with True value.

.. note::
   Buttons should be displayed via ``sv_draw_buttons`` method otherwise the
   node won't display extra property which can be used by user to disable
   updates for the current node.


Muting
------

Blender gives opportunity to temporary switch off any node in a tree. In this
case its input data paths through the node without any modifications toward next
nodes. Bas node class has default ``sv_internal_links`` property to determine
how the data should path a node. If default behaviour does not fit into a node
logic it can override the property. The property should return iterable tuple
of input and output sockets of the node.

.. note::
   Before implementing your own ``sv_internal_links`` property have a look at
   the ``utils/nodes_mixins/sockets_config`` module. It has implementations
   of the property for some basic node types.

.. warning::
   Unfortunately the ``sv_internal_links`` property does not change how
   internal links will be displayed in UI. Currently it's limitation of Blender
   which API does not give control of displaying internal links properly.


Nodes With Dependencies
-----------------------

Nodes can use some external library which can be installed manually by user from
Extra Nodes tab in the add-on settings. When a node uses external library and
it is not installed the node should add itself into a list of dummy nodes.
Dummy nodes do nothing but display information that a library is not installed.

.. figure:: https://user-images.githubusercontent.com/10011941/85948219-e3957800-b94f-11ea-9040-d1e3009dc016.png
   :align: right
   :width: 250px

Also when library is not installed the nodes should not register their selves.
Also such nodes dose not apper in the Add node menu.

.. code-block:: python
   
   from sverchok.dependencies import FreeCAD

   if FreeCAD is None:
       utils.dummy_nodes.add_dummy('SvSolidAreaNode', 'Solid Area', 'FreeCAD')
   
   class SvSolidAreaNode:
       ...
   
   def register():
       if FreeCAD is not None:
           bpy.utils.register_class(SvSolidAreaNode)

The dependencies is a special module from which all dependent library should be
imported. If a library is not available instead of NoModuleFound error the 
None value will be imported. The ``add_dummy`` function expects ``bl_idname`` 
of the node, its name and name of the library on which the node is dependent.

.. tip::
   There is alternative and more simple way to handle the nodes with missing
   dependencies. They should be registered as regular nodes but in their process
   method they should raise an Error with a message which points that some
   library should be installed to make the node to work.

   The approach can handle the case when node is not dependent on a library
   except in some of its modes.


JSON Import / Export
--------------------

Sverchok has special format for sharing node trees and saving them into presets.
In most cases nodes developers should not prepare their node to make them work
with JSON import / export system. What is important to know:

- Standard json export saves all properties including collection and nesting
  collection and pointers. 
- For now only data block names of pointer properties will be saved. 
- During import pointers will be searched in current scene, if there is no data
  blocks with current name nothing will be assigned to the pointer.
- It is strongly not recommended to save pointers for viewer nodes. For skipping
  property to save use: `BoolProperty(options={'SKIP_SAVE'}` it will impact only
  on unsaving property into json file.
- Custom properties (which uses square bracket interface) are ignored.
- It is possible to add `save_to_json(node_data: dict)` and
  `load_from_json(node_data: dict, import_version: float)` method to a node for
  adding extra logic into import export, but it's better to avoid using it.
  It's difficult to add changes into nodes using this methods and support import
  previous JSON files.


Upgrade Node
------------

It's possible to improve existing nodes but it should be done carefully, without
breaking existing layouts. It can be done in two ways:

Improve existing node
^^^^^^^^^^^^^^^^^^^^^

First is when you add extra functionality to some node. It's possible by adding
extra buttons, sockets, modes. When you add something like this you should ensure
that default behaviour will be unchanged.

New socket, in most cases, can be placed anywhere among existing ones but it
should be checked in the process method that data from sockets is not collecting
by their indexes. Also there is no any automation and in old Blender files the
socket will be missing. So the socket should be added manually and currently
most appropriate place for this is the process method. It leads to some overhead
so probably in future there will be a special upgrade method for such things.
The socket should be optional and the node should be able to work without the
socket to be connected.

.. tip::
   Also quite frequent case is socket renaming. It can be done by adding 
   ``label`` attribute with new name. Also for old files this should be
   repeated in the process method.

Any property can be added to a node but it's default value should not change 
initial node behaviour.

It's possible to add extra values to Enum properties but they always should be
placed in the end of the lists because Blender files keep current enum value
by its index.

All other changes should be done by creating new version of the node.

Create new node version
^^^^^^^^^^^^^^^^^^^^^^^

If it's needed to fix some existing behaviour or remove one the new version of
a node should be introduced. It's not necessary step when changes should be 
applied to changes which were made in not released version of Sverchok. In this
case changes can be done with breaking backward compatibility.

Creating new version should be done togather with keeping previous one. In most
cases it's enough **to copy** module of current node into old_nodes folder. It
should be done more carefully if in the module together with the node something
else is registered.

New version of the node should be created **in the same module** of initial
node by adding suffix to node class. Convention of the suffix is
``MKn`` where *n* is index of new version. The same should be done to
``bl_idname`` attribute of the class. New version of the node can implement
anything what can be implemented in new node.

.. note::
   By changing class name and its ``bl_idname`` attribute, don't forget to fix
   these names in the registration functions and in the ``index.md`` file.

When new version is introduced it's convenient to add replacement operator to
the old version of the node which automatically replace old node with new one
with keeping all connected links. This can be done by adding 
``replacement_nodes`` attribute. The operator will appear in the node context
menu.

.. code-block:: python

   class Node:
       replacement_nodes = [
           (new_node_bl_idname, inputs_mapping_dict, outputs_mapping_dict)
       ]

where ``new_node_bl_idname`` is ``bl_idname`` of replacement node class,
``inputs_mapping_dict`` is a dictionary mapping names of inputs of this node
to names of inputs to new node, and ``outputs_mapping_dict`` is a dictionary
mapping names of outputs of this node to names of outputs of new node.
``inputs_mapping_dict`` and ``outputs_mapping_dict`` can be None.

.. note::
   This attribute also can be used by regular node for quick replacement with
   nodes which have similar functionality.

.. warning::
   When a node has multiple previous version the replacement operator should be
   added (updated) to all of them.

Also the operator will try to copy all node properties by their names. If it's
impossible it's possible to copy properties manually by adding 
``migrate_from(self, old_node)`` method to new node. Also if some extra
work should be done with sockets it's possible to implement in
``migrate_props_pre_relink(self, old_node)`` method which will be called before
links creation.

Alpha/Beta Node State
^^^^^^^^^^^^^^^^^^^^^

When new node is created or existing version of a node is improved we usually
would like to have some time to catch and fix bugs. It can be done the better
the more people will test the node. Thus we have to merge changes into master.
But when node is in master users can save them in their layout and farther fixes
of the node can break them. To avoid this it's possible to mark a node to show
to users that the node is in development state and that backwards incompatible
changes can be introduced. In order to do this Alpa or Beta icon should be
assigned to ``sv_icon`` attribute of the node class.

.. code-block:: python

    class Node:
        sv_icon = 'SV_ALPHA`  # or 'SV_BETA'

It's recommended to mark new nodes and new version of existing node with
*in development* state if there are doubts in robustness of the nodes. A node
should lose the state when new Sverchok's release is introduced.
