List Repeater
=============

.. image:: https://user-images.githubusercontent.com/14288520/187916847-eddb3806-d466-4730-bcba-5cf71ff2bf9e.png
  :target: https://user-images.githubusercontent.com/14288520/187916847-eddb3806-d466-4730-bcba-5cf71ff2bf9e.png

Functionality
-------------

Allows explicit repeat of lists and elements. The node is *data type agnostic*, meaning it makes no assumptions about the data you feed it. It should accepts any type of data native to Sverchok..

Inputs
------

+--------+--------------------------------------------------------------------------+
| Input  | Description                                                              |
+========+==========================================================================+
| Data   | The data - can be anything                                               |
+--------+--------------------------------------------------------------------------+
| Number | The amount of times to repeat elements selected by the `Level` parameter |
+--------+--------------------------------------------------------------------------+

Parameters
----------

Level and unwrap.

**Level**

It is essentially how many chained element look-ups you do on a list. If ``SomeList`` has a considerable *nestedness* then you might access the most atomic element of the list doing ``SomeList[0][0][0][0]``. Levels in this case would be 4.

**unwrap**

Removes any extra layers of wrapping (brackets or parentheses) found at the current Level. If the element pointed at is ``[[0,2,3,2]]``  it will become ``[0,2,3,2]``.


Outputs
-------

* **Lists** (nested). The type of *Data out* will be appropriate for the operations defined by the parameters of the Node.

Examples
--------

Trying various inputs, adjusting the parameters, and piping the output to a *Debug Print* (or stethoscope) node will be the fastest way to acquaint yourself with the inner workings of the *List Repeater* Node.

.. image:: https://user-images.githubusercontent.com/14288520/187930209-252a899b-9db9-4125-8417-6d2d110ce40c.png
  :target: https://user-images.githubusercontent.com/14288520/187930209-252a899b-9db9-4125-8417-6d2d110ce40c.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/187932385-97321a1c-8a75-41bc-982a-59c420226aec.png
  :target: https://user-images.githubusercontent.com/14288520/187932385-97321a1c-8a75-41bc-982a-59c420226aec.png

* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Curves->Bezier-> :doc:`Bezier Spline (Curve) </nodes/curve/bezier_spline>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

A practical reason to use the node is when you need a series of copies of edge or polygon lists. Usually in conjunction with `Matrix Apply`, which outputs a series of `vertex lists` as a result of transform parameters.

.. image:: https://user-images.githubusercontent.com/14288520/187916873-4eb95b3a-ab51-451f-b45d-04c56714182e.png
  :alt: ListRepeater_Demo1.PNG
  :target: https://user-images.githubusercontent.com/14288520/187916873-4eb95b3a-ab51-451f-b45d-04c56714182e.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Vector-> :doc:`Vector X/Y/Z </nodes/vector/axis_input_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Transforms-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Modifiers->Modifier Change :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`