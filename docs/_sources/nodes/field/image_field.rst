Image Field
===========

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0a0215eb-dd9e-4a85-808c-834d4d052c52
  :target: https://github.com/nortikin/sverchok/assets/14288520/0a0215eb-dd9e-4a85-808c-834d4d052c52

Functionality
-------------

This node generates Vector Fields and Scalar Fields based on different representations of colors in the Blender's Image object.

The image is supposed to lie in one of coordinate planes. For example, if the
image lies in XOY plane, and we fix some pair of X and Y coordinates (X0, Y0),
then the values of the field will be the same in all points (X0, Y0, Z) for any
Z.

Inputs
------

This node does not have inputs.

Parameters
----------

This node has the following parameters:

* **Image plane**. The coordinate plane in which the image is supposed to be
  placed. The available values are XY, YZ and XZ. The default value is XY.
* **Image**. Blender's Image object to be turned into Field.

Outputs
-------

This node has the following outputs:

* **RGB**. Vector field. Coordinates of the vectors are defined by RGB components of colors in the image.
* **HSV**. Vector field. Coordinates of the vectors are defined by HSV components of colors in the image.
* **Red**, **Green**, **Blue**. Scalar fields defined by RGB components of colors in the image.
* **Hue**, **Saturation**, **Value**. Scalar fields defined by HSV components of colors in the image.
* **Alpha**. Scalar field defined by the alpha (transparency) channel of the image.
* **RGB Average**. Scalar field defined as average of R, G and B channels of the image.
* **Luminosity**. Scalar field defined as luminosity channel of the image.

Example of usage
----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/284644/79607518-c309a000-810c-11ea-86fa-be7c16043b32.png
  :target: https://user-images.githubusercontent.com/284644/79607518-c309a000-810c-11ea-86fa-be7c16043b32.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Fields-> :doc:`Vector Field Graph </nodes/field/vector_field_graph>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
