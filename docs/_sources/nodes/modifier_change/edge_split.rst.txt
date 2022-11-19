Split Edges
===========

.. image:: https://user-images.githubusercontent.com/14288520/200128313-beaf2178-fb18-4a82-a94c-f3db3e2b5ad9.png
  :target: https://user-images.githubusercontent.com/14288520/200128313-beaf2178-fb18-4a82-a94c-f3db3e2b5ad9.png

Functionality
-------------

This node splits each edge of the input mesh. It supports the following modes of operation:

* Split each edge in two. Place of split is defined by linear interpolation
  between two vertices of the edge with user-provided factor value.
* Split each edge in three. The edge is split in two places. Each vertex is
  offset from one of vertices of the edge by user-provided factor value.
* Split each edge in arbitrary number of pieces, by making several cuts. New vertices are placed evenly.

.. image:: https://user-images.githubusercontent.com/14288520/200128601-00df8252-5379-4f1e-b820-18c14a45fda7.png
  :target: https://user-images.githubusercontent.com/14288520/200128601-00df8252-5379-4f1e-b820-18c14a45fda7.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of the input mesh. This input is mandatory.
- **Edges**. Edges of the input mesh. This input is mandatory.
- **Faces**. Faces of the input mesh. This input is optional.
- **EdgeMask**. The mask defining which edges must be split. By default, the
  node splits all edges of the mesh.
- **Factor**. This defines where each edge must be split. The default value is 0.5.

   * If **Mode** parameter is set to **Simple**, then place of split is defined by
     linear interpolation between two vertices of the edge. Values of Factor
     near 0 mean the split point will be near first vertex of the edge, and
     values near 1 mean the split point will be near the second vertex of the
     edge.
   * If **Mode** parameter is set to **Mirror**, then each edge will be split in two
     places. Each place is defined by linear interpolation between one of
     vertices of the edge and the middle point of the edge. Values of factor
     near 0 will mean split points will be near vertices of the edge. Values of
     factor near 1 will mean split points will be near the middle of the edge.
   * Otherwise, this input is not available.
- **Cuts**. This input is available only when **Mode** parameter is set to
  **Multiple**. Number of cuts (new vertices) to make at each edge.
  Correspondingly, number of pieces into which each edge is split is defined as
  ``Cuts + 1``. Set this to 0 to do not split edges. The default value is 1
  (split each edge in two equal pieces).

Parameters
----------

This node has the following parameter:

- **Mode**. The following options are available:

  * **Simple**. Each edge will be split in one place.
  * **Mirror**. Each edge will be split in two places, symmetrical with respect
    to the middle of the edge.
  * **Multiple**. Each edge will be split in several places. Number of cuts is
    defined by **Cuts** input.

  The default option is **Simple**.

.. image:: https://user-images.githubusercontent.com/14288520/201472654-55398ec8-d437-44be-8d77-1f023695b0e2.png
  :target: https://user-images.githubusercontent.com/14288520/201472654-55398ec8-d437-44be-8d77-1f023695b0e2.png

.. image:: https://user-images.githubusercontent.com/14288520/201472763-44e8782e-50ae-4b0b-9aa4-7c75e1bcfab6.png
  :target: https://user-images.githubusercontent.com/14288520/201472763-44e8782e-50ae-4b0b-9aa4-7c75e1bcfab6.png

.. image:: https://user-images.githubusercontent.com/14288520/201472839-2662621f-f2d6-4fb5-aa04-d48108d30e2c.png
  :target: https://user-images.githubusercontent.com/14288520/201472839-2662621f-f2d6-4fb5-aa04-d48108d30e2c.png

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the output mesh.
* **Edges**. Edges of the output mesh.
* **Faces**. Faces of the output mesh. This output is empty if **Faces** input
  is not connected.

Examples
--------

Split even edges

.. image:: https://user-images.githubusercontent.com/14288520/200129550-d9c578a3-4f61-4ae2-98ee-24521f8adc6e.png
  :target: https://user-images.githubusercontent.com/14288520/200129550-d9c578a3-4f61-4ae2-98ee-24521f8adc6e.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* MODULE: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* EQUAL: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`