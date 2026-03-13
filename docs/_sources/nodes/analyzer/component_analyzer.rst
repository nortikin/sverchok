Component Analyzer
==================

.. image:: https://user-images.githubusercontent.com/14288520/194724104-e5ca2bfc-1659-445f-b62c-edbb3c760eff.png
  :target: https://user-images.githubusercontent.com/14288520/194724104-e5ca2bfc-1659-445f-b62c-edbb3c760eff.png

Functionality
-------------

This node allows to get the related data to mesh elements (vertices, edges and faces)

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Faces**

Parameters
----------

This node has the following parameters:

- **Mode**. This parameter defines what elements are you interested: **Vertices**, **Edges** or **Faces**.
- **Operator**. Criteria type to apply. Supported criteria set depends on Mode:

  * For **Vertices** supported criteria are:

    * **Normal**. :ref:`Vertices normal vector. Offers different calculation methods<VERTICES_NORMAL>`:

        * Bmesh (standard Blender)
        * Mean Weighted Equally (Faster)
        * Mean Weighted Based on Triangle Area
        * Mean Weighted Edge Length Reciprocal
        * Mean Weighted by Sine

    * **Matrix**: :ref:`Matrix aligned with normal<VERTICES_MATRIX>`.
    * **Sharpness**: :ref:`Curvature of mesh in vertex<VERTICES_SHARPNESS>`.
    * **Adjacent Edges**: :ref:`Adjacent edges<VERTICES_ADJACENT_EDGES>`.
    * **Adjacent Faces**: :ref:`Adjacent faces<VERTICES_ADJACENT_FACES>`.
    * **Adjacent Edges num**: :ref:`Number of Adjacent edges<VERTICES_ADJACENT_EDGES_NUM>`.
    * **Adjacent Faces num**: :ref:`Number of Adjacent faces<VERTICES_ADJACENT_FACES_NUM>`.
    * **Adjacent Edges Idx**: :ref:`Index of Adjacent edges<VERTICES_ADJACENT_EDGES_IDX>`.
    * **Adjacent Faces Idx**: :ref:`Index of adjacent faces<VERTICES_ADJACENT_FACES_IDX>`.
    * **Edges Angle**: :ref:`Angle between this vert's two connected edges<VERTICES_EDGES_ANGLE>`.
    * **Is Boundary**: :ref:`Is Vertex on mesh borders<VERTICES_IS_BOUNDARY>`.
    * **Is Manifold**: :ref:`Is Vertex part of the Manifold<VERTICES_IS_MANIFOLD>`.
    * **Is Wire**: :ref:`Is vertex only connected by edges<VERTICES_IS_WIRE>`.
    * **Is Interior**: :ref:`Is Vertex on mesh interior<VERTICES_IS_INTERIOR>`.


  * For **Edges**, supported criteria are:

    * **Geometry**. :ref:`Geometry of each edge. (explode)<EDGES_GEOMETRY>`.
    * **Direction**. :ref:`Normalized edge direction<EDGES_DIRECTION>`.
    * **Center**. :ref:`Edges Midpoint<EDGES_CENTER>`.
    * **Origin**. :ref:`Edges First point<EDGES_ORIGIN>`.
    * **End**. :ref:`Edges End point<EDGES_END>`.
    * **Normal**. :ref:`Edge Normal<EDGES_NORMAL>`.
    * **Matrix**. :ref:`Matrix aligned with edge<EDGES_MATRIX>`.
    * **Matrix Normal**. :ref:`Matrix aligned with edge and edge normal (needs faces)<EDGES_MATRIX_NORMAL>`.
    * **Length**. :ref:`Edge length<EDGES_LENGTH>`.
    * **Sharpness**. :ref:`Average of curvature of mesh in edges vertices<EDGES_SHARPNESS>`.
    * **Face Angle**. :ref:`Edges faces angle<EDGES_FACE_ANGLE>`.
    * **Inverted**. :ref:`Reversed edges<EDGES_INVERTED>`.
    * **Adjacent faces**. :ref:`Adjacent faces<EDGES_ADJUCENT_FACES>`.
    * **Connected edges**. :ref:`Edges connected to each edge<EDGES_CONNECTED_EDGES>`.
    * **Adjacent faces Num**. :ref:`Adjacent faces number<EDGES_ADJACENT_FACES_NUM>`.
    * **Connected edges Num**. :ref:`Connected edges number<EDGES_CONNECTED_EDGES_NUM>`.
    * **Adjacent faces Idx**. :ref:`Adjacent faces Index<EDGES_ADJACENT_FACES_IDX>`.
    * **Connected edges Idx**. :ref:`Connected edges Index<EDGES_CONNECTED_EDGES_IDX>`.
    * **Is Boundary**. :ref:`Is Edge on mesh borders<EDGES_IS_BOUNDARY>`.
    * **Is Interior**. :ref:`Is Edge part of manifold<EDGES_IS_INTERIOR>`.
    * **Is Contiguous**. :ref:`Is Edge contiguous<EDGES_IS_CONIGUOUS>`.
    * **Is Convex**. :ref:`Is Edge Convex<EDGES_IS_CONVEX>`.
    * **Is Concave**. :ref:`Is Edge Concave<EDGES_IS_CONCAVE>`.
    * **Is Wire**. :ref:`Has no related faces<EDGES_IS_WIRE>`.

  * For **Faces**, supported criteria are:

    * **Geometry**. :ref:`Geometry of each face. (explode)<FACES_GEOMETRY>`
    * **Center**. :ref:`Center of each face<FACES_CENTER>`.
       * **Center Bounds**. Center of bounding box of faces.
       * **Center Median**. Mean of vertices of each face.
       * **Center Median Weighted**. Mean of vertices of each face weighted by edges length.
    * **Normal**. :ref:`Normal of faces<FACES_NORMAL>`.
    * **Normal Absolute**. :ref:`Median Center + Normal<FACES_NORMAL_ABSOLUTE>`.
    * **Tangent** :ref:`Tangent<FACES_TANGENT>`.
       * **Tangent edge**. Face tangent based on longest edge.
       * **Tangent edge diagonal**. Face tangent based on the edge farthest from any vertex.
       * **Tangent edge pair**. Face tangent based on the two longest disconnected edges.
       * **Tangent vert diagonal**. Face tangent based on the two most distant vertices.
       * **Center-Origin**. Face tangent based on the mean center and first corner.
    * **Matrix**. :ref:`Matrix aligned with face<FACES_MATRIX>`.
    * **Area**. :ref:`Area of faces<FACES_AREA>`.
    * **Perimeter**. :ref:`Perimeter of faces<FACES_PERIMETER>`.
    * **Sides Number**. :ref:`Sides of faces<FACES_SIDES_NUMBER>`.
    * **Adjacent Faces Num**. :ref:`Number of Faces that share a vertex with face<FACES_ADJACENT_FACES_NUM>`.
    * **Neighbor Faces Num**. :ref:`Number of Faces that share a edge with face<FACES_NEIGHTOR_FACES_NUM>`.
    * **Sharpness**. :ref:`Average of curvature of mesh in faces vertices<FACES_SHARPNESS>`.
    * **Inverse**. :ref:`Reversed Polygons (Flipped)<FACES_INVERSE>`.
    * **Edges**. :ref:`Face Edges<FACES_EDGES>`.
    * **Adjacent Faces**. :ref:`Faces that share a edge with face<FACES_ADJACENT_FACES>`.
    * **Neighbor Faces**. :ref:`Faces that share a vertex with face<FACES_NEIGHBOR_FACES>`.
    * **Adjacent Faces Idx**. :ref:`Index of Faces that share a vertex with face<FACES_ADJACENT_FACES_IDX>`.
    * **Neighbor Faces Idx**. :ref:`Index of Faces that share a edge with face<FACES_NEIGHBOR_FACES_IDX>`.
    * **Is Boundary**. :ref:`Is the face boundary or interior<FACES_IS_BOUNDARY>`.


