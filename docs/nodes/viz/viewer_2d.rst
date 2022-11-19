Viewer 2D
=========

.. image:: https://user-images.githubusercontent.com/14288520/189997976-04f0a52a-d79d-4e6f-8bbb-e1314c90d59f.png
  :target: https://user-images.githubusercontent.com/14288520/189997976-04f0a52a-d79d-4e6f-8bbb-e1314c90d59f.png

.. image:: https://user-images.githubusercontent.com/14288520/190164728-9cb2ccfa-ad2c-4120-a21b-9e0bbdf6f954.png
  :target: https://user-images.githubusercontent.com/14288520/190164728-9cb2ccfa-ad2c-4120-a21b-9e0bbdf6f954.png

.. image:: https://user-images.githubusercontent.com/14288520/190137970-e1023822-5169-4506-9353-e2446b8698ad.png
  :target: https://user-images.githubusercontent.com/14288520/190137970-e1023822-5169-4506-9353-e2446b8698ad.png

Functionality
-------------

This node displays data it in the 2d view, using opengl and shaders. The node is intended to be a fast way to show you the result of your node tree. We've added various levels of refinements that you may find useful to better understand the virtual geometry you've created.

Modes
-----

* **Number**: Displays graphically list of numbers
* **Path**: Displays paths using a vectors list
* **Curve**: Display Curves at desired resolution
* **Mesh**: Displays mesh data from vectors, edges and polygons list

Features
--------

* **Background**: Display background under the mesh with desired color
* **Working Plane**: Projection is over XY, XZ or YZ plane
* **Scale**: Drawing scale
* **Point Size and Edge width**.
* **Cycle**: Close Path (only in path mode)
* **Vertex Color, Edge Color and Polygon Color**: Color of displayed geometry. It can be color per element or color per object
* **Random Vertex Color**: Use random vertex colors
* **Edges Vertex Color**: Uses vertex color to colorize edges
* **Polygons Vertex Color**:  Uses vertex color to colorize polygons

Feature Examples
----------------

* **Background**: Display background under the mesh with desired color

.. image:: https://user-images.githubusercontent.com/14288520/190150035-c0f9ede3-e018-441e-8174-74ee0c4df6b2.png
  :target: https://user-images.githubusercontent.com/14288520/190150035-c0f9ede3-e018-441e-8174-74ee0c4df6b2.png

-------------

* **Working Plane**: Projection is over XY, XZ or YZ plane

.. image:: https://user-images.githubusercontent.com/14288520/190149183-7c31f5a9-fb83-448a-90eb-ad064830ca4e.png
  :target: https://user-images.githubusercontent.com/14288520/190149183-7c31f5a9-fb83-448a-90eb-ad064830ca4e.png

-------------

* **Scale**: Drawing scale

.. image:: https://user-images.githubusercontent.com/14288520/190151451-c2894184-1b91-4208-8a55-ce714bc810cd.png
  :target: https://user-images.githubusercontent.com/14288520/190151451-c2894184-1b91-4208-8a55-ce714bc810cd.png

-------------

* **Point Size and Edge width**.

.. image:: https://user-images.githubusercontent.com/14288520/190150929-6c30b446-846e-421c-b9db-c332f9c1d16f.png
  :target: https://user-images.githubusercontent.com/14288520/190150929-6c30b446-846e-421c-b9db-c332f9c1d16f.png

-------------

* **Cycle**: Close Path (only in path mode)

.. image:: https://user-images.githubusercontent.com/14288520/190152668-a4e4d26f-decf-467f-ad12-38e56b4512ee.png
  :target: https://user-images.githubusercontent.com/14288520/190152668-a4e4d26f-decf-467f-ad12-38e56b4512ee.png

-------------

* **Vertex Color, Edge Color and Polygon Color**: Color of displayed geometry. It can be color per element or color per object

