Sort Curves
===========

.. image:: https://user-images.githubusercontent.com/14288520/211191173-5dfa0ee3-9daa-4d08-beea-87288b3ace26.png
  :target: https://user-images.githubusercontent.com/14288520/211191173-5dfa0ee3-9daa-4d08-beea-87288b3ace26.png

Functionality
-------------

This node sorts (reorders) a list of Curve objects so that they could
potentially be concatenated together, i.e. so that the end point of each curve
would be near the beginning of the following curve. **NOTE**: this node does
not change shapes of curves, it only changes the order of curves. So, if start
/ end points of curves do not match, exact concatenation will not be possible
with any sorting.

Optionally, this node can reverse the direction of some curves to find the best
order of curves concatenation. For example, if in general start / end points of
curves were already matching, but some of curves in the input list had
incorrect direction, this node will be able to find such curves and reverse
them.

The first curve in the list will remain on it's place in any case, and it's
direction will not be changed.

.. image:: https://user-images.githubusercontent.com/14288520/211217157-76fd6a0f-eee6-4309-8f76-c5a373855668.png
  :target: https://user-images.githubusercontent.com/14288520/211217157-76fd6a0f-eee6-4309-8f76-c5a373855668.png

Calculation time is *O(N^2)*, where N is the number of curves, so if you have a
lot of curves to sort, you may want to consider other options, for example if
you have a way to generate curves in the correct order in the first place.

Inputs
------

This node has the following input:

* **Curves**. The list of curves to be sorted. This input is mandatory.

Parameters
----------

This node has the following parameter:

* **Allow Reverse**. If checked, then in addition to reordering the list of
  curves, the node will also try to reverse some of them, in order to find the
  best concatenation sequence. This, off course, will take additional time.
  Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Curves**. Reordered list of curves. If **Allow Reverse** parameter is
  checked, then directions of some of these curves are probably reversed.
* **Indexes**. Indexes of output curves in the input list.
* **FlipMask**. This output contains True for each curve in the **Curves**
  output, direction of which was reversed; for others it contains False.
* **SumError**. Total error of optimisation; more precisely, sum of squares of
  distances between the end of each curve and the beginning of the following -
  for the order of curves which was found the best. So if the node was able to
  find a sequence for precise concatenation of curves, this output will contain
  0.

.. image:: https://user-images.githubusercontent.com/14288520/211217426-bd0ca5e0-5bc5-456a-8fbb-bec85d9a5c6e.png
  :target: https://user-images.githubusercontent.com/14288520/211217426-bd0ca5e0-5bc5-456a-8fbb-bec85d9a5c6e.png

Example of Usage
----------------

Take a simple object (plane) from scene. It's edges are unordered, and
directions of these edges are random. Generate a Line curve segment from each
of these edges. Next we want to concatenate these lines to one Curve object. In
order to do this, we have to reorder line segments and reverse two of them.

.. image:: https://user-images.githubusercontent.com/14288520/211217751-7765bc54-526b-4542-a1cc-a87797734738.png
  :target: https://user-images.githubusercontent.com/14288520/211217751-7765bc54-526b-4542-a1cc-a87797734738.png

https://gist.github.com/f6c0c4b9c1d3075f99ce0d28583c5c5e

* Curves-> :doc:`Curve Endpoints </nodes/curve/endpoints>`
* Curves-> :doc:`Concatenate Curves </nodes/curve/concat_curves>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`