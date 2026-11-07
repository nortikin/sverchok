Edgenet to Segments
===================

.. image:: https://github.com/user-attachments/assets/d0bc67f6-1f09-4455-9d5e-bff481cef164
  :target: https://github.com/user-attachments/assets/d0bc67f6-1f09-4455-9d5e-bff481cef164

Functionality
-------------

Splits each edgenet (mesh composed by verts and edges) in segments (sequences of ordered vertices) with knots in vertices intersection and angle change in paths

.. image:: https://github.com/user-attachments/assets/dd25e91a-3966-494d-b2d3-28d7be3c843b
  :target: https://github.com/user-attachments/assets/dd25e91a-3966-494d-b2d3-28d7be3c843b

Inputs
------

- **Vertices**
- **Edges**
- **Angle Threshold** - threshold for edge direction changes

Outputs
-------

- **Vertices**
- **Edges**
- **Lengths**: Lengths of segments to use in farthere interpolation of segments
- **Total length**: Total length (donno why user will need it, it was fast to calc)


Examples of usage
-----------------


.. image:: https://github.com/user-attachments/assets/4bba02bc-bdc6-4ce9-93fa-3f8ae0544f5b
  :target: https://github.com/user-attachments/assets/4bba02bc-bdc6-4ce9-93fa-3f8ae0544f5b

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------
