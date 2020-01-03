Adaptive Polygons Mk2
=====================

Functionality
-------------

This node puts a (transformed) copy of one object, called **donor**, along each
face of another object, called **recipient**. Copies of donor objects are
deformed (adapted) to match the shape and normals of recipient's face.

This node works primarily with Quads and Tris; if you ask it to work with NGons
(N > 4), it can produce weird resuls.

As an option, the node can process NGons (and Quads / Tris, optionally) in so
called "Frame / Fan" mode. In this mode, each face of recipient mesh is inset
by some amount, so it is replaced with a number of either Quads or Tris. Each
of such faces is then processed as usual.

Or one can pass recipient object through **Inset Special** node to achieve results
similar to Tissue's "Fan" or "Frame" modes.

In many cases it is good idea to pass the output of this node through **Remove
Doubles** node.

This node is based on original code taken with permission from
https://sketchesofcode.wordpress.com/2013/11/11/ by Alessandro Zomparelli
(sketchesofcode). Further features were developed after the Tissue addon by
Alessandro.

Inputs
------

This node has the following inputs:

- **VersR**. Vertices of the recipient object. This input is mandatory.
- **PolsR**. Faces of the recipient object. Please have in mind that order of
  indices in each face affect donor object rotation; for example, `[0, 1, 2,
  3]` is one rotation, `[3, 0, 1, 2]` is the same turned by 90 degrees. This
  input is mandatory. 
- **VersD**. Vertices of the donor object. This input is mandatory.
- **PolsD**. Faces of the donor object.
- **FaceDataD**. List containing an arbitrary data item for each face of donor
  object. For example, this may be used to provide material indexes of donor
  object faces. Optional input.
- **Width coeff**. Coefficient for donor object width (size along X,Y axis,
  usually). Default value is 1.0. The input expects one number per each
  recipient object face.
- **Frame width**. Width of frame for "Frame / Fan" mode. Maximum value of 1.0
  means that there will be no gap in the center of face, so this will be "Fan"
  mode. Default value is 0.5. This input is available only if **Frame mode**
  parameter is set to value other than **Do not use**.
- **Z coeff**. Coefficient for donor object size along recipient object face
  normal. Exact meaning depends on **Z Scale** parameter (see below). The
  default value is 1.0. The input expects one number per each recipient object face.
- **Z offset**. Offset of donor objects along the normal of recipient object
  face. Default value is 0.0. The input expects one number per each recipient
  object face.
- **Z Rotation**. Rotation of donor objects along the normal of recipient
  object face, in radians. Default value is 0.0. The input expects one number
  per each recipient object face.
- **PolyRotation**. Rotation of each recipient object face indexes. The default
  value is 0. For example, if recipient face definition is `[3, 4, 5, 6]`, and
  *PolyRotation* is set to 1, then the face will be interpreted as `[4, 5, 6,
  3]`. This will affect the orientation of donor object.
- **PolyMask**. Mask for recipient object faces processing. What exactly will
  be done with faces which are masked out is defined by **Mask Mode** parameter
  (see below).

Parameters
----------

This node has some number of parameters, and most of them are accessible only in the N panel:

- **Join**. If checked, then all procuced copies of donor object will be merged
  into one mesh. Unchecked by default.
- **Matching mode**. This defines how the list of donor objects is matched with list of recipient objects. Available values are:
  
   - **Match longest**. Each pair of recipient and donor objects will be
     processed. For example, if there are 2 recipient objects and 2 donor
     objects, you will have two outputs: `recipient[1] + donor[1]` and
     `recipient[2] + donor[2]`. If one of lists is shorter than another, the
     last object will be repeated as many times as necessary. For example, if
     there is 1 recipient object and 2 donor objects, you will have two
     outputs: `recipient[1] + donor[1]` and `recipient[1] + donor[2]`.
   - **Donor per face**. The list of donor objects will be treated as "one
     donor object per recipient object face". Number of outputs will be defined
     by number of recipient objects.

   The default value is **Match longest**.

- **Normal axis**. Axis of the donor object to be aligned with recipient object
  face normal. Available values are X, Y, and Z. Default value is Z.
- **Z Scale**. This defines how donor object size along recipient face normal
  is calculated. Available values are:

  - **Proportional**. Donor object size along recipient face normal is
    calculated by it's size along Z axis (or other one, defined by **Normal
    axis** parameter) multiplyed by value from **Z coeff** input.
  - **Constant**. Donor object size along recipient face normal is taken from
    **Z Coeff** input.
  - **Auto**. Calculate donor object scale along normal automatically, based on
    it's scale along two other axes. Multiply that automatically calculated
    value to the value taken from **Z Coeff** input.

  The default value is **Proportional**.

