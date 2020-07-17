
Scalar Fields
-------------

A scalar field is a mathematical object, which is defined as a function from R^3 to R, i.e. a mapping which maps each point in a 3D space to some number. Such objects are quite common in mathematics and in physics too; for example, you can take a field of temperatures (which maps each point to the temperature in that point).

Technically, scalar field is defined as Python class, which can calculate some number for a provided point in space. Note that the definition of the field function can be quite complex, but it does not mean that that complex definition will be executed for all points in 3D space — only for points for which it is actually required to know the value.

Sverchok can generate such fields by several ways, including user-provided formulas; it can execute some mathematical operations on them (such as addition or multiplication).

Vector Fields
-------------

A vector field is a mathematical object, which is defined as a function from R^3 to R^3, i.e. a mapping which maps each point in 3D space into a 3D vector. Such objects are very common in mathematics and in physics; for example, consider the field of some force, for example the gravitation field, which defines the gravitation force vector for each point in space.

Note that when we are talking about vector fields, there are two possible ways to interpret their values:

1. to think that the vector, which is defined by vector field in point P, starts in point P and ends in some point P';
2. to think that the vector which is defined by vector field in point P, starts in the origin and ends in some point Q.

In physics, the first approach is the most common, and it is mostly used by Sverchok.

One can note, that both approaches are easily convertible: if you have a field, which maps point P to a vector from 0 to Q, then you can say that you have a field which maps point P to a vector from P to (P+Q). Or the other way around, if you have a field which maps point P to a vector from P to P', then you can say that you have a field which maps point P to a vector from 0 to (P' - P).

"Apply vector field" node follows the first approach, i.e. for each provided point P it returns the point to which P would be mapped if we understand that the vector VectorField(P) starts at P. Mathematically, it returns `P + VectorField(P)`. In most cases, you will want to use this node instead of "evaluate vector field".

"Evaluate vector field" node, on the other hand, follows the second approach, i.e. for each point P it returns VectorField(P).

We will call fields that are "designed" to work with "Apply vector field" - "Relative vector fields", or "Bound vector fields". Fields "designed" to work with "Evaluate vector field" we will call "Absolute vector fields", or "Free vector fields".

Technically, vector field is a Python class that can be asked to return a vector for any 3D point. Note that the definition of the field function can be quite complex, but it does not mean that that complex definition will be executed for all points in 3D space — only for points for which it is actually required to know the value.

Sverchok can generate such fields by several ways, including user-provided formulas; it can execute some mathematical operations on them (such as addition or multiplication). Vector field can be applied to some set of vertices to receive another one — i.e., deform some mesh by field. There are also several ways to convert vector fields to scalar fields (for example, you can take a norm of the vector field, or use divergence differential operator).

