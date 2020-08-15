Rigid Origami
===========

Functionality
-------------

This node simulates rigid origami folding. This will treat a source paper as a flat rigid sheet and each edges inside the plane as hinges. 

This node generates folded origami shapes from source papers having some edges inside. Implementation of this node is mainly inspired in "Simulation of Rigid Origami" by Tomonori Tachi and the "New origami example" in Grasshopper. Each edge angles of the final results will be generated with large influences by the edge existenses and angles around them.

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of a plane (paper) object to be folded. This input and the edges and faces of the paper are mandatory.
- **Edges**. All edges of the target paper.
- **Faces**. All faces of the target paper. The normals of each polygons shold be the same direction when not folded.
- **Fold edge indices**. Indices of edges to be folded. These edges should be edges inside of a paper. If some of the edges inside are not included, those edge-angles are considered to be kept the same. If boundary edges are included, they are simply ignored.
- **Fold edge angles**. Edge angles of 'Fold edge indices'. Angles are designated with radian. Valley/Mountain angles are plus/minus values respectively. The number of the list items should be the same as the indices count.

Parameters
----------

This node has the following parameters:

- **Folding ratio**. Folding ratio from 0.0 to 1.0. Zero means the first state, and One represents the final state.
- **Division count**. When calculating the each edge angles, these angles will be divided with this number to get correct results. This count will affect the final shape. This will take from 1 to 100. When this count increases, the calculation will be generally more precise.
- **Fixed Face index**. This polygon will stay still when folded.

Outputs
-------

This node has the following outputs:

- **Vertices**. Vertices of the folded plane.

Examples of usage
-----------------

Twisted square folding.

.. image:: https://user-images.githubusercontent.com/64673405/90147680-661dae00-ddbd-11ea-96bb-0d29b9b8104d.png
  :alt: https://user-images.githubusercontent.com/64673405/90147680-661dae00-ddbd-11ea-96bb-0d29b9b8104d.png

Miura fold simulation.

.. image:: https://user-images.githubusercontent.com/64673405/90147700-6a49cb80-ddbd-11ea-9d57-07ae2880af8d.png
  :alt: https://user-images.githubusercontent.com/64673405/90147700-6a49cb80-ddbd-11ea-9d57-07ae2880af8d.png

Windmill.

.. image:: https://user-images.githubusercontent.com/64673405/90317118-23e1a180-df62-11ea-92aa-170079922ce7.png
  :alt: https://user-images.githubusercontent.com/64673405/90317118-23e1a180-df62-11ea-92aa-170079922ce7.png

