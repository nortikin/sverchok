Inscribed Circle
================

.. image:: https://user-images.githubusercontent.com/14288520/197333809-17a0b469-5dbb-4b0b-a825-1f9ec3ec5fff.png
  :target: https://user-images.githubusercontent.com/14288520/197333809-17a0b469-5dbb-4b0b-a825-1f9ec3ec5fff.png

Functionality
-------------

This node calculates the center and the radius of the inscribed circle for each
triangular face of the input mesh. For non-tri faces, the node will either skip
them or give an error, depending on a setting.

.. image:: https://user-images.githubusercontent.com/14288520/197336160-5924a187-31cc-420f-aaf2-443911c3a7f3.png
  :target: https://user-images.githubusercontent.com/14288520/197336160-5924a187-31cc-420f-aaf2-443911c3a7f3.png

Inputs
------

This node has the following inputs:

- **Vertices**. The vertices of the input mesh. This input is mandatory.
- **Faces**. The faces of the input mesh. This input is mandatory.

Parameters
----------

This node has the following parameter:

- **On non-tri faces**. Defines what the node should do if it encounters a
  non-triangular face. There are following options available:

   - **Skip**. Just skip such faces - do not generate inscribed circles for them.
   - **Error**. Stop processing and give an error (turn the node red).

   The default option is **Skip**. This parameter is available in the N panel only.

.. image:: https://user-images.githubusercontent.com/14288520/197336065-37c7579a-78a7-4e41-87c3-9f8f16ec2c3b.png
  :target: https://user-images.githubusercontent.com/14288520/197336065-37c7579a-78a7-4e41-87c3-9f8f16ec2c3b.png

Outputs
-------

This node has the following outputs:

- **Center**. Centers of the inscribed circles.
- **Radius**. Radiuses of the inscribed circles.
- **Normal**. Normals of the planes where inscribed circles lie - i.e., face normals.
- **Matrix**. For each inscribed circle, this contains a matrix, Z axis of
  which points along face normal, and the translation component equals to the
  center of the inscribed circle. This output can be used to actually place
  circles at their places.

.. image:: https://user-images.githubusercontent.com/14288520/197334259-b9dc54cf-bcd8-44e7-bf3f-3d31ad796da2.png
  :target: https://user-images.githubusercontent.com/14288520/197334259-b9dc54cf-bcd8-44e7-bf3f-3d31ad796da2.png

See also
--------

* CAD-> :doc:`Offset </nodes/modifier_change/offset>`

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/197336441-a2a6f384-bc99-4d2d-9bf0-1e17efdd4527.png
  :target: https://user-images.githubusercontent.com/14288520/197336441-a2a6f384-bc99-4d2d-9bf0-1e17efdd4527.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator->Generatots Extended-> :doc:`Regular Solid </nodes/generators_extended/regular_solid>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197336587-798e9883-6371-4857-934f-1b4090d28419.gif
  :target: https://user-images.githubusercontent.com/14288520/197336587-798e9883-6371-4857-934f-1b4090d28419.gif

Inscribed circles for icosphere:

.. image:: https://user-images.githubusercontent.com/14288520/197336729-8808de12-cd4b-45db-8969-a17d6c964ca4.png
  :target: https://user-images.githubusercontent.com/14288520/197336729-8808de12-cd4b-45db-8969-a17d6c964ca4.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197336821-10da8403-5a88-4d70-bc4a-271726a55f53.gif
  :target: https://user-images.githubusercontent.com/14288520/197336821-10da8403-5a88-4d70-bc4a-271726a55f53.gif

Inscribed circles for (triangulated) Suzanne:

.. image:: https://user-images.githubusercontent.com/14288520/197337199-6d88f7ba-998d-4779-b43c-269d4a58af8b.png
  :target: https://user-images.githubusercontent.com/14288520/197337199-6d88f7ba-998d-4779-b43c-269d4a58af8b.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Modifiers->Modifier Change-> :doc:`Triangulate Mesh </nodes/modifier_change/triangulate>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`