* **Output Parameters**: Depending on output nature (if offers multiple results per component or single result) the node offers one of this parameters.

  * **Split Output**. Split the result to get one object per result *[[0, 1], [2]] --> [[0], [1], [2]]*
  * **Wrap Output**. Keeps original data shape *[Matrix, Matrix, Matrix] --> [[Matrix, Matrix], [Matrix]]*

- Some routines offer *Output Numpy* property to output numpy arrays in stead of regular python lists (making the node faster)

---------

Vertices
--------

.. _VERTICES_NORMAL:

---------


Vertices-Normal
---------------

Vertices normal vector. Offers different calculation methods:

    * Bmesh (standard Blender). Slower (Legacy)
    * Mean Weighted Equally (Faster)
    * Mean Weighted Based on Triangle Area
    * Mean Weighted Edge Length Reciprocal
    * Mean Weighted by Sine

.. image:: https://user-images.githubusercontent.com/14288520/194768660-e2588833-1175-4e29-903a-c54cb8f43e9c.png
  :target: https://user-images.githubusercontent.com/14288520/194768660-e2588833-1175-4e29-903a-c54cb8f43e9c.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _VERTICES_MATRIX:

Vertices-Matrix
---------------

Matrix aligned with normal.

.. image:: https://user-images.githubusercontent.com/14288520/194768847-300b2d0a-77a7-4d0a-998e-061f2a2f6111.png
  :target: https://user-images.githubusercontent.com/14288520/194768847-300b2d0a-77a7-4d0a-998e-061f2a2f6111.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _VERTICES_SHARPNESS:

