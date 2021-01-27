Polyline viewer
===============

.. image:: https://user-images.githubusercontent.com/28003269/96707644-35538980-13a9-11eb-95f9-56b02f2c561e.png

Functionality
-------------

Inspite of its name it can generate splines of two types: polylines or NURBS. 
Input vertices should be given in sorted order from start spline to its end. Generating spines can have thickness. 
If bevel object is given (curve type) it will be extruded along generated splines.

Category
--------

Viz -> Polyline viewer

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
- **Spline type** - NURBS ot polyline
- **Close** - Closes the generated splines
- **Assign matrix to** - Matrix can be assigned either to objects or mesh. It will effect only onto position of origin. Also if matrix is applying to objects `lock origin` will be always True
- **Caps** - Seals the ends of a beveled curve

Outputs
-------

- Objects


Examples
--------

**Brains generator**

.. image:: https://user-images.githubusercontent.com/28003269/96714209-deeb4880-13b2-11eb-9c89-c9ff6393a9fb.png

**Generating bunch of wires**

.. image:: https://user-images.githubusercontent.com/28003269/96716140-ab5ded80-13b5-11eb-9f0f-7dc0c3f7fefa.png