- **Use normals**. This defines how recipient object normals will be used to
  transform the donor objects. Available values are:

  - **Map**. Interpolation between recipient object's vertex normals will be
    used to deform the donor object. While this procuces smoother results, this
    gives more deformation of donor object.
  - **Face**. Recipient object's face normal will be used to orient the donor
    object. While this gives less deformation of donor object, it can give gaps
    between copies.

  The default value is **Map**.

- **Interpolate normals**. This parameter is available only if **Use normals**
  is set to **Map**. This defines the method of interpolation between recipient
  object's vertex normals. Available values are:

  - **Linear**. Linear interpolation will be used.
  - **Unit length**. Linear interpolation will be used, but the resulting
    normal will be resized to length of 1.0. This can give more smooth results
    in some cases.

  The default value is **Linear**.

- **Use shell factor**. If checked, each vertex normal will be multiplied by
  so-called "shell factor" - a multiplier calculated based on the sharpness of
  the vertex. Where a flat surface gives 1.0, and higher values sharper edges.
  When this parameter is checked, you will have more constant "thickness" of
  the resulting shape; when it is unchecked, the shape will tend to be more
  smooth. Unchecked by default.

- **Coordinates**. This defines the method of calculation of donor object's
  coordinates along two axes orthogonal to recipient's face normal. In any
  case, the location is defined by transforming some area of XOY plane (or
  other plane, according to **Normal axis** paramter), called *source area*, to
  the recipient object face. The question is what is the source area. The
  available values are:

  - **Bounds**. The source area is defined as follows:

    - For Quad recipient object faces, the bounding rectangle of donor object is taken.
    - For Tris recipient object faces, the bounding triangle of donor object is
      taken. The "bounding triangle" is defined as the smallest triangle, which
      covers all donor vertices while having bottom side parallel to X axis (or
      other axis according to **Normal axis** parameter). The triangle can be
      defined as either equilateral or rectangular, depending on **Bounding
      triangle** parameter.
  
  - **As Is**. The source area is defined as follows:

    - For Quad faces, the `[-1/2; 1/2] x [-1/2; 1/2]` unit square is taken.
    - For Tris faces, the unit triangle is taken. The triangle can be defined
      as equilateral or rectangular, depending on **Bounding triangle**
      parameter.

  Note that by definition of **Bounds** mode, the donor object always lies
  within the *source area*.

  The **As Is** mode allows one to manually transform the donor object before
  passing it to this node; interesting results may be achieved by making the
  donor object smaller than *source area*, or bigger than it, or even outside
  of it.

  The default value is **Bounds**.

- **Bounding triangle**. This defines the form of triangle to be used as base area (for tris faces). The available values are:

  - **Equilateral**. The base triangle will be defined as a triangle with all
    sides equal. When **Coordinates** parameter is set to **As Is**, this will
    be a triangle with center at `(0, 0, 0)` and a side of 1. In **Bounds**
    mode, this will be the bounding triangle.

  - **Rectangular**. The base triangle will be defined as a triangle with one
    angle equal to 90 degrees. When **Coordinates** parameter is set to **As
    Is**, this will be a triangle with center of it's hypotenuse at `(0, 0, 0)`
    and length of hypotenuse equal to 2. In **Bounds** mode, this will be the
    bounding triangle.
  
  Please see below for the illustrations of bounding triangles.
  The default value is **Equilateral**.

- **Frame mode**. This defines when to apply "Frame / Fan" mode. The available values are:

  - **Do not use**. Frame / fan mode will not be used.
  - **NGons only**. Frame / fan mode will be used for NGons (n > 4) only. Other
    faces will be processed in simple replacement mode.
  - **NGons and Quads**. Frame / fan mode will be used for NGons and Quads
    (i.e. n >= 4) only. Tris will be processed in simple replacement mode.
  - **Always**. Frame / fan mode will be used for all faces.

  The default value is **Do not use**.

  Note that "Frame / Fan" mode makes either several Quads (when FrameWidth <
  1.0) or several Tris (when FrameWidth == 1.0) out of each recipient face. How
  exactly these Quads and Tris will be processed is defined by **Faces mode**
  parameter.

- **Faces mode**. This defines how deformations of donor object will be
  calculated for Quad and Tris recipient faces. Available values are:

  - **Quads / Tris Auto**. For Quad faces, the linear transformation will be
    used. For Tris faces, the barycentric transformation will be used to
    transform source triangle into the recipient triangle. This method gives
    good and smooth results for both Quads and Tris.
  - **Quads Always**. In this mode, Tris faces are processed as if they were
    (degenerated) Quads with third and fourth vertices coinciding. Such
    transformation can make one corner of donor object sharper than others, and
    in some cases produce weird results for Tris. But such results can be
    interesting in some cases. Note that at the moment the Tissue addon always
    uses this mode.

  The default value is **Quads / Tris Auto**.

