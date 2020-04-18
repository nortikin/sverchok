
Curve
-----

Sverchok uses the term **Curve** mostly in the same way as it is used in mathematics.

From the user perspective, a Curve object is just a (more or less smooth) curve
laying in 3D space, which goes from one point (start) to another point (end).
The start and the end point of the curve may coincide, in this case we say the
curve is **closed**, or **cyclic**.

Let's state some properties of the Curve object, which will define our
understanding of this term in context of Sverchok:

* A curve is a finite, one-dimensional object, existing in 3D space.
* Every curve must have exactly two endpoints. No more, no less.
* If the endpoints coincide, the curve is considered to be closed.
* There may be no gaps on the interior of a curve, as that would result in more
  than two endpoints.
* There may be no branching points on the curve, except where an endpoint is
  coincident with some interior point of the curve.

Mathematically, a Curve is a set of points in 3D space, which can be defined as
a codomain of some function from R to R^3; i.e. the function, which maps some
real number to a vector in 3D space. We will be considering only "good enough"
functions; more exactly, such function must be continuous, and have at least 3
derivatives at (mostly) each point.

It is important to understand, that each curve can be defined by more than one
function (which is called parameterization of the curve). We usually use the
one which is most fitting our goals in specific task.

Usually we use the letter **t** for curve parameter; in some case the letter **u** is used.

For example, let's consider a straight line segment, which is beginning at `(0,
0, 0)` and ending at `(1, 1, 1)`. The following parameterizations all define
the same line:

A)

      x(t) = t

      y(t) = t

      z(t) = t

B)
      x(t) = t^2

      y(t) = t^2

      z(t) = t^2

C)

      x(t) = t^3

      y(t) = t^3

      z(t) = t^3

As you understand, we can write down as many equations for it as we want.

Different parametrizations of the same curve can have different values of **t**
parameter corresponding to the beginning and the end of the curve. For example,

D)
      x(t) = t - 1

      y(t) = t - 1

      z(t) = t - 1

defines the parametrization, for which `t = 1` corresponds to the beginning of
the segment, and `t = 2` corresponds to the end of the segment. The range of
the curve parameter which corresponds to the curve from it's beginning to the
end is called **curve domain**.

Another important thing to understand is that the value of curve parameter at
some point has nothing to do with the length of the curve. With our straight
line example, if we consider A) parametrization at the point of `t = 0.5`, it
will be `(0.5, 0.5, 0.5)`, i.e. the middle of the segment. But, if we take the
same segment with B) parametrization, `t = 0.5` will give us `(0.25, 0.25,
0.25)`, which is not the middle of the segment at all.

Among all possible parametrizations of a curve, one is distinguished. It is
called **natural parametrization**. The natural parametrization of the curve
has the property: certain change in **t** parameter corresponds to exactly the
same change in curve length. Each curve has exactly one natural
parametrization.

Since Blender has mostly mesh-based approach to modelling, as well as Sverchok,
to "visualize" the Curve object, you have to convert it to mesh. It is usually
done by use of "Evaluate Curve" node, or "Curve Length Parameter" node.

