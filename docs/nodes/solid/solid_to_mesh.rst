Solid to Mesh
=============

Functionality
-------------

Transform Solid data to Mesh Data.

Offers three methods:

**Basic**: This method is the fastest offers a Precision option that expects values(and only will be affected)  like 1, 0.1, 0.001. Note that a lower number means more precision. Also when reducing the precision (by giving a greater number) the node may not change until you change the input solid data.

**Standard**: Has the following options

- Surface deviation: Maximal linear deflection of a mesh section from the surface of the object.

- Angular deviation: Maximal angular deflection from one mesh section to the next section.

- Relative surface deviation: If checked, the maximal linear deviation of a mesh segment will be the specified Surface deviation multiplied by the length of the current mesh segment (edge).


**Mefisto**: The only setting is:

- Maximum edge length: If this number is smaller the mesh becomes finer. The smallest value is 0.


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/solid_to_mesh/solid_to_mesh_blender_sverchok_example.png