Vertices-Sharpness
------------------

Curvature of mesh in vertex.

.. image:: https://user-images.githubusercontent.com/14288520/194769012-01b3545e-a9dd-4467-b12a-082989c63ae0.png
  :target: https://user-images.githubusercontent.com/14288520/194769012-01b3545e-a9dd-4467-b12a-082989c63ae0.png

---------

.. _VERTICES_ADJACENT_EDGES:

Vertices - Adjacent Edges
-------------------------

.. image:: https://user-images.githubusercontent.com/14288520/194756122-8ceab86c-d94a-4857-aaff-91d786cdb83f.png
  :target: https://user-images.githubusercontent.com/14288520/194756122-8ceab86c-d94a-4857-aaff-91d786cdb83f.png

---------

.. _VERTICES_ADJACENT_FACES:

Vertices - Adjacent Faces
-------------------------

.. image:: https://user-images.githubusercontent.com/14288520/194756573-dbce801c-9c16-4ae6-9d37-2168c4490e5c.png
  :target: https://user-images.githubusercontent.com/14288520/194756573-dbce801c-9c16-4ae6-9d37-2168c4490e5c.png

---------

.. _VERTICES_ADJACENT_EDGES_NUM:

Vertices - Adjacent Edges num
-----------------------------

Number of Adjacent edges.

.. image:: https://user-images.githubusercontent.com/14288520/195196810-4f75b702-f8a0-49fa-8943-6967c01d629b.png
  :target: https://user-images.githubusercontent.com/14288520/195196810-4f75b702-f8a0-49fa-8943-6967c01d629b.png

---------

.. _VERTICES_ADJACENT_FACES_NUM:

Vertices - Adjacent Faces num
-----------------------------

Number of adjacent faces.

.. image:: https://user-images.githubusercontent.com/14288520/194769464-423f8c2f-b5a0-4686-a43c-183c415c31d6.png
  :target: https://user-images.githubusercontent.com/14288520/194769464-423f8c2f-b5a0-4686-a43c-183c415c31d6.png

---------

.. _VERTICES_ADJACENT_EDGES_IDX:

Vertices - Adjacent Edges Idx
-----------------------------

Index of Adjacent edges.

.. image:: https://user-images.githubusercontent.com/14288520/194769669-cd52f9a9-33cf-49f1-940b-906275d7d199.png
  :target: https://user-images.githubusercontent.com/14288520/194769669-cd52f9a9-33cf-49f1-940b-906275d7d199.png

---------

.. _VERTICES_ADJACENT_FACES_IDX:

Vertices - Adjacent Faces Idx
-----------------------------

Index of adjacent faces.

.. image:: https://user-images.githubusercontent.com/14288520/194770290-9680ac05-2226-4388-8a51-aa36146c17d0.png
  :target: https://user-images.githubusercontent.com/14288520/194770290-9680ac05-2226-4388-8a51-aa36146c17d0.png

---------

.. _VERTICES_EDGES_ANGLE:

Vertices - Edges Angle
----------------------

Angle between this vert's two connected edges. Else return -1.

.. image:: https://user-images.githubusercontent.com/14288520/194770458-fa4368bd-cef4-4aa7-81eb-610cd049067d.png
  :target: https://user-images.githubusercontent.com/14288520/194770458-fa4368bd-cef4-4aa7-81eb-610cd049067d.png

---------

.. _VERTICES_IS_BOUNDARY:

Vertices - Is Boundary
----------------------

Is Vertex on mesh borders.

.. image:: https://user-images.githubusercontent.com/14288520/194956735-8d172c37-bb75-466d-893e-2d246a593d32.png
  :target: https://user-images.githubusercontent.com/14288520/194956735-8d172c37-bb75-466d-893e-2d246a593d32.png

---------

.. _VERTICES_IS_MANIFOLD:

Vertices - Is Manifold
----------------------

Is Vertex part of the Manifold.

