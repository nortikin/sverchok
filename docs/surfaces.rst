
Surface
-------

Sverchok uses the term **Surface** mostly in the same way it is used in mathematics.

From the user perspective, a Surface object is just some (more or less smooth)
surface laying in 3D space, which has some boundary. It may appear that
boundary of the surface from one side coincides with the boundary of the
surface from another side; in such case we say the surface is **closed**, or
**cyclic** in certain direction. Examples of closed surfaces are:

* Cylindrical surface (closed in one direction);
* Toroidal surface (closed in two directions);
* Sphereical surface (closed in two directions).

The simples example of non-closed (open) surface is a unit square.

You will find that the Surface object has a lot in common with Curve object.
One may say, that Surface is almost the same as Curve, just it is a 2D object
rather than 1D.

Mathematically, a Surface is a set of points in 3D space, which can be defined
as a codomain of some function from R^2 to R^3; i.e. the function, which maps
each point on 2D plane to some point in 3D space. We will be considering only
"good enough" functions - continuous and having at least one derivative at each
point.

It is important to understand, that each surface can be defined by more than
one function (which is called parametrization of curve). We usually use the one
which is most fitting our goals in specific task.

We usually use the letters **u** and **v** for curve parameters.

Excercise for the reader: write down several possible parametrization for the
unit square surface, which has corners `(0, 0, 0)`, `(0, 1, 0)`, `(1, 1, 0)`,
`(1, 0, 0)`.

The range of the surface parameters corresponding to the whole surface within
it's boundaries (in specific parametrization) is called **surface domain**. The
same surface can have different domains in different parametrizations.

Similar to curves, the values of surface parameters have nothing to do with
distances or areas, which are covered by points on the surface.

Since Blender has mostly a mesh-based approach to modelling, as well as
Sverchok, to "visualize" the Surface object you have to convert it to mesh. It
is usually done by use of "Evaluate Surface" node.

