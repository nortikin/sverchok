********
Features
********

Comes with more than 600 nodes to help create and manipulate geometry. Combining these nodes will allow you to:


Parametric modeling
===================

Generate and edit parametric 3D models with nodes. There are |generators| and |extra_generators|.
Their purpose is to generate different primitive objects. This primitives can be used
for creating more complex models. There are |transform| which can perform basic operations
with objects and there are nodes which can modify objects (|modifiers|, |modifiers2|, |cad|).
And at last there are |viewers| which can import 3D objects into the Blender scene.

.. |generators| replace:: :doc:`generator nodes <../nodes/generator/generator_index>`
.. |extra_generators| replace:: :doc:`generator nodes 2 <../nodes/generators_extended/generators_extended_index>`
.. |transform| replace:: :doc:`transform nodes <../nodes/transforms/transforms_index>`
.. |modifiers| replace:: :doc:`Modifiers <../nodes/modifier_change/modifier_change_index>`
.. |modifiers2| replace:: :doc:`Modifiers 2 <../nodes/modifier_make/modifier_make_index>`
.. |cad| replace:: :doc:`CAD nodes <../nodes/CAD/CAD_index>`
.. |viewers| replace:: :doc:`viewer nodes <../nodes/viz/viz_index>`

.. figure:: https://user-images.githubusercontent.com/28003269/126115967-ec28a5c6-6808-4ede-bcc8-5a5667acd5ee.gif

    Using generator, modifier and viewer nodes together


Supporting curves, solids and other data types
==============================================

Except standard mesh objects Sverchok supports such type of objects as |curves|, |surfaces|, |nurbs|, |solids|.
This is mathematical objects which using has its own advantages.

.. |curves| replace:: :doc:`Curves <../data_structure/curves>`
.. |surfaces| replace:: :doc:`Surfaces <../data_structure/surfaces>`
.. |nurbs| replace:: :doc:`Nurbs <../data_structure/nurbs>`
.. |solids| replace:: :doc:`Solids <../data_structure/solids>`

.. figure:: https://user-images.githubusercontent.com/28003269/126273173-8b43b005-ea48-4bdb-9f5b-812bdf778c64.gif
    :width: 800

    Creating catenary curves


Analyzer nodes
==============

There are bunch of nodes which can give utility information about object such as curvature, area, volume
bounding box, nearest point etc. Most of them can be found in |analyzers| category. 

.. |analyzers| replace:: :doc:`Curves <../nodes/analyzer/analyzer_index>`

.. figure:: https://user-images.githubusercontent.com/284644/80917635-d9089900-8d79-11ea-982e-ccde3742ffc6.png
    :width: 800

    Color surface according its curvature


Materials, UV maps
==================

Working with materials and UV maps. (|material|, |uv_map|, |unwrap|)

.. |material| replace:: :doc:`Assign material <../nodes/object_nodes/assign_materials>`
.. |uv_map| replace:: :doc:`Assign UV map <../nodes/object_nodes/set_custom_uv_map>`
.. |unwrap| replace:: :doc:`Unwrap mesh <../nodes/modifier_change/follow_active_quads>`

.. figure:: https://user-images.githubusercontent.com/28003269/126289625-dd6279eb-2d07-4bab-b7db-24d8b0816ee9.gif

    Set UV map to a plane


Instancing objects
==================

Instancing tens and hundreds thousands of objects with |instance| and |instance2| nodes.

.. |instance| replace:: :doc:`Object instancer <../nodes/viz/instancer>`
.. |instance2| replace:: :doc:`Object instancer <../nodes/viz/dupli_instances_mk5>`

.. image:: https://user-images.githubusercontent.com/10011941/117689137-c0fffc80-b1b9-11eb-9a00-2a57f7e49976.png

Other features
==============

.. hlist::
   :columns: 3

   * :doc:`Genetic algorithm <../nodes/logic/evolver>`
   * :doc:`Insolation/sun radiation calculation <../nodes/analyzer/object_insolation>`
   * :doc:`Real time drawing to SVG <../nodes/svg/svg_index>`
   * :doc:`Generate images with WFC algorithm <../nodes/generators_extended/wfc_texture>`
   * :doc:`Simulations <../nodes/pulga_physics/pulga_physics_solver>`
   * :doc:`Import JSON and CSV formats <../nodes/text/text_in_mk2>`