.. image:: https://user-images.githubusercontent.com/14288520/194956887-dd6ffb69-86ed-48f8-941c-7051c29cea46.png
  :target: https://user-images.githubusercontent.com/14288520/194956887-dd6ffb69-86ed-48f8-941c-7051c29cea46.png

---------

.. _VERTICES_IS_WIRE:

Vertices - Is Wire
------------------

Is vertex only connected by edges.

.. image:: https://user-images.githubusercontent.com/14288520/194957034-f1ad8c5c-c474-4578-839d-33ac62404abe.png
  :target: https://user-images.githubusercontent.com/14288520/194957034-f1ad8c5c-c474-4578-839d-33ac62404abe.png


---------

.. _VERTICES_IS_INTERIOR:

Vertices - Is Interior
----------------------

Is Vertex on mesh interior.

.. image:: https://user-images.githubusercontent.com/14288520/194957218-55d5ff0f-5a8e-4964-aaee-24de242920c7.png
  :target: https://user-images.githubusercontent.com/14288520/194957218-55d5ff0f-5a8e-4964-aaee-24de242920c7.png

---------

Edges
-----

.. _EDGES_GEOMETRY:

Edges - Geometry
----------------

Geometry of each edge. (explode).

.. image:: https://user-images.githubusercontent.com/14288520/194773553-cc9e2a73-bab6-44a1-a48c-7e2fa186c846.png
  :target: https://user-images.githubusercontent.com/14288520/194773553-cc9e2a73-bab6-44a1-a48c-7e2fa186c846.png

---------

.. _EDGES_DIRECTION:

Edges - Direction
-----------------

Normalized edge direction.

.. image:: https://user-images.githubusercontent.com/14288520/194780672-29407873-d34c-410c-95ab-4f765c06857d.png
  :target: https://user-images.githubusercontent.com/14288520/194780672-29407873-d34c-410c-95ab-4f765c06857d.png

---------

.. _EDGES_CENTER:

Edges - Center
--------------

Edges Midpoint.

.. image:: https://user-images.githubusercontent.com/14288520/194780946-97fe13a5-e133-4ea4-9530-61764772c7fc.png
  :target: https://user-images.githubusercontent.com/14288520/194780946-97fe13a5-e133-4ea4-9530-61764772c7fc.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _EDGES_ORIGIN:

Edges - Origin
--------------

Edges First point.

.. image:: https://user-images.githubusercontent.com/14288520/194782144-c74beffa-167f-4388-a413-29527bf03d49.png
  :target: https://user-images.githubusercontent.com/14288520/194782144-c74beffa-167f-4388-a413-29527bf03d49.png

---------

.. _EDGES_END:

Edges - End
-----------

Edges End point.

.. image:: https://user-images.githubusercontent.com/14288520/194782308-ada6d219-fb59-41e6-9949-74678382934c.png
  :target: https://user-images.githubusercontent.com/14288520/194782308-ada6d219-fb59-41e6-9949-74678382934c.png

---------

.. _EDGES_NORMAL:

Edges - Normal
--------------

Edge Normal

.. image:: https://user-images.githubusercontent.com/14288520/194829363-306ee46e-a9cd-40f1-ba98-547f2cd22251.png
  :target: https://user-images.githubusercontent.com/14288520/194829363-306ee46e-a9cd-40f1-ba98-547f2cd22251.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _EDGES_MATRIX:

Edges - Matrix
--------------

Matrix aligned with edge.

.. image:: https://user-images.githubusercontent.com/14288520/194838309-93e6c20a-c2e0-4bb4-be4b-0ab4663cdef6.png
  :target: https://user-images.githubusercontent.com/14288520/194838309-93e6c20a-c2e0-4bb4-be4b-0ab4663cdef6.png

.. image:: https://user-images.githubusercontent.com/14288520/194833014-bafbb153-f45d-40e2-aaa0-65863858cf5c.gif
  :target: https://user-images.githubusercontent.com/14288520/194833014-bafbb153-f45d-40e2-aaa0-65863858cf5c.gif

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _EDGES_MATRIX_NORMAL:

Edges - Matrix Normal
---------------------

Matrix aligned with edge and edge normal (needs faces).

.. image:: https://user-images.githubusercontent.com/14288520/194841026-1d2149f1-8fff-4a66-8eb2-a1c8803821bf.png
  :target: https://user-images.githubusercontent.com/14288520/194841026-1d2149f1-8fff-4a66-8eb2-a1c8803821bf.png

---------

.. _EDGES_LENGTH:

Edges - Length
--------------

Edge length.

