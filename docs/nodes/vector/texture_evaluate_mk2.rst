Texture Evaluate
================

This node evaluates a  texture at specific coordinates

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Mapping        | Vectors mapping mode. Offers:                                           |
|                | UV Coordinates (with domain 0 to 1) and                                 |
|                | Object (with domain -1 to 1)                                            |
+----------------+-------------------------------------------------------------------------+
| Channel        | Color channel to output                                                 |
|                | Offers: Red, Green, Blue, Hue, Saturation, Value, Alpha, RGB Average,   |
|                | Luminosity and Color                                                    |
+----------------+-------------------------------------------------------------------------+
| Use Alpha      | Toggle to add alpha channel (Only when Channel is set to Color)         |
+----------------+-------------------------------------------------------------------------+
| Vertices       | Vertices of the mesh to displace                                        |
+----------------+-------------------------------------------------------------------------+
| Texture        | Texture(s) to use as base                                               |
+----------------+-------------------------------------------------------------------------+


Examples
--------



.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_1.png

Mixing 3 textures

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_2.png

Masking mesh with texture

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_3.png

Blender procedural textures work in 3D space

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_4.png

You can input multiple textures, when joined [[texture, texture,..],[..],..] they will be used in a single set of vertices with a single output list

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_5.png

Differences between Object Mapping and UV Coordinates mapping
