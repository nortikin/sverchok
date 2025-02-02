CSG Boolean MK2
===============

.. image:: https://user-images.githubusercontent.com/14288520/198852539-b0583c14-01a2-4cba-a8a1-fd8d872d7975.png
  :target: https://user-images.githubusercontent.com/14288520/198852539-b0583c14-01a2-4cba-a8a1-fd8d872d7975.png

Functionality
-------------

This node implements the 3 boolean *3d Mesh* functions; Intersect, Join, Difference. 

.. image:: https://user-images.githubusercontent.com/14288520/198852978-c958f428-50f0-43f0-9e88-50e315b510d9.png
  :target: https://user-images.githubusercontent.com/14288520/198852978-c958f428-50f0-43f0-9e88-50e315b510d9.png

There are switches and modes.

- Nested Accumulate (bool first two objects, then applies the rest to the result one by one.
- Only final result (output only last iteration result)

::|csg demo|

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

warnings
--------

This Boolean implementation is by no means fast, nor does it generate optimal output geometry. It is however often "correct". There are operational limitations to be aware of.

- Boolean algorithms are computationally expensive.
- the algorithm expects the input meshes to be both outward facing
- expects input meshes to be manifold ( no holes.. and also no intersecting or (self)overlapping geometry)
- co planar faces will result in undetermined output
- edges on one mesh should not be in the same 3d space as a face on the other mesh.

You might get error reports from the node along the lines of "float division by zero", in that scenario you should confirm that the state of your input meshes isn't in contradiction with the above mentioned bullet points. You can quickly test if a mesh has concident vertices (but isn't closed) by added a "Merge By Distance" node, prior to passing the mesh to csg boolean node. 

To perform calculations we use a library taken from Evan Wallace and ported to Python by Tim Knip. The original license of the library is this MIT::

    ## License
    Copyright (c) 2011 Evan Wallace (http://madebyevan.com/), under the MIT license.
    Python port Copyright (c) 2012 Tim Knip (http://www.floorplanner.com), under the MIT license.


Why add it if it's flawed?
--------------------------

Because when we omit such a node purely because it has a set of unfavorable edge cases, then we ignore the much larger parameter space in which such a node is adequate and sufficient for our needs. Here is the pullrequest that introduced this version of the node

https://github.com/nortikin/sverchok/pull/1575

Alternatives
------------

Consider booleans as "beta" in Sverchok. You might be interested in the FreeCAD implementation discussed here. https://github.com/nortikin/sverchok/issues/3430

.. |csg demo| image:: https://user-images.githubusercontent.com/14288520/198853352-112f44c9-0a3f-4cc4-8a24-9a930c900050.png
            :target: https://user-images.githubusercontent.com/14288520/198853352-112f44c9-0a3f-4cc4-8a24-9a930c900050.png
