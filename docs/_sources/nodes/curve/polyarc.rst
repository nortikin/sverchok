Poly Arc
========

.. image:: https://user-images.githubusercontent.com/14288520/205465202-a89e0877-a7e3-4528-bce0-d69302bfd21b.png
  :target: https://user-images.githubusercontent.com/14288520/205465202-a89e0877-a7e3-4528-bce0-d69302bfd21b.png

Functionality
-------------

This node generates a Curve, which goes through the specified points, made of
series of circular arcs and straight line segments. Arcs are created so that
they touch smoothly in their meeting points. User can specify the tangent
vector of the curve at it's starting point. If such tangent vector is not
specified, the node will calculate it automatically by some algorithm.

.. image:: https://user-images.githubusercontent.com/14288520/205465625-aa629471-e74d-445f-8dd4-24f692b53b3e.png
  :target: https://user-images.githubusercontent.com/14288520/205465625-aa629471-e74d-445f-8dd4-24f692b53b3e.png

Inputs
------

This node has the following inputs:

* **Vertices**. List of points to build a curve through. This input is mandatory.
* **Tangent**. Tangent vector of the curve at it's starting point. This input
  is optional. If not connected, the node will calculate it on it's own.

.. image:: https://user-images.githubusercontent.com/14288520/205465780-d781149b-192b-44c9-9a92-0097b3e6b3fd.png
  :target: https://user-images.githubusercontent.com/14288520/205465780-d781149b-192b-44c9-9a92-0097b3e6b3fd.png

Parameters
----------

This node has the following parameters:

* **Concatenate**. If checked, the node will concatenate all arcs into one
  Curve object. Otherwise, it will output separate Curve object for each arc.
  Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205465992-e11a23e4-74c1-4cfb-8a6e-ff15d11daba0.png
  :target: https://user-images.githubusercontent.com/14288520/205465992-e11a23e4-74c1-4cfb-8a6e-ff15d11daba0.png

* **Cyclic**. If checked, the node will generate closed (cyclic) curve, by
  connecting the last vertex to the first. Note that the curve will most
  probably be not smooth at that closing point. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205466107-c279ab63-402a-487f-b0bd-c71c68f30a8b.gif
  :target: https://user-images.githubusercontent.com/14288520/205466107-c279ab63-402a-487f-b0bd-c71c68f30a8b.gif

* **NURBS output**. This parameter is available in the N panel only. If
  checked, the node will output a NURBS curve. Built-in NURBS maths
  implementation will be used. If not checked, the node will output generic
  concatenated curve from several straight segments and circular arcs. In most
  cases, there will be no difference; you may wish to output NURBS if you want
  to use NURBS-specific API methods with generated curve, or if you want to
  output the result in file format that understands NURBS only. Unchecked by
  default.

.. image:: https://user-images.githubusercontent.com/14288520/205466224-98d5b3bb-f7a6-4fa6-829b-8d19bade3da0.png
  :target: https://user-images.githubusercontent.com/14288520/205466224-98d5b3bb-f7a6-4fa6-829b-8d19bade3da0.png

Outputs
-------

This node has the following outputs:

* **Curve**. Generated Curve object.
* **Center**. Centers of generated circular arcs, together with their orientation.
* **Radius**. Radiuses of generated circular arcs.
* **Angle**. Angles of generated circular arcs, in radians.

.. image:: https://user-images.githubusercontent.com/14288520/205466946-b95685e8-d714-44cc-a270-eefbc56e0dac.png
  :target: https://user-images.githubusercontent.com/14288520/205466946-b95685e8-d714-44cc-a270-eefbc56e0dac.png


Examples of usage
-----------------

A simple example with specified starting tangent vector:

.. image:: https://user-images.githubusercontent.com/14288520/205482369-0e1d819d-738f-477d-9708-d326c4c1753b.png
  :target: https://user-images.githubusercontent.com/14288520/205482369-0e1d819d-738f-477d-9708-d326c4c1753b.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

An example of closed polyarc curve (note that it is not smooth at the closing point):

.. image:: https://user-images.githubusercontent.com/14288520/205482545-7f3a5c5f-7049-4763-a8e9-74be477ea7bc.png
  :target: https://user-images.githubusercontent.com/14288520/205482545-7f3a5c5f-7049-4763-a8e9-74be477ea7bc.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

The curve is not necessarily should be flat:

.. image:: https://user-images.githubusercontent.com/14288520/205482896-94434842-8621-4eda-96b2-752e0beef814.gif
  :target: https://user-images.githubusercontent.com/14288520/205482896-94434842-8621-4eda-96b2-752e0beef814.gif