.. image:: https://user-images.githubusercontent.com/14288520/194842208-b692b73c-7271-4ab4-9f17-2c2310906174.png
  :target: https://user-images.githubusercontent.com/14288520/194842208-b692b73c-7271-4ab4-9f17-2c2310906174.png

---------

.. _EDGES_SHARPNESS:

Edges - Sharpness
-----------------

Average of curvature of mesh in edges vertices.

.. image:: https://user-images.githubusercontent.com/14288520/194854190-4c7b3e87-3d84-43d7-bb67-a35f057fe418.png
  :target: https://user-images.githubusercontent.com/14288520/194854190-4c7b3e87-3d84-43d7-bb67-a35f057fe418.png

* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`

.. image:: https://user-images.githubusercontent.com/14288520/194855271-e2bb56d2-b888-4ebf-86f6-fa21d82d1bd9.gif
  :target: https://user-images.githubusercontent.com/14288520/194855271-e2bb56d2-b888-4ebf-86f6-fa21d82d1bd9.gif

---------

.. _EDGES_FACE_ANGLE:

Edges - Face Angle
------------------

Edges faces angle.

.. image:: https://user-images.githubusercontent.com/14288520/194857652-58815b0b-3ff1-42d8-a9cb-222eb6c0682c.png
  :target: https://user-images.githubusercontent.com/14288520/194857652-58815b0b-3ff1-42d8-a9cb-222eb6c0682c.png

* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`

---------

.. _EDGES_INVERTED:

Edges - Inverted
----------------

Reversed edges.

.. image:: https://user-images.githubusercontent.com/14288520/194862948-841b4fe2-3a25-4bac-ad7c-333e74e60561.png
  :target: https://user-images.githubusercontent.com/14288520/194862948-841b4fe2-3a25-4bac-ad7c-333e74e60561.png

---------

.. _EDGES_ADJUCENT_FACES:

Edges - Adjacent faces
----------------------

Adjacent faces.

.. image:: https://user-images.githubusercontent.com/14288520/194905469-ed6e1b53-ccdc-42c9-a615-f3fb36f7e896.png
  :target: https://user-images.githubusercontent.com/14288520/194905469-ed6e1b53-ccdc-42c9-a615-f3fb36f7e896.png

---------

.. _EDGES_CONNECTED_EDGES:

Edges - Connected edges
-----------------------

Edges connected to each edge.

.. image:: https://user-images.githubusercontent.com/14288520/194908721-55a07297-63fe-48a4-bd2e-a89ed5ce8ac8.png
  :target: https://user-images.githubusercontent.com/14288520/194908721-55a07297-63fe-48a4-bd2e-a89ed5ce8ac8.png

See
---

* List-> :doc:`Mask Converter </nodes/list_masks/mask_convert>`

---------

.. _EDGES_ADJACENT_FACES_NUM:

Edges - Adjacent faces Num
--------------------------

Adjacent faces number.

.. image:: https://user-images.githubusercontent.com/14288520/194912503-aacca85a-b097-44e9-9c73-19ca1eb5350c.png
  :target: https://user-images.githubusercontent.com/14288520/194912503-aacca85a-b097-44e9-9c73-19ca1eb5350c.png

---------

.. _EDGES_CONNECTED_EDGES_NUM:

Edges - Connected edges Num
---------------------------

Connected edges number.

.. image:: https://user-images.githubusercontent.com/14288520/194914550-8bf3b696-7a45-4a32-bac2-fbc838aedbf4.png
  :target: https://user-images.githubusercontent.com/14288520/194914550-8bf3b696-7a45-4a32-bac2-fbc838aedbf4.png

---------

.. _EDGES_ADJACENT_FACES_IDX:

Edges - Adjacent faces Idx
--------------------------

Adjacent faces Index.

.. image:: https://user-images.githubusercontent.com/14288520/194917091-790e2bcf-1b63-4a86-a872-8ecb3c0e43f5.png
  :target: https://user-images.githubusercontent.com/14288520/194917091-790e2bcf-1b63-4a86-a872-8ecb3c0e43f5.png

---------

.. _EDGES_CONNECTED_EDGES_IDX:

Edges - Connected edges Idx
---------------------------

Connected edges Index.

.. image:: https://user-images.githubusercontent.com/14288520/194924312-ccd28d94-219a-4940-bd47-a572a7b842ba.png
  :target: https://user-images.githubusercontent.com/14288520/194924312-ccd28d94-219a-4940-bd47-a572a7b842ba.png

---------

.. _EDGES_IS_BOUNDARY:

Edges - Is Boundary
-------------------
Is Edge on mesh borders.

