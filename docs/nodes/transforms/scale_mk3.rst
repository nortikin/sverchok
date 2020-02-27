Scale
=====

Functionality
-------------

This node will allow you to scale any king of geometry. It works directly with vertices, not with matrixes, so the output will be just scaled geometry from your original vertices.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.
There is three inputs:

- **Vertices**
- **Centers**
- **Scale**
- **Factor**

Parameters
----------

All parameters except **Vertices** has a default value. **Factor** can be given by the node or an external input.


+----------------+---------------+-----------------+----------------------------------------------------+
| Param          | Type          | Default         | Description                                        |
+================+===============+=================+====================================================+
| **Vertices**   | Vector        | none            | vertices to scale                                  |
+----------------+---------------+-----------------+----------------------------------------------------+
| **Centers**    | Vector        | (0.0, 0.0, 0.0) | point from which the scaling will be done          |
+----------------+---------------+-----------------+----------------------------------------------------+
| **Scale**      | Vector        | (1.0, 1.0, 1.0) | Axis scaling                                       |
+----------------+---------------+-----------------+----------------------------------------------------+
| **Multiplier** | Float         | 1.0             | Uniform multiplier factor                          |
+----------------+---------------+-----------------+----------------------------------------------------+

Outputs
-------

Only **Vertices** will be generated. Depending on the type of the inputs, if more than one factor or centers are set, then more objects will be outputted.
If you generate more outputs than inputs were given, then is probably that you need to use list Repeater with your edges or polygons.

Example of usage
----------------

Creating a spiral from a Circle:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_1.png

The node will match different data structures, in this case this mechanism is used to create surface is generated from a line:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_2.png

Deforming an icosphere into a distorted ovoid:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_3.png
