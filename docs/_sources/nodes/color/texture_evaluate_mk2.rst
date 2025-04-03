Texture Evaluate
================

.. image:: https://user-images.githubusercontent.com/14288520/189663161-48c45f22-ec8a-4973-b881-6da7fb829f11.png
  :target: https://user-images.githubusercontent.com/14288520/189663161-48c45f22-ec8a-4973-b881-6da7fb829f11.png

This node evaluates a  texture at specific coordinates

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Mapping        | Vectors mapping mode. Offers:                                           |
|                |                                                                         |
|                | UV Coordinates (with domain 0 to 1) and                                 |
|                |                                                                         |
|                | Object (with domain -1 to 1)                                            |
+----------------+-------------------------------------------------------------------------+
| Channel        | Color channel to output                                                 |
|                |                                                                         |
|                | Offers: Red, Green, Blue, Hue, Saturation, Value, Alpha, RGB Average,   |
|                |                                                                         |
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
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_1.png

Mixing 3 textures

.. image:: https://user-images.githubusercontent.com/14288520/189663199-78a379ee-0a7c-49ba-80b3-52f31f13fe6a.png
  :target: https://user-images.githubusercontent.com/14288520/189663199-78a379ee-0a7c-49ba-80b3-52f31f13fe6a.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Masking mesh with texture

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_3.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_3.png

Blender procedural textures work in 3D space

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_4.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/texture_evaluate/texture_evaluate_sverchok_blender_example_4.png

You can input multiple textures, when joined [[texture, texture,..],[..],..] they will be used in a single set of vertices with a single output list

.. image:: https://user-images.githubusercontent.com/14288520/189665154-9b97814d-e3b0-4e15-a886-8fe0ea2b4e1a.png
  :target: https://user-images.githubusercontent.com/14288520/189665154-9b97814d-e3b0-4e15-a886-8fe0ea2b4e1a.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

Differences between Object Mapping and UV Coordinates mapping
