Scale
=====

.. image:: https://user-images.githubusercontent.com/14288520/191336220-94690d25-7b2e-4ea0-b637-5659aaf26211.png
  :target: https://user-images.githubusercontent.com/14288520/191336220-94690d25-7b2e-4ea0-b637-5659aaf26211.png

.. image:: https://user-images.githubusercontent.com/14288520/191336746-1a675e31-1237-4b01-b0a4-e71ff1f313ca.png
  :target: https://user-images.githubusercontent.com/14288520/191336746-1a675e31-1237-4b01-b0a4-e71ff1f313ca.png

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

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster)

**List Match**: Define how list with different lengths should be matched

Outputs
-------

Only **Vertices** will be generated. Depending on the type of the inputs, if more than one factor or centers are set, then more objects will be outputted.
If you generate more outputs than inputs were given, then is probably that you need to use list Repeater with your edges or polygons.

Example of usage
----------------

Creating a spiral from a Circle:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_1.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_1.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The node will match different data structures, in this case this mechanism is used to create surface is generated from a line:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_2.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_2.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Sine Oscillator: Number-> :doc:`Oscillator </nodes/number/oscillator>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Deforming an icosphere into a distorted ovoid:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_3.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/scale/scale_vectors_blender_sverchok_example_3.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`