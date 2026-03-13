Nearest Point on Mesh
=====================

.. image:: https://user-images.githubusercontent.com/14288520/196508801-a7149ece-35a9-4f46-93fd-b3e4449fc2f2.png
  :target: https://user-images.githubusercontent.com/14288520/196508801-a7149ece-35a9-4f46-93fd-b3e4449fc2f2.png

.. image:: https://user-images.githubusercontent.com/14288520/196511961-63df5e7c-443a-43d3-a200-c29464f4334f.png
  :target: https://user-images.githubusercontent.com/14288520/196511961-63df5e7c-443a-43d3-a200-c29464f4334f.png

.. image:: https://user-images.githubusercontent.com/14288520/196512405-888ef444-d7e7-4741-a3c6-b85672d83bee.gif
  :target: https://user-images.githubusercontent.com/14288520/196512405-888ef444-d7e7-4741-a3c6-b85672d83bee.gif

Functionality
-------------

Finds the closest point in a specified mesh.

Inputs
------

Vertices, Faces: Base mesh for the search
Points: Points to query
Distance: Maximum query distance (only for Nearest in Range mode)

Parameters
----------

* **Mode**:
  
  - **Nearest**: Nearest point on the mesh surface
  - **Nearest in range**: Nearest points on the mesh within a range (one per face)
  
* **Flat Output**: (only in Nearest in Range) Flattens the list of every vertex to have only a list for every inputted list.
* **Safe Check**: (in N-Panel) When disabled polygon indices referring to unexisting points will crash Blender. Not performing this check makes node faster

Outputs
-------

* **Location**: Position of the closest point in the mesh
* **Normal**: mesh normal at closets point
* **Index**: Face index of the closest point
* **Distance**: Distance from the queried point to the closest point

Examples
--------

Used as skin-wrap modifier:

.. image:: https://user-images.githubusercontent.com/14288520/196513979-581eaac9-02d5-4390-b0f4-93c27b3e5906.png
  :target: https://user-images.githubusercontent.com/14288520/196513979-581eaac9-02d5-4390-b0f4-93c27b3e5906.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/196535057-49414fd8-f59f-4943-81a4-b9e2f5a6d78a.png
  :target: https://user-images.githubusercontent.com/14288520/196535057-49414fd8-f59f-4943-81a4-b9e2f5a6d78a.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Vector-> :doc:`Vector Lerp </nodes/vector/lerp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/196535560-ef622a57-ecdb-4741-9410-3df82ee13348.gif
  :target: https://user-images.githubusercontent.com/14288520/196535560-ef622a57-ecdb-4741-9410-3df82ee13348.gif

---------

Determine which polygons are nearer than a distance:

.. image:: https://user-images.githubusercontent.com/14288520/196544827-ba6f069d-3d8b-4786-80ae-468add944239.png
  :target: https://user-images.githubusercontent.com/14288520/196544827-ba6f069d-3d8b-4786-80ae-468add944239.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/196545316-1acd076d-37d6-4b90-a182-7235c8eef2ce.gif
  :target: https://user-images.githubusercontent.com/14288520/196545316-1acd076d-37d6-4b90-a182-7235c8eef2ce.gif

---------

Placing objects on mesh:

.. image:: https://user-images.githubusercontent.com/14288520/196542962-9ae63126-3ce8-4bc9-8c9b-662e3ef05b84.png
  :target: https://user-images.githubusercontent.com/14288520/196542962-9ae63126-3ce8-4bc9-8c9b-662e3ef05b84.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Normal </nodes/matrix/matrix_normal>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/196543406-38217fb4-6f65-4740-88cb-56dc268af55b.gif
  :target: https://user-images.githubusercontent.com/14288520/196543406-38217fb4-6f65-4740-88cb-56dc268af55b.gif