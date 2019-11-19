Inset Special
=============



Functionality
-------------

Make inset in polygons. Output inner and outer polygons separately.

Inputs and Parameters
---------------------

This node has the following inputs:

- **Inset** - Proportional offset values meaning 0 in the center and 1 in the edges. Vectorized for every polygon as [[f,f,f,f,f]]

- **Distance** - Offset distance along normal. Vectorized for every polygon as [[f,f,f,f,f]]

- **vertices** - Vertices of objects

- **polygons** - polygons of objects

- **ignore** - mask of affected polygons

- **Make Inner** - Determine if inner face should be created


Outputs
-------

This node has the following outputs:

- **vertices**
- **polygons**
- **Ignored** - get polygons that have not been affected.
- **Inset** - get inner polygons.

Examples of usage
-----------------

.. image:: https://raw.githubusercontent.com/vDicdoval/sverchok/docs_images/images_for_docs/CAD/Inset_special/inset_special_example.png
  :alt: procedural_Inset_example_blender_sverchok_1.png
  
.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/CAD/Inset_special/inset_special_example2.png
  :alt: procedural_Inset_example_blender_sverchok_2.png


