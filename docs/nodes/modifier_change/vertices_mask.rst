Mask Vertices
=============

.. image:: https://user-images.githubusercontent.com/14288520/200125469-8ff2b55d-1cb5-4b50-8f6d-506f5839477d.png
  :target: https://user-images.githubusercontent.com/14288520/200125469-8ff2b55d-1cb5-4b50-8f6d-506f5839477d.png

Functionality
-------------

Filter vertices with False/True bool values and automatically removes not connected edges and polygons.

.. image:: https://user-images.githubusercontent.com/14288520/200125916-512e22aa-984c-4dc3-b17b-53609a3c1140.png
  :target: https://user-images.githubusercontent.com/14288520/200125916-512e22aa-984c-4dc3-b17b-53609a3c1140.png

Inputs
------

- **Mask**
- **Vertices**
- **Poly Edge**

Parameters
----------

+-----------+------------------+-----------+----------------------------------------------------------------+
| Param     | Type             | Default   | Description                                                    |
+===========+==================+===========+================================================================+
| Mask      | list of booleans | [1,0]     | Mask can be defined with ListInput node or Formula node        |
|           |                  |           |                                                                |
|           |                  |           | or other as list [n,n1,n2...ni] where n's can be 0 or 1        |
|           |                  |           |                                                                |
|           |                  |           | (False or True)                                                |
+-----------+------------------+-----------+----------------------------------------------------------------+

Outputs
-------

- **Vertices**
- **Poly Edge**

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/200126185-9049b68e-7eb4-464c-8d56-fba5307249f0.png
  :target: https://user-images.githubusercontent.com/14288520/200126185-9049b68e-7eb4-464c-8d56-fba5307249f0.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`