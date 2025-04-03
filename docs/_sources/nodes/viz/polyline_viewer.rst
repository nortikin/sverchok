Polyline Viewer
===============

.. image:: https://user-images.githubusercontent.com/14288520/190324978-906e2e24-891d-4ea1-9ffc-9cfb9c849f1f.png
  :target: https://user-images.githubusercontent.com/14288520/190324978-906e2e24-891d-4ea1-9ffc-9cfb9c849f1f.png

.. image:: https://user-images.githubusercontent.com/14288520/190347707-60c3bbc6-c6b3-47ed-b3c7-90ec60e10810.png
  :target: https://user-images.githubusercontent.com/14288520/190347707-60c3bbc6-c6b3-47ed-b3c7-90ec60e10810.png

Functionality
-------------

In spite of its name it can generate splines of two types: polylines or NURBS. 
Input vertices should be given in sorted order from start spline to its end. Generating spines can have thickness. 
If bevel object is given (curve type) it will be extruded along generated splines.

Category
--------

Viz -> Polyline Viewer

Inputs
------

- **Vertices** - expect sorted along spline
- **Matrix**
- **radius** - thickness of generated splines
- **tilt** - screwing of generate spline in radians
- **bevel object** - curve type object to extrude along generated spline

Parameters
----------

- **Live** - Processing only happens if *update* is ticked
- **Hide View** - Hides current meshes from view
- **Hide Select** - Disables the ability to select these meshes
- **Hide Render** - Disables the renderability of these meshes
- **Base Name** - Base name for Objects and Meshes made by this node
- **Random name** - Generates random name with random letters
- **Select** - Select every object in 3dview that was created by this Node
- **Collection** - Pick collection where to put objects
- **Material Select** - Assign materials to Objects made by this node
- **Add material** - It creates new material and assigns to generated objects
- **Lock origin** - If it disabled then origins of generated objects can be set manually in viewport
- **Merge** - On by default, join all meshes produced by incoming geometry into one
- **2D or 3D** - Dimensions of generated splines
- **Bevel depth** - Changes the size of the bevel
- **Resolution** - Alters the smoothness of the bevel
- **Spline type** - NURBS to polyline
- **Cyclic** - Closes the generated splines
- **Assign matrix to** - Matrix can be assigned either to objects or mesh. It will effect only onto position of origin. Also if matrix is applying to objects `lock origin` will be always True
- **Caps** - Seals the ends of a beveled curve

Outputs
-------

- Objects


Examples
--------

**Brains generator**

.. image:: https://user-images.githubusercontent.com/28003269/96714209-deeb4880-13b2-11eb-9c89-c9ff6393a9fb.png
    :target: https://user-images.githubusercontent.com/28003269/96714209-deeb4880-13b2-11eb-9c89-c9ff6393a9fb.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Analyzers-> :doc:`KDT Closest Path </nodes/analyzer/kd_tree_path>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`

---------

**Generating bunch of wires**

.. image:: https://user-images.githubusercontent.com/14288520/190354647-c6e97c84-e644-44a1-bddb-6cbc7651ad85.png
  :target: https://user-images.githubusercontent.com/14288520/190354647-c6e97c84-e644-44a1-bddb-6cbc7651ad85.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Number-> :doc:`Number Range </nodes/number/number_range>`