Approximate Bezier Curve
========================

.. image:: https://user-images.githubusercontent.com/14288520/206150256-a3a25c48-739e-48cb-921d-8b6b51242d27.png
  :target: https://user-images.githubusercontent.com/14288520/206150256-a3a25c48-739e-48cb-921d-8b6b51242d27.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node builds a Bezier_ Curve object, which approximate the given set of
points, i.e. goes as close to them as possible while remaining a smooth curve.

.. _Bezier: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

.. image:: https://user-images.githubusercontent.com/14288520/206152120-5c4cc61a-f70b-4256-9cb4-129e7445c596.png
  :target: https://user-images.githubusercontent.com/14288520/206152120-5c4cc61a-f70b-4256-9cb4-129e7445c596.png

Inputs
------

This node has the following inputs:

* **Vertices**. The points to be approximated. This input is mandatory.
* **Degree**. Degree of the curve to be build. The default value is 3.

.. image:: https://user-images.githubusercontent.com/14288520/206155176-3e326801-3326-442f-90ba-9a32d82aadc0.png
  :target: https://user-images.githubusercontent.com/14288520/206155176-3e326801-3326-442f-90ba-9a32d82aadc0.png

Parameters
----------

This node has the following parameter:

* **Metric**. This parameter is available in the N panel only. It defines the
  metric to be used for calculation of curve's T parameter which correspond to
  specified vertices. The default value is **Euclidean**. Usually you do not
  have to adjust this parameter.

.. image:: https://user-images.githubusercontent.com/14288520/206155856-4b9761b1-59d8-4581-972d-a2dfb8c1cf92.png
  :target: https://user-images.githubusercontent.com/14288520/206155856-4b9761b1-59d8-4581-972d-a2dfb8c1cf92.png

Outputs
-------

This node has the following outputs:

* **Curve**. The generated Bezier Curve object.
* **ControlPoints**. Control points of the generated curve.

.. image:: https://user-images.githubusercontent.com/14288520/206156177-bf190a41-c046-4b9e-b588-b3484799a30f.png
  :target: https://user-images.githubusercontent.com/14288520/206156177-bf190a41-c046-4b9e-b588-b3484799a30f.png

Example of usage
----------------

Take points from Greasepencil drawing and approximate them with a smooth curve (Annotations_):

.. image:: https://user-images.githubusercontent.com/14288520/206159158-fc4a6766-ff18-4417-814f-5797c0bc3bae.png
  :target: https://user-images.githubusercontent.com/14288520/206159158-fc4a6766-ff18-4417-814f-5797c0bc3bae.png

* BPY Data-> :doc:`Object ID Selector+ </nodes/object_nodes/get_asset_properties_mk2>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

.. _Annotations: https://docs.blender.org/manual/en/latest/interface/annotate_tool.html