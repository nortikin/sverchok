Vector Drop
===========

.. image:: https://user-images.githubusercontent.com/14288520/189416082-af9b8af3-b405-49cc-8894-b5fd15ada232.png
  :target: https://user-images.githubusercontent.com/14288520/189416082-af9b8af3-b405-49cc-8894-b5fd15ada232.png

Functionality
-------------

Reverse operation to Matrix apply. 
If matrix apply adding all transformations to vertices.
Than vector drop subtract matrix from vertices.

Inputs
------

* **Vectors** - Vectors input to transform
* **Matrixes** - Matrix to subtract from vertices

Outputs
-------

**Vectors** - vertices

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189416105-c7b9ec1f-9ebd-4c8b-be56-bd9670349acc.png
  :target: https://user-images.githubusercontent.com/14288520/189416105-c7b9ec1f-9ebd-4c8b-be56-bd9670349acc.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* Modifiers->Modifier Change-> :doc:`Polygon Boom </nodes/modifier_change/polygons_boom>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer 2D </nodes/viz/viewer_2d>`

.. image:: https://user-images.githubusercontent.com/14288520/189416117-b9c89036-1e36-4046-8b37-1b578cb993d7.png
  :target: https://user-images.githubusercontent.com/14288520/189416117-b9c89036-1e36-4046-8b37-1b578cb993d7.png