.. image:: https://user-images.githubusercontent.com/14288520/194956371-07b9d194-5636-417f-93f4-ac95cb3b2177.png
  :target: https://user-images.githubusercontent.com/14288520/194956371-07b9d194-5636-417f-93f4-ac95cb3b2177.png

---------

.. _EDGES_IS_INTERIOR:

Edges - Is Interior
-------------------

Is Edge part of manifold.

.. image:: https://user-images.githubusercontent.com/14288520/194956237-8e614761-8e5a-4d86-b6c5-ce9066e26545.png
  :target: https://user-images.githubusercontent.com/14288520/194956237-8e614761-8e5a-4d86-b6c5-ce9066e26545.png

---------

.. _EDGES_IS_CONIGUOUS:

Edges - Is Contiguous
---------------------

Is Edge contiguous.

.. image:: https://user-images.githubusercontent.com/14288520/194956092-fbedde53-1da1-4bec-b672-7c933fa3097d.png
  :target: https://user-images.githubusercontent.com/14288520/194956092-fbedde53-1da1-4bec-b672-7c933fa3097d.png

---------

.. _EDGES_IS_CONVEX:

Edges - Is Convex
-----------------

Is Edge Convex.

.. image:: https://user-images.githubusercontent.com/14288520/194955931-a4757ee0-14ca-488c-8f0b-051d41ca02c6.png
  :target: https://user-images.githubusercontent.com/14288520/194955931-a4757ee0-14ca-488c-8f0b-051d41ca02c6.png

---------

.. _EDGES_IS_CONCAVE:

Edges - Is Concave
------------------

Is Edge Concave. (It is opposite of Convex)

.. image:: https://user-images.githubusercontent.com/14288520/194955618-d4ab1aa4-9e4a-4461-a89f-e55c45865849.png
  :target: https://user-images.githubusercontent.com/14288520/194955618-d4ab1aa4-9e4a-4461-a89f-e55c45865849.png

---------

.. _EDGES_IS_WIRE:

Edges - Is Wire
---------------

Has no related faces.

.. image:: https://user-images.githubusercontent.com/14288520/194955454-ddb7e21d-9d8e-4a50-8222-3d6958e8325b.png
  :target: https://user-images.githubusercontent.com/14288520/194955454-ddb7e21d-9d8e-4a50-8222-3d6958e8325b.png

---------

Faces
-----

.. _FACES_GEOMETRY:

Faces - Geometry
----------------

Geometry of each face. (explode)

.. image:: https://user-images.githubusercontent.com/14288520/195037856-40826018-19ae-4c19-9203-c60372803278.png
  :target: https://user-images.githubusercontent.com/14288520/195037856-40826018-19ae-4c19-9203-c60372803278.png

---------

.. _FACES_CENTER:

Faces - Center
--------------

       * **Center Bounds**. Center of bounding box of faces.
       * **Center Median**. Mean of vertices of each face.
       * **Center Median Weighted**. Mean of vertices of each face weighted by edges length.

.. image:: https://user-images.githubusercontent.com/14288520/195043348-3cf1952e-9aea-4d6c-8500-bec48de3686e.png
  :target: https://user-images.githubusercontent.com/14288520/195043348-3cf1952e-9aea-4d6c-8500-bec48de3686e.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _FACES_NORMAL:

Faces - Normal
--------------

Normal of faces.

.. image:: https://user-images.githubusercontent.com/14288520/195049179-0c3b919a-29cc-4ba1-b0be-a3e4dda6d066.png
  :target: https://user-images.githubusercontent.com/14288520/195049179-0c3b919a-29cc-4ba1-b0be-a3e4dda6d066.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _FACES_NORMAL_ABSOLUTE:

Faces - Normal Absolute
-----------------------

Median Center + Normal.

.. image:: https://user-images.githubusercontent.com/14288520/195052751-2ad46c0f-ce84-4045-90ec-d4017d2e5f64.png
  :target: https://user-images.githubusercontent.com/14288520/195052751-2ad46c0f-ce84-4045-90ec-d4017d2e5f64.png

---------

.. _FACES_TANGENT:

Faces - Tangent
---------------

       * **Tangent edge**. Face tangent based on longest edge.
       * **Tangent edge diagonal**. Face tangent based on the edge farthest from any vertex.
       * **Tangent edge pair**. Face tangent based on the two longest disconnected edges.
       * **Tangent vert diagonal**. Face tangent based on the two most distant vertices.
       * **Center-Origin**. Face tangent based on the mean center and first corner.