- **Mask mode**. This defines what to do with recipient objectfaces excluded by the
  **PolyMask** input. Available values are:

  - **Skip**. Such faces will be skipped completely, i.e. will not produce any
    vertices and faces.
  - **As Is**. Such faces will be output as they were, i.e. one face will be
    output for each recipient face.

  The default value is **Skip**.

- **NGons**. This defines what to do with NGon recipient object faces (i.e.
  faces with number of vertices more than 4). Available values are:

  - **As Quads**. Such faces will be processed as if they were quads; only
    first three and the last vertex of the NGon will be used to form a Quad.
    This can give weird results for such faces. 
  - **Skip**. Such faces will be skipped completely, i.e. will not produce any
    vertices and faces.
  - **As Is**. Such faces will be output as they were, i.e. one face will be
    output for each recipient face.

  The default value is **As Quads**.

Base area illustrations
-----------------------

The following illustration demonstrates the meaning of "bounding rectangle" term (it is used for Quads when **Coordinates** is set to **Bounds**):

.. image:: https://user-images.githubusercontent.com/284644/70073275-5e94eb00-161a-11ea-8bee-4166313f4cab.png

The following is the unit square (which is used for Quads when **Coordinates** is set to **As Is**):

.. image:: https://user-images.githubusercontent.com/284644/70073317-74a2ab80-161a-11ea-808a-6ea041cf7850.png

The following illustration demonstrates the meaning of term "bounding equilateral triangle" (it is used for Tris when **Coordinates** is set to **Bounds**, and **Bounding triangle** is set to **Equilateral**):

.. image:: https://user-images.githubusercontent.com/284644/70073381-99971e80-161a-11ea-9ffa-a8bee07b0536.png

The following is the unit equilateral triangle (it is used for Tris when **Coordinates** is set to **As Is**, and **Bounding triangle** is set to **Equilateral**):

.. image:: https://user-images.githubusercontent.com/284644/70073338-7ff5d700-161a-11ea-9e28-a50525cfe7bb.png

The following demonstrates the meaning of term "bounding rectangular triangle" (it is used for Tris when **Coordinates** is set to **Bounds**, and **Bounding triangle** is set to **Rectangular**):

.. image:: https://user-images.githubusercontent.com/284644/70073402-a7e53a80-161a-11ea-972f-04e9f76d54ae.png

The following is a "unit rectangular triangle" (it is used for Tris when **Coordinates** is set to **As Is**, and **Bounding triangle** is set to **Rectangular**):

.. image:: https://user-images.githubusercontent.com/284644/70073442-bcc1ce00-161a-11ea-84f1-1b544c4ab3dd.png

Outputs
-------

This node hsa the following outputs:

- **Vertices**
- **Polygons**
- **FaceData**. List of data items, which were provided in the **FaceDataD**
  input, containing one data item for each face of output mesh.
- **VertRecptIdx**. For each output vertex, this output contains an index of
  recipient object face, which was used to construct this output vertex.
- **FaceRecptIdx**. Foreach output face, this output contains an index of
  recipient object face, which was used to construct this output face.

The outputs will contain one object, if **Join** flag is checked, or one object
per recipient object face, otherwise.

Examples of usage
-----------------

Example of **Z coeff** input usage:

.. image:: https://user-images.githubusercontent.com/284644/68081971-5473a700-fe38-11e9-8f8a-dbd204bafadd.png

Demonstration of how this node works with Tris recipient faces by default (in **Quads / Tris Auto** mode):

.. image:: https://user-images.githubusercontent.com/284644/68081972-5473a700-fe38-11e9-8604-018e7b59996d.png

The same setup but with **Faces mode** set to **Quads Always**:

.. image:: https://user-images.githubusercontent.com/284644/68081973-5473a700-fe38-11e9-89f6-8e4b4330772a.png

In some cases iterative application can give interesting results:

.. image:: https://user-images.githubusercontent.com/284644/68075234-ee027080-fdc6-11e9-8192-61d0917d45f7.png

An example of **Frame** mode:

.. image:: https://user-images.githubusercontent.com/284644/68528852-d7ee3600-0319-11ea-81ba-14bdd6e36a8e.png

The same setup with **FrameWidth** set to 1.0 - the processing switches to **Fan** mode:

.. image:: https://user-images.githubusercontent.com/284644/68528834-b68d4a00-0319-11ea-89d7-5857c886d423.png

An example of **Rectangular** triangles usage:

.. image:: https://user-images.githubusercontent.com/284644/70074578-cba98000-161c-11ea-88dd-69336809a659.png

An example of "Use shell factor" parameter usage:

.. image:: https://user-images.githubusercontent.com/284644/71557169-3acf9400-2a64-11ea-85e6-b8301669745b.png

You can also find some more examples `in the development thread <https://github.com/nortikin/sverchok/pull/2651>`_.