.. image:: https://user-images.githubusercontent.com/14288520/190157278-9c110e7c-5e60-4507-aa5b-31a0d44e6f2a.png
  :target: https://user-images.githubusercontent.com/14288520/190157278-9c110e7c-5e60-4507-aa5b-31a0d44e6f2a.png

* Generator->Generator Extended-> :doc:`NGon </nodes/generators_extended/polygon_grid>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

-------------

* **Random Vertex Color**: Use random vertex colors

.. image:: https://user-images.githubusercontent.com/14288520/190157905-e10a9fec-a6c1-48cc-a222-2aeb9c18e2f0.png
  :target: https://user-images.githubusercontent.com/14288520/190157905-e10a9fec-a6c1-48cc-a222-2aeb9c18e2f0.png

-------------

* **Edges Vertex Color**: Uses vertex color to colorize edges

.. image:: https://user-images.githubusercontent.com/14288520/190158666-a611d501-b1d4-4c76-bbcc-21823029833f.png
  :target: https://user-images.githubusercontent.com/14288520/190158666-a611d501-b1d4-4c76-bbcc-21823029833f.png

-------------

* **Polygons Vertex Color**:  Uses vertex color to colorize polygons

.. image:: https://user-images.githubusercontent.com/14288520/190159248-be156f18-f5b4-43a8-b140-52b01a3bfd7c.png
  :target: https://user-images.githubusercontent.com/14288520/190159248-be156f18-f5b4-43a8-b140-52b01a3bfd7c.png

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190119957-b10d20d9-feaf-4038-84b7-d6d74169bbfb.png
  :target: https://user-images.githubusercontent.com/14288520/190119957-b10d20d9-feaf-4038-84b7-d6d74169bbfb.png

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

-------------

.. image:: https://user-images.githubusercontent.com/14288520/189998316-ee8def48-791b-4da0-8a1a-008ce80f8c36.png
  :target: https://user-images.githubusercontent.com/14288520/189998316-ee8def48-791b-4da0-8a1a-008ce80f8c36.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

-------------

.. image:: https://user-images.githubusercontent.com/14288520/189998351-4ffb42be-a51b-4ecd-a4ec-e781d30055df.png
  :target: https://user-images.githubusercontent.com/14288520/189998351-4ffb42be-a51b-4ecd-a4ec-e781d30055df.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

-------------

.. image:: https://user-images.githubusercontent.com/14288520/189998404-8bb7216a-1411-490c-b985-738435d04151.png
  :target: https://user-images.githubusercontent.com/14288520/189998404-8bb7216a-1411-490c-b985-738435d04151.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves->Primitives-> :doc:`Fillet Polyline </nodes/curve/fillet_polyline>`

-------------

.. image:: https://user-images.githubusercontent.com/10011941/81241305-2dc24300-900a-11ea-8bba-26f9fb140767.png
    :target: https://user-images.githubusercontent.com/10011941/81241305-2dc24300-900a-11ea-8bba-26f9fb140767.png

* Script-> :doc:`Profile Parametric </nodes/script/profile_mk3>`

-------------

.. image:: https://user-images.githubusercontent.com/14288520/189998505-fb07a75e-898a-4891-80cf-b9e40403cf54.png
  :target: https://user-images.githubusercontent.com/14288520/189998505-fb07a75e-898a-4891-80cf-b9e40403cf54.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

-------------

.. image:: https://user-images.githubusercontent.com/14288520/189998531-b384a5a5-1718-42c2-9c35-3d787a7681bb.png
  :target: https://user-images.githubusercontent.com/14288520/189998531-b384a5a5-1718-42c2-9c35-3d787a7681bb.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

-------------

.. image:: https://user-images.githubusercontent.com/14288520/189999818-9a89e298-4984-465e-8601-9a73ef645129.png
  :target: https://user-images.githubusercontent.com/14288520/189999818-9a89e298-4984-465e-8601-9a73ef645129.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`