.. image:: https://user-images.githubusercontent.com/14288520/195100712-bdb0c083-f6eb-4564-a5f7-0dc5a1742c86.png
  :target: https://user-images.githubusercontent.com/14288520/195100712-bdb0c083-f6eb-4564-a5f7-0dc5a1742c86.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _FACES_MATRIX:

Faces - Matrix
--------------

Matrix aligned with face.

.. image:: https://user-images.githubusercontent.com/14288520/195119288-b1d8631e-1220-455e-83d9-e301fc78dd9b.png
  :target: https://user-images.githubusercontent.com/14288520/195119288-b1d8631e-1220-455e-83d9-e301fc78dd9b.png

**See also**:

* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`

---------

.. _FACES_AREA:

Faces - Area
------------

Area of faces

.. image:: https://user-images.githubusercontent.com/14288520/195124255-071d0524-50c2-44ad-9065-838f1576557e.png
  :target: https://user-images.githubusercontent.com/14288520/195124255-071d0524-50c2-44ad-9065-838f1576557e.png

See also:

* Analyzers-> :doc:`Area </nodes/analyzer/area>`

---------

.. _FACES_PERIMETER:

Faces - Perimeter
-----------------

Perimeter of faces

.. image:: https://user-images.githubusercontent.com/14288520/195137602-40855148-91a5-4837-911c-30c75ae4f1b1.png
  :target: https://user-images.githubusercontent.com/14288520/195137602-40855148-91a5-4837-911c-30c75ae4f1b1.png

---------

.. _FACES_SIDES_NUMBER:

Faces - Sides Number
--------------------

Sides of faces

.. image:: https://user-images.githubusercontent.com/14288520/195144476-db7bbcdd-5e83-44c4-9ff1-c55c06cf4ceb.png
  :target: https://user-images.githubusercontent.com/14288520/195144476-db7bbcdd-5e83-44c4-9ff1-c55c06cf4ceb.png

---------

.. _FACES_ADJACENT_FACES_NUM:

Faces - Adjacent Faces Num
--------------------------

Faces that share a edge with face.

.. image:: https://user-images.githubusercontent.com/14288520/195150475-b2ee2f4d-9cd5-48c2-8c0e-257941f39d43.png
  :target: https://user-images.githubusercontent.com/14288520/195150475-b2ee2f4d-9cd5-48c2-8c0e-257941f39d43.png

---------

.. _FACES_NEIGHTOR_FACES_NUM:

Faces - Neighbor Faces Num
--------------------------

Number of Faces that share a edge with face.

.. image:: https://user-images.githubusercontent.com/14288520/195152113-edc37237-9b95-4805-863c-8cb2cd79f470.png 
  :target: https://user-images.githubusercontent.com/14288520/195152113-edc37237-9b95-4805-863c-8cb2cd79f470.png

---------

.. _FACES_SHARPNESS:

Faces - Sharpness
-----------------

Average of curvature of mesh in faces vertices.

.. image:: https://user-images.githubusercontent.com/14288520/195155814-91e685e0-2844-426e-93d2-0e3046bc64b2.png
  :target: https://user-images.githubusercontent.com/14288520/195155814-91e685e0-2844-426e-93d2-0e3046bc64b2.png

---------

.. _FACES_INVERSE:

Faces - Inverse
---------------

Reversed Polygons (Flipped).

.. image:: https://user-images.githubusercontent.com/14288520/195158253-378aa5ad-1898-42ff-bc2a-37339a3ff2f2.png
  :target: https://user-images.githubusercontent.com/14288520/195158253-378aa5ad-1898-42ff-bc2a-37339a3ff2f2.png

---------

.. _FACES_EDGES:

Faces - Edges
-------------

Face Edges.

.. image:: https://user-images.githubusercontent.com/14288520/195161080-54d10265-06c4-4486-9c0e-3d327cb2fabd.png
  :target: https://user-images.githubusercontent.com/14288520/195161080-54d10265-06c4-4486-9c0e-3d327cb2fabd.png

---------

.. _FACES_ADJACENT_FACES:

Faces - Adjacent Faces
----------------------

Faces that share a edge with face.

.. image:: https://user-images.githubusercontent.com/14288520/195164387-ccdb956b-63a8-42c2-9db2-8ba3ba4f8e4b.png
  :target: https://user-images.githubusercontent.com/14288520/195164387-ccdb956b-63a8-42c2-9db2-8ba3ba4f8e4b.png

---------

.. _FACES_NEIGHBOR_FACES:

Faces - Neighbor Faces
----------------------

Faces that share a vertex with face.

.. image:: https://user-images.githubusercontent.com/14288520/195166317-8fec2612-eaf7-4a68-8c39-87b8ba99a4f1.png
  :target: https://user-images.githubusercontent.com/14288520/195166317-8fec2612-eaf7-4a68-8c39-87b8ba99a4f1.png

---------

.. _FACES_ADJACENT_FACES_IDX:

Faces - Adjacent Faces Idx
--------------------------

Index of Faces that share a vertex with face.

.. image:: https://user-images.githubusercontent.com/14288520/195168039-e6eaceae-361b-4a9a-9691-ecb8d5e0fc14.png
  :target: https://user-images.githubusercontent.com/14288520/195168039-e6eaceae-361b-4a9a-9691-ecb8d5e0fc14.png

---------

.. _FACES_NEIGHBOR_FACES_IDX:

Faces - Neighbor Faces Idx
--------------------------

Index of Faces that share a edge with face.

.. image:: https://user-images.githubusercontent.com/14288520/195169928-ed7a0433-a686-4fae-916e-b338015caecb.png
  :target: https://user-images.githubusercontent.com/14288520/195169928-ed7a0433-a686-4fae-916e-b338015caecb.png

---------

.. _FACES_IS_BOUNDARY:

Faces - Is Boundary
-------------------

Is the face boundary or interior

.. image:: https://user-images.githubusercontent.com/14288520/195173276-68980397-11e4-41ed-bf62-4440cbed4744.png
  :target: https://user-images.githubusercontent.com/14288520/195173276-68980397-11e4-41ed-bf62-4440cbed4744.png

---------

Example of usage
----------------

Component Matrix:

.. image:: https://user-images.githubusercontent.com/14288520/195290143-f5c2d8d7-402d-42d3-801c-fe1d07e96651.png
  :target: https://user-images.githubusercontent.com/14288520/195290143-f5c2d8d7-402d-42d3-801c-fe1d07e96651.png

* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Analyzers-> :ref:`Component Analyzer/Vertices/Matrix <VERTICES_MATRIX>`
* Analyzers-> :ref:`Component Analyzer/Edges/Matrix Normal <EDGES_MATRIX_NORMAL>`
* Analyzers-> :ref:`Component Analyzer/Faces/Matrix <FACES_MATRIX>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Component Sharpness:

