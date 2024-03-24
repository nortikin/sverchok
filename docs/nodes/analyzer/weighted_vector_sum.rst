Center of Mass (Mesh) (Alpha)
=============================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d4ea8073-e205-4a93-867e-55c77ac81f4d
  :target: https://github.com/nortikin/sverchok/assets/14288520/d4ea8073-e205-4a93-867e-55c77ac81f4d

Functionality
-------------

Calculate centers of mass every input mesh (with mass verts or density of materials) and calculate total center of mass:

By edges and density:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/23b5b892-ba5d-491a-b900-503d09242e97
  :target: https://github.com/nortikin/sverchok/assets/14288520/23b5b892-ba5d-491a-b900-503d09242e97

Extrapolates lists of mass of vertices:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bde8dfeb-ace0-4eac-b5b8-195f1700ac99
  :target: https://github.com/nortikin/sverchok/assets/14288520/bde8dfeb-ace0-4eac-b5b8-195f1700ac99

Using of modifier stack:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/027a572b-e764-4009-b08b-b1acff23bb27
  :target: https://github.com/nortikin/sverchok/assets/14288520/027a572b-e764-4009-b08b-b1acff23bb27

Inputs
------

- **Vertices** - or a nested list of vertices that represent separate objects.
- **Edges** - Edges of meshes.
- **Polygons** - Polygons of meshes.
- **Mass of vertices** - Calculate of centers of mass only with vertices (ignore edges and faces). Default value is 1 mass (ex. kg, ton etc.).
- **Density** - Calculate of centers of mass only with edges or faces and ignore vertices. Default value is 1 mass/volume.

Parameters
----------

- **Skip unmanifold centers** - True: If some meshes cannot be used to calc centers of mass then skip them. False - show exception

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c23429a9-44c3-47b6-bd8e-817d1cf6e4eb
      :target: https://github.com/nortikin/sverchok/assets/14288520/c23429a9-44c3-47b6-bd8e-817d1cf6e4eb

- **Center mode** - select mode to calculate center of mass (Vertices, edges, faces or volumes)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c5bc5545-9d2a-42f0-bc59-c48caee94165
      :target: https://github.com/nortikin/sverchok/assets/14288520/c5bc5545-9d2a-42f0-bc59-c48caee94165

    for modes **Vertices** and **Edges** triangulations are disabled (not used):

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/a9136534-a9b2-4fbe-982e-45d56a437a0b
      :target: https://github.com/nortikin/sverchok/assets/14288520/a9136534-a9b2-4fbe-982e-45d56a437a0b

- **Triangulation** - used only for **Faces** or **Volumes** mode. Calculations of center of mass do triangulations before calculations.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/d3853de6-7a49-4658-87ec-c9e3b84fc3b3
      :target: https://github.com/nortikin/sverchok/assets/14288520/d3853de6-7a49-4658-87ec-c9e3b84fc3b3

Output
------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7de47244-453c-4029-bd6d-916365fd1197
  :target: https://github.com/nortikin/sverchok/assets/14288520/7de47244-453c-4029-bd6d-916365fd1197

- **Vertices** - Vertices of result meshes
- **Edges** - Edges of result meshes (Triangulated after **Face** or **Volume** mode)
- **Faces** - Faces of result meshes (Triangulated after **Face** or **Volume** mode)
- **Center of mass of objects** - Center of mass of every input meshes that can be calculated
- **Total center** - If there are any center of mass then this parameter contains center of mass of all meshes (depends of input params **Mass of vertices** or **Density**)
- **Counts**, **Lengths**, **Areas**, **Volumes** - params of meshes
- **Total Counts**, **Total Lengths**, **Total Areas**, **Total Volumes** - Total params of meshes
- **Masses** - List of mass of every input meshes (**Vertices** mode: total summa of vertices mass, **Edges** mode: multiply length*density, **Faces** mode: multiply areas*density, **Volumes** mode: multiply volumes*density)
- **Mass** - Summary mass of all calculated meshes
- **Mask** - Mask of calculated objects. Example: if Mode is Volume and mashes are [cube1, plane1, vertex1, cube2] then mask is [ True, False, False, True]

Examples
--------

TODO