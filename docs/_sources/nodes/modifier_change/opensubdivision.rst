Catmull-Clark Subdivision Node
==============================

.. image:: https://user-images.githubusercontent.com/14288520/200193808-718aef11-b7cf-4684-a0c7-b0139f4f4e95.png
  :target: https://user-images.githubusercontent.com/14288520/200193808-718aef11-b7cf-4684-a0c7-b0139f4f4e95.png

Functionality
-------------

This node applies [Catmull-Clark subdivision](https://en.wikipedia.org/wiki/Catmull%E2%80%93Clark_subdivision_surface) (as implemented by the [OpenSubdiv](https://github.com/PixarAnimationStudios/OpenSubdiv)) to the input mesh at the specified number of levels. 

.. image:: https://user-images.githubusercontent.com/14288520/200194195-da41fd97-423b-4d5b-bef0-f752665201be.png
  :target: https://user-images.githubusercontent.com/14288520/200194195-da41fd97-423b-4d5b-bef0-f752665201be.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of input mesh.
- **Faces**. Faces of input mesh.

Parameters
----------

This node has the following parameters:

- **Levels**. Maximum subdivision level to be applied to input mesh.

.. image:: https://user-images.githubusercontent.com/14288520/200194321-70f2da21-691d-4293-8965-6d16d1fd402e.png
  :target: https://user-images.githubusercontent.com/14288520/200194321-70f2da21-691d-4293-8965-6d16d1fd402e.png

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Faces**. All faces of resulting mesh.

**Note**: **Vertices** and **Faces** inputs **must** be compatible, in that the **Faces** input **may not refer to vertex indices that do not exist in the Vertices list** (e.g. **Faces** cannot refer to vertex 7, provided a list of **Vertices** with only 5 vertices). 

Unexpected behavior may occur if using Faces from one mesh with Vertices from another. 

Examples of usage
-----------------
(Old)

.. image:: https://user-images.githubusercontent.com/79929629/180858417-dc585075-486a-443b-a618-ae04e281cd90.png
  :target: https://user-images.githubusercontent.com/79929629/180858417-dc585075-486a-443b-a618-ae04e281cd90.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Matrix Apply: Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

(Old)

.. image:: https://user-images.githubusercontent.com/79929629/180858569-40b684c8-bdc7-4690-9e74-f0733dd21210.png
  :target: https://user-images.githubusercontent.com/79929629/180858569-40b684c8-bdc7-4690-9e74-f0733dd21210.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Apply: Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Vector Test:

.. image:: https://user-images.githubusercontent.com/14288520/200194455-5b73d35f-12ff-45d7-b486-5fe2505adc11.png
  :target: https://user-images.githubusercontent.com/14288520/200194455-5b73d35f-12ff-45d7-b486-5fe2505adc11.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Many Bodies:

.. image:: https://user-images.githubusercontent.com/14288520/200195224-cecce757-8b4f-4e18-ba75-4597a88c1916.png
  :target: https://user-images.githubusercontent.com/14288520/200195224-cecce757-8b4f-4e18-ba75-4597a88c1916.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* MUL, DIV: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Level 0 Catmul-Clark Subdivision of NGons:

.. image:: https://user-images.githubusercontent.com/14288520/200195960-49322096-3aad-4138-baac-398b185c63eb.png
  :target: https://user-images.githubusercontent.com/14288520/200195960-49322096-3aad-4138-baac-398b185c63eb.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* MUL, ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Node Mute:

.. image:: https://user-images.githubusercontent.com/14288520/200196279-c757b430-4bc8-4820-8ee4-7514c6f6712a.png
  :target: https://user-images.githubusercontent.com/14288520/200196279-c757b430-4bc8-4820-8ee4-7514c6f6712a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`