.. image:: https://user-images.githubusercontent.com/14288520/195288780-7326b5d6-5b17-4ddc-8388-d87b0d97115e.png
  :target: https://user-images.githubusercontent.com/14288520/195288780-7326b5d6-5b17-4ddc-8388-d87b0d97115e.png

* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Analyzers-> :ref:`Component Analyzer/Vertices/Sharpness <VERTICES_SHARPNESS>`
* Analyzers-> :ref:`Component Analyzer/Edges/Sharpness <EDGES_SHARPNESS>`
* Analyzers-> :ref:`Component Analyzer/Faces/Sharpness <FACES_SHARPNESS>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* LESS, BIG Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Adjacent Edges, Faces Angle and Neighbor Faces Num:

.. image:: https://user-images.githubusercontent.com/14288520/195287717-da03aca8-1ec5-40d6-94c2-e377615aa774.png
  :target: https://user-images.githubusercontent.com/14288520/195287717-da03aca8-1ec5-40d6-94c2-e377615aa774.png

* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Analyzers-> :ref:`Component Analyzer/Vertices/Adjacent Edges Num <VERTICES_ADJACENT_EDGES_NUM>`
* Analyzers-> :ref:`Component Analyzer/Edges/Face Angle <EDGES_FACE_ANGLE>`
* Analyzers-> :ref:`Component Analyzer/Faces/Neighbor Faces Num <FACES_NEIGHTOR_FACES_NUM>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* LESS, BIG: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Edge Tools:

.. image:: https://user-images.githubusercontent.com/14288520/195286671-06504b9f-2cbf-40ae-9f5a-de5f7c2f0ec1.png
  :target: https://user-images.githubusercontent.com/14288520/195286671-06504b9f-2cbf-40ae-9f5a-de5f7c2f0ec1.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`2pt Quadratic Spline </nodes/generator/quad_spline>`
* Analyzers-> :ref:`Component Analyzer/Edges/Origin <EDGES_ORIGIN>`
* Analyzers-> :ref:`Component Analyzer/Edges/End <EDGES_FACE_ANGLE>`
* Analyzers-> :ref:`Component Analyzer/Edges/Center <EDGES_CENTER>`
* MUL, ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
