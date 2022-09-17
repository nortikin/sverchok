Curve Mapper
============

.. image:: https://user-images.githubusercontent.com/14288520/189163825-3b10bd74-e86d-4767-99e3-13265c4e3a24.png
  :target: https://user-images.githubusercontent.com/14288520/189163825-3b10bd74-e86d-4767-99e3-13265c4e3a24.png

Functionality
-------------

This node map all the incoming values using the curve you define manually through the interface.

Disclaimer
----------

This node creates a Blender material node-group and uses "RGB Curves" nodes to create and store the curve.
Due the nature of this implementation the changing the curve will not trigger the node update.
To update the output you need to click in the "Update" button or perform another action that triggers the node-tree update.

Inputs
------

This node has the following input:

* **Value**. The value to be used as an input for the function. The default value is 0.5.

Outputs
-------

This node has the following outputs:

* **Value**. The result of the function application to the input value.
* **Curve**. A Curve object, representing the mapping. This curve will be
  always lying in XOY plane along the OX axis. The domain of the curve is
  defined by **Min X** and **Max X** parameters, which are defined in the curve
  editor widget.
* **Control Points**: Location over the XOY Plane of the control points of the widget.
  It can be used as a 2D slider.

Examples
--------

Basic range remapping:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Curve%20Mapper/curve_mapper_sverchok__blender_example_1.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Curve%20Mapper/curve_mapper_sverchok__blender_example_1.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

Using the node to define the column profile:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Curve%20Mapper/curve_mapper_sverchok__blender_example_2.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Curve%20Mapper/curve_mapper_sverchok__blender_example_2.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Example of the Curve output usage:

.. image:: https://user-images.githubusercontent.com/284644/80520701-4051d200-89a3-11ea-92fd-2f2f2004e4e7.png
  :target: https://user-images.githubusercontent.com/284644/80520701-4051d200-89a3-11ea-92fd-2f2f2004e4e7.png

* Curves-> :doc:`Naturally Parametrized Curve </nodes/curve/length_rebuild>`
* Surface-> :doc:`Revolution Surface </nodes/surface/revolution_surface>`
* Surface-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`