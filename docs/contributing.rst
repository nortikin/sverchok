**********
Contribute
**********

Our workflow:
=============

#. You have the freedom to code how you like, but follow `pep8 <https://www.python.org/dev/peps/pep-0008/>`_.

#. Implementing ideas from other add-ons is fine, if you have the appropriate licenses (GPL), 
   written consent or rights. We don't accept unattributed code you didn't write.

#. Before you spend a lot of time making something, we recommend you tell us about it beforehand 
   in the Issue Tracker. Sometimes the thing you want to make already exists, or we have plans for
   it already with placeholder code.

#. Brainstorm and discuss solutions. We use the issue tracker a lot and will give our honest opinion
   and interpretations of new code. We are artists and technical people trying to solve complicated and
   interesting issues using code and Blender. We care about optimal code but also accept working and novel solutions.

#. Test your code, Test your proposed changes. Write automated tests for your code whenever it makes sense.
   Please refer to `this document <testing.html>`_ for details.


What not to do:
===============

Doing these things will break old layouts or have other unintended consequences.

1. Change ``bl_idname`` of a node

2. Remove or rename sockets (use labels for socket renaming)

3. Adding new socket inbetween existing sockets. We prefer that you add sockets behind the last
   existing socket for either ``self.inputs`` or ``self.outputs``. This is the rule only if access
   to sockets is made by their indexes.

4. There are other reserved property names see the bpy.types.Node baseclass in Blender docs and
   Sverchok's custom node mixin class.


To create a node:
=================

1. Make a scripted node to test the idea.

2. Show your node to us in an issue or create branch or fork of master in github. If it
   is a huge complex job we can make you collaborator. 

3. Copy an existing node that is similar, as a basis to start from.

4. Change class name, class bl_idname, docstring, and class registration section in your file (at the bottom)

5. Add node's ``bl_idname`` to *sverchok/index.md* file in an appropriate category.

6. Add file to matching category: ``..sverchok/nodes/whatever_existing_category/your_file.py``

7. Make a pull request.


Code structure:
===============

1. There is a convention that all classes that are subclasses of blender classes - have to have 
   prefix ``Sv``, ie SvColors.

2. ``sverchok/node_tree.py`` and ``sverchok/utils/nodes_mixins`` contains base classes of nodes.

3. ``sverchok/data_structure.py`` has a lot of function to manipulate with lists.

4. **Utils** folder has:

   a. CADmodule - to provide lines intersection

   b. IndexViewerDraw - to provide OpenGL drawing of INDXview node in basics

   c. sv_bmeshutils - manipulation with Blender builtin mesh data structure

   d. text_editor_plugins - for sandbox node scripted node (SN) to implement Ctrl+I auto complete function

   e. text_editor_submenu - templates of SN

   f. voronoi - for delaunai and voronoi functions of correspond nodes

5. **Node scripts** folder for every template for SN (see utils-e.)

6. **Nodes** folder for categorized nodes.

#. to **CHANGE** some node, please, follow next (in case if changes will brock backward compatibility):

   a. Copy node file to ../old_nodes;
   b. Change ``bl_idname`` to old_bl_idname + MK2.
