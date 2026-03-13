Solid Boolean
=============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node performs boolean operations on Solid objects: Union ("Fuse"),
Intersection ("Common parts"), Difference ("Cut").

The node can operate either on pairs of objects (like "Solid A" plus "Solid
B"), or on lists of objects (fuse several objects at once, or cut several holes
in a body at once). In this "Accumulative" node, the node performs as follows:

* for Union operation: fuse each list of objects into one body.
* for Intersection operation: take only the part which belongs to **all**
  bodies in the list.
* for Difference operation: take the first body in the list, and use all other
  bodies as "tools", to cut "holes" in the first body.

This node can also produce information about which element of the resulting
Solid object came from which source object. Calculating such information can
take time, so this is an optional feature.

Inputs
------

This node has the following inputs:

* **Solid A**. The first Solid object to perform operation on. This input is
  available and mandatory only if **Accumulate nested** parameter is not
  checked. This input can consume data with nesting level 1 or 2, i.e. lists of
  Solids or lists of lists of Solids.
* **Solid B**. The second Solid object to perform operation on. This input is
  available and mandatory only if **Accumulate nested** parameter is not
  checked. This input can consume data with nesting level 1 or 2, i.e. lists of
  Solids or lists of lists of Solids.
* **Solids**. List of Solid objects to perform operation on. This input is
  available and mandatory only if **Accumulate nested** parameter is checked.
  This input can consume data with nesting level 1 or 2, i.e. lists of Solids
  or lists of lists of Solids. The node will make one Solid out of each list of
  Solids.

Options
-------

This node has the following parameters:

* **Operation**. Boolean operation to perform. The available options are:
  **Intersect**, **Union**, **Difference**. The default option is
  **Intersect**.
* **Generate Masks**. If checked, the node will generate information about
  which element of the resulting Solid came from which solid object. Unchecked
  by default.
* **Accumulate nested**. If checked, the node will operate on pairs of objects,
  so **Solid A** and **Solid B** inputs will be available. Otherwise, the node
  will operate on lists of objects (of arbitrary length), so **Solids** input
  will be available. Unchecked by default.
* **Refine Solid**. If checked, the node will refine the generated Solid
  object, by removing unnecessary edges. In many cases this is required, but in
  cases when this is not required this will only take time. This parameter is
  available only if **Operation** parameter is set to **Union**. Checked by
  default.

Outputs
-------

This node has the following outputs:

* **Solid**. The resulting Solid object. If **Accumulate nested** parameter is
  checked, then this output will always contain data of nesting level 1
  (list of Solids). If **Accumulate nested** parameter is not checked, then
  this output will contain data of nesting level corresponding to nesting level
  in the **Solids A** and **Solids B** inputs, considering the node makes one
  Solid out of each pair of Solids.
* **EdgesMask**. Mask for Edges of generated Solid object, which is True for
  edges that come from more than one source object. For **Intersect**
  operation, this mask will always contain all True. This output is only
  available when **Generate Masks** parameter is checked.
* **EdgeSources**. For each Edge of generated Solid object, this output
  contains a list of indexes of source objects, from which this edge came. See
  more detailed explanation below. This output is only available when
  **Generate Masks** parameter is checked.
* **FacesMask**. Mask for Faces of generated Solid object, which is True for
  faces that come from more than one source object. For Union operation, this
  output contains all False, because all "common" faces are always inside the
  body. This output is only available when **Generate Masks** parameter is
  checked.
* **FaceSources**. For each Face of generated Solid object, this output
  contains a list of indexes of source objects, from which this face came.
  This output is only available when **Generate Masks** parameter is checked.

The following illustrates how **EdgeSources** output is calculated:

.. image:: https://user-images.githubusercontent.com/284644/94042893-8ccffb00-fde5-11ea-938e-328df1d65d7e.png

Here we have two cubes, 0 (plugged into Solid A input), and 1 (plugged into
Solid B input). Purple edges came from cube 0, for them EdgeSources output
contains ``[0]``. Orange edges came from cube 1, for them EdgeSources output
contains ``[1]``. Edges marked with cyan came from both cubes, for them
EdgeSources output contains ``[0, 1]``.

FaceSources output is calculated similarly, but for faces instead of edges.


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/solid_boolean/solid_boolean_blender_sverchok_example.png

Example of **EdgesMask** output usage:

.. image:: https://user-images.githubusercontent.com/284644/94038496-f1885700-fddf-11ea-93e6-894aea236ef8.png

Example of **EdgeSources** output usage. Take five cubes, fuse them, then select only edges that came from intersection of cubes number 1 and 2 (starting from zero), and make fillet for them:

.. image:: https://user-images.githubusercontent.com/284644/94045977-82176500-fde9-11ea-9c9d-2bce61012280.png

