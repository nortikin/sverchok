Segment
=======

.. image:: https://user-images.githubusercontent.com/14288520/188512106-e151f579-82d5-4cb5-8e41-c67d87f02151.png
  :target: https://user-images.githubusercontent.com/14288520/188512106-e151f579-82d5-4cb5-8e41-c67d87f02151.png

Functionality
-------------

The node creates segments between two given points. Also number of subdivisions can be set.

Category
--------

Generators -> Segment

Inputs
------

- **A** - 1 vertices
- **B** - 2 vertices
- **Num cuts** - number of line subdivision

Outputs
-------

- **Verts** - coordinates of line(s)
- **Edges** - just edges

Parameters
----------

+---------------+---------------+--------------+---------------------------------------------------------+
| Param         | Type          | Default      | Description                                             |
+===============+===============+==============+=========================================================+
| **Cute modes**| Enum          | "Cuts"       | **Cuts** - cut line evenly                              |
|               |               |              |                                                         |
|               | Cuts/Steps    |              | **Steps** - cut line proportionally by given steps      |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Split to    | Boolean       |              |                                                         |
| objects**     | (N panel)     | True         | Each line will be put to separate object any way        |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Numpy       | Boolean       | False        | Convert vertices to Numpy array                         |
| output**      | (N panel)     |              |                                                         |
+---------------+---------------+--------------+---------------------------------------------------------+

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/188512120-e3410fd7-eda8-4697-8ef6-04b60dbb6845.png
  :target: https://user-images.githubusercontent.com/14288520/188512120-e3410fd7-eda8-4697-8ef6-04b60dbb6845.png

.. image:: https://user-images.githubusercontent.com/14288520/188512135-6084a8b5-c15b-494b-a44c-6a0f6e50578c.gif
  :target: https://user-images.githubusercontent.com/14288520/188512135-6084a8b5-c15b-494b-a44c-6a0f6e50578c.gif

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

The AB mode will output a divided segment for each vector pair, the step can be used to change the proportions of the divisions

.. image:: https://user-images.githubusercontent.com/14288520/188512311-9ea7e002-ca3d-47ee-b639-f055d4b9e4b4.png
  :target: https://user-images.githubusercontent.com/14288520/188512311-9ea7e002-ca3d-47ee-b639-f055d4b9e4b4.png

.. image:: https://user-images.githubusercontent.com/14288520/188512296-6287d7eb-ae38-4087-9a31-1fe433deea93.gif
  :target: https://user-images.githubusercontent.com/14288520/188512296-6287d7eb-ae38-4087-9a31-1fe433deea93.gif

* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Modifiers->Modifier Make-> :doc:`WireFrame </nodes/modifier_make/wireframe>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Advanced example using the node to create a paraboloid grid