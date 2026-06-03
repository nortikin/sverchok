EisenScript
==================

**EisenScript** is a procedural geometry scripting language based on L-systems.
It defines rules that recursively transform and branch geometric primitives
into complex structures — fractals, trees, architectural forms, and more.

EisenScript was originally implemented in StructureSynth; nowadays it has several implementations.

This node implements an extended version of EisenScript language. Additions are:

* `#input` definitions for externally controllable variables
* Possibility to do calculations; anywhere where in original EisenScript you
  could put a numeric literal, you can place an expression, like `(sin(x))`.
* Parametrized rules.

The node reads an EisenScript program from a Blender text block and outputs
placement matrices for each primitive type (box, sphere, grid, line, point,
triangle). Each output socket carries a list of 4×4 transformation matrices
that can be used with the **Matrix Transform** or **Objects In** nodes to
place actual geometry.

.. image:: https://github.com/user-attachments/assets/e1a247ee-9704-4b59-960d-b0ed8e8e8805
  :target: https://github.com/user-attachments/assets/e1a247ee-9704-4b59-960d-b0ed8e8e8805

Overview
--------

An EisenScript program consists of **rules**, **transformations**, **repetitions**,
and **primitives**. Rules define recursive patterns; transformations modify the
current coordinate frame; repetitions apply transformations multiple times; and
primitives emit geometric objects.

A simple program might look like this:

::

    set maxdepth 100
    rule trunk {
        {y 2} trunk
        {y 1 s 0.8} box
    }
    trunk

This defines a recursive "trunk" rule: each call translates up by 2 units and
recalls itself, and also spawns a scaled box. The result is a column of
successively smaller boxes.

Program Structure
-----------------

A program is a sequence of top-level statements processed in order:

* **Input directives** — ``#input`` declares runtime-configurable parameters.
* **Define directives** — ``#define`` declares named constants (numbers or
  Python expressions).
* **Set statements** — ``set`` configures global interpreter behavior.
* **Rule definitions** — ``rule name { ... }`` defines a named rule.
* **Bare branches** — a branch without a preceding rule name is treated as
  the implicit start rule.

Statements may be separated by newlines or whitespace.

Input Directives
~~~~~~~~~~~~~~~~

``#input`` declares a runtime-configurable program parameter:

::

    #input width                    # no default — must be provided at runtime
    #input height 17                # default value 17
    #input depth number 5           # explicit type keyword, default 5

Syntax: ``#input <name> [number] [default_value]``

The default value must be a plain number (int, float, or fraction like ``1/3``).
``#input`` and ``#define`` share the same namespace — a name cannot appear in both.

Define Directives
~~~~~~~~~~~~~~~~~

``#define`` declares a named constant available throughout the program:

::

    #define radius 5
    #define angle (360 / n)

Values may be plain numbers or parenthesized Python expressions. Expressions
support forward references — if variable ``a`` depends on ``b`` and ``b`` on
``c``, dependencies are resolved in topological order.

Set Statements
~~~~~~~~~~~~~~

``set`` configures global interpreter behavior:

+-------------------+-----------------------------------------------+
| Statement         | Description                                   |
+===================+===============================================+
| ``set maxdepth N``| Global recursion depth limit.                 |
+-------------------+-----------------------------------------------+
| ``set maxobjects N`` | Hard cap on total primitive instances.     |
+-------------------+-----------------------------------------------+
| ``set minsize F`` | Terminate branches smaller than diagonal *F*. |
+-------------------+-----------------------------------------------+
| ``set maxsize F`` | Terminate branches larger than diagonal *F*.  |
+-------------------+-----------------------------------------------+
| ``set seed N``    | Random seed for weighted rule selection.      |
+-------------------+-----------------------------------------------+
| ``set background C`` | Set background color (e.g. ``#FF0000``).   |
+-------------------+-----------------------------------------------+
| ``set color random`` | Choose random colors from colorpool.       |
+-------------------+-----------------------------------------------+

Rule Definitions
~~~~~~~~~~~~~~~~

A rule maps a name to one or more branches:

::

    rule r1 maxdepth 10 weight 2 {
        {x 1} r1
        {s 0.5} box
    }

Components:

+---------------+--------------------------------------------+
| Component     | Syntax                                     |
+===============+============================================+
| Name          | ``IDENTIFIER``                             |
+---------------+--------------------------------------------+
| Parameters    | ``(p1, p2, ...)``                          |
+---------------+--------------------------------------------+
| Maxdepth      | ``maxdepth N`` or ``md N``                 |
+---------------+--------------------------------------------+
| Retirement    | ``> successor`` (rule to substitute)       |
+---------------+--------------------------------------------+
| Weight        | ``weight W`` or ``w W``                    |
+---------------+--------------------------------------------+
| Body          | ``{ branch* }``                            |
+---------------+--------------------------------------------+

**Parameterized rules** allow dynamic behavior:

::

    rule branch(angle, length) {
        {rz angle s length 1 1} box
    }
    branch(30, 5)

**Implicit rules** (shorthand without ``rule`` keyword):

::

    my_rule(w, h)
    {s w h 1} box

is equivalent to: ``rule my_rule(w, h) { {s w h 1} box }``

Branches
~~~~~~~~

A branch is a sequence of repetitions and transformation blocks followed by
a terminal (rule reference or primitive):

::

    3 * {rz 120} 2 * {x 1} box
    {rz 90 s 0.8} r1
    box

Structure: ``(repetition | transform_block)* terminal``

* **Repetition** — ``N * { transforms }`` applies transforms *N* times,
  accumulating the matrix.
* **Transform block** — ``{ transforms }`` applies transforms once (count = 1).
* **Terminal** — a ``rule_ref`` or a ``primitive``.

Transformations within a branch are applied right-to-left (like function
composition). In repetitions, each iteration accumulates the transformation matrix.

Repetitions
~~~~~~~~~~~

``N * { transformations... }`` applies the transformations *N* times,
accumulating the matrix:

::

    5 * {x 1 rz 72} box

Produces 5 copies, each translated by 1 unit and rotated by 72° more than
the previous. The count can be:

* **Integer**: ``5 * {x 1} box``
* **Variable**: ``n * {x 1} box`` (resolved from ``#define``)
* **Expression**: ``(n * 2) * {x 1} box``

Transformations
---------------

Transformations modify the current transformation matrix. They are applied
inside ``{...}`` blocks.

Geometrical Transformations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------+-----------------------------------------------------------+
| Syntax | Effect                                                    |
+========+===========================================================+
| ``x v``| Translate along X by *v*                                  |
+--------+-----------------------------------------------------------+
| ``y v``| Translate along Y by *v*                                  |
+--------+-----------------------------------------------------------+
| ``z v``| Translate along Z by *v*                                  |
+--------+-----------------------------------------------------------+
| ``rx v``| Rotate about X axis by *v* degrees                        |
+--------+-----------------------------------------------------------+
| ``ry v``| Rotate about Y axis by *v* degrees                        |
+--------+-----------------------------------------------------------+
| ``rz v``| Rotate about Z axis by *v* degrees                        |
+--------+-----------------------------------------------------------+
| ``s v`` | Uniform scale by *v*                                      |
+--------+-----------------------------------------------------------+
| ``s v1 v2`` | Scale X by *v1*, Y by *v2*, Z by *v1*               |
+--------+-----------------------------------------------------------+
| ``s v1 v2 v3`` | Scale X, Y, Z by *v1*, *v2*, *v3*                  |
+--------+-----------------------------------------------------------+
| ``m f1 ... f9`` | Apply 3×3 matrix (row-major, 9 values)              |
+--------+-----------------------------------------------------------+
| ``fx`` | Mirror about X axis                                       |
+--------+-----------------------------------------------------------+
| ``fy`` | Mirror about Y axis                                       |
+--------+-----------------------------------------------------------+
| ``fz`` | Mirror about Z axis                                       |
+--------+-----------------------------------------------------------+

Rotation and scale centers: by default (legacy LSystem mode) transformations
are centered at ``(0, 0, 0)``. With **Origin center** unchecked, they are
centered at ``(0.5, 0.5, 0.5)`` — the center of the unit cube.

Color Transformations
~~~~~~~~~~~~~~~~~~~~~

Color transformations affect the color of emitted primitives but do not
affect geometry.

+-------------------+---------------------------------------------------------+
| Syntax            | Effect                                                  |
+===================+=========================================================+
| ``h v`` / ``hue v`` | Shift hue by *v* degrees (wraps 0–360)               |
+-------------------+---------------------------------------------------------+
| ``sat v``         | Multiply saturation by *v* (clamped to [0, 1])          |
+-------------------+---------------------------------------------------------+
| ``b v`` / ``brightness v`` | Multiply brightness by *v* (clamped to [0, 1]) |
+-------------------+---------------------------------------------------------+
| ``a v`` / ``alpha v`` | Multiply alpha by *v* (clamped to [0, 1])          |
+-------------------+---------------------------------------------------------+
| ``color C``       | Set absolute color to *C*                               |
+-------------------+---------------------------------------------------------+
| ``blend C s``     | Blend with color *C* at strength *s*                    |
+-------------------+---------------------------------------------------------+

Colors are specified as HTML hex strings (``#FF0000``), SVG keywords
(``red``, ``lightgoldenrodyellow``), or quoted strings (``'darkgreen'``).

**NB**: At the moment, color transformations are parsed, but are not processed
and do not affect output of the node. Colors support will be added in later
versions of the node.

Values
------

A **value** is one of:

+-------------+----------------------------------------------+
| Type        | Syntax                                       |
+=============+==============================================+
| Number      | ``3``, ``3.14``, ``1/3``, ``-1.5e2``         |
+-------------+----------------------------------------------+
| Variable    | ``a``, ``radius``, ``my_var``                |
+-------------+----------------------------------------------+
| Expression  | ``(a + b)``, ``(sin(theta))``                |
+-------------+----------------------------------------------+

**Keyword restriction**: identifiers that match transformation keywords
(``x``, ``y``, ``z``, ``rx``, ``ry``, ``rz``, ``s``, ``m``, ``fx``, ``fy``,
``fz``, ``h``, ``hue``, ``sat``, ``b``, ``brightness``, ``a``, ``alpha``,
``color``, ``blend``) are **not** accepted as variable references inside
``{...}`` blocks. To use a variable with such a name, wrap it in an expression:

::

    s (x) (y) 1    # Scale by variables x and y

Expressions
-----------

Parenthesized Python expressions provide computed values:

::

    {x (a + b * theta)} box
    #define scale (base * 0.9)
    (n * 2) * {rz (360 / n)} box

The expression is evaluated with ``eval()`` using a safe namespace containing:

* All functions from the ``math`` module: ``sin``, ``cos``, ``tan``, ``sqrt``,
  ``pow``, ``log``, ``exp``, ``floor``, ``ceil``, ``fabs``, ``asin``, ``acos``,
  ``atan``, ``atan2``, ``radians``, ``degrees``, ``hypot``, ``erf``, ``gamma``,
  and more.
* Constants: ``pi``, ``e``
* Built-ins: ``abs``, ``round``, ``min``, ``max``, ``pow``, ``tuple``, ``list``
* All ``#define`` variables

Rule References
---------------

A rule reference invokes another rule:

::

    r1                              # plain call
    r1(3, 5)                        # with arguments
    r1(a, (b + 1))                  # mixed arguments
    md 10 r1                        # with retirement depth
    md 10 > leaf r1                 # with retirement and successor

**Ambiguity**: if a rule has multiple definitions (same name), one is chosen
at random weighted by the ``weight`` modifier. All definitions must have the
same parameter count.

Primitives
----------

Primitives are the geometric shapes emitted by the interpreter:

+-------------+-----------------------------------------------------+
| Primitive   | Description                                         |
+=============+=====================================================+
| ``box``     | Solid cube centered at origin                       |
+-------------+-----------------------------------------------------+
| ``grid``    | Wireframe cube (edges only)                         |
+-------------+-----------------------------------------------------+
| ``sphere``  | Sphere centered at origin                           |
+-------------+-----------------------------------------------------+
| ``line``    | Line segment along X axis, centered in YZ plane     |
+-------------+-----------------------------------------------------+
| ``point``   | Single point at origin                              |
+-------------+-----------------------------------------------------+
| ``Triangle[v1;v2;v3]`` | Custom triangle with explicit vertices     |
+-------------+-----------------------------------------------------+

**Triangle syntax**: ``Triangle[0,0,0; 1,0,0; 0.5,1,0]``. Vertices are
``(x, y, z)`` triples separated by ``;``. Missing Y or Z defaults to ``0.0``.

Scoping Rules
-------------

Variable resolution follows this priority (highest to lowest):

1. **Rule parameters** — parameters of the current rule definition
2. **Input parameters** — ``#input`` directives (resolved at runtime)
3. **Define variables** — ``#define`` directives at program level

When a rule is called with arguments, the arguments are bound to the parameter
names, creating a local scope:

::

    #input val 100
    rule r(val) {
        {s val 1 1} box    # val = argument, not 100
    }
    r(5)                   # produces box scaled by 5

Nested rule calls create nested scopes. Inner parameters shadow outer
parameters with the same name.

Termination Criteria
--------------------

EisenScript provides several mechanisms to control the extent of generation:

* **``set maxdepth N``** — global recursion depth limit.
* **``set maxobjects N``** — hard cap on total primitive instances.
* **``set minsize F``** — terminate branches where the diagonal of the unit
  cube is smaller than *F*.
* **``set maxsize F``** — terminate branches where the diagonal exceeds *F*.
* **``md N``** — per-rule max recursion depth.
* **``md N > successor``** — when max depth is reached, call *successor* rule
  instead of terminating.

Inputs
------

The set of inputs for this node depends on ``#input`` directives declared in
the EisenScript program. Each ``#input`` parameter becomes one input socket.
If a parameter has a default value, the input is optional; otherwise it must be
connected.

Parameters
----------

This node has the following parameters:

- **Script**. Name of Blender text buffer containing the EisenScript program.
  Select from the list of available text blocks in the node header.
- **Seed**. Integer seed for weighted rule selection. Default is 0. Changing
  the seed produces different random choices when ambiguous rules are defined.
- **Max depth**. Global recursion depth limit. Overrides any ``set maxdepth``
  in the program. Default is 8.
- **Max objects**. Hard cap on total primitive instances (0 = unlimited).
  Default is 1000. This prevents runaway generation.
- **Origin center**. If checked, transformations use ``(0,0,0)`` as center
  (legacy LSystem behavior). If unchecked, use ``(0.5,0.5,0.5)`` per the
  EisenScript specification. Default is checked (True).

Outputs
-------

This node has the following outputs:

* **Box**. List of 4×4 placement matrices for all ``box`` primitives.
* **Grid**. List of 4×4 placement matrices for all ``grid`` primitives.
* **Sphere**. List of 4×4 placement matrices for all ``sphere`` primitives.
* **Line**. List of 4×4 placement matrices for all ``line`` primitives.
* **Point**. List of 4×4 placement matrices for all ``point`` primitives.
* **Triangle**. List of 4×4 placement matrices for all ``triangle`` primitives.

Each output is a list of ``mathutils.Matrix`` objects (4×4). These matrices
can be used with the **Matrix Transform** node to place objects, or with the
**Objects In** node to instance geometry at each location.

Examples
--------

Simple Tree
~~~~~~~~~~~

::

    set maxdepth 100
    rule trunk {
        {y 2} trunk
        {y 1 s 0.8} box
    }
    trunk

.. image:: https://github.com/user-attachments/assets/47d94243-a8d0-4706-8b24-6750c0d810f9
  :target: https://github.com/user-attachments/assets/47d94243-a8d0-4706-8b24-6750c0d810f9

Radial Pattern with Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    #define n 12
    #define angle_step (360 / n)
    n * {rz angle_step x 2} box

.. image:: https://github.com/user-attachments/assets/8fb9d07c-62f6-4925-832b-3f051cd21517
  :target: https://github.com/user-attachments/assets/8fb9d07c-62f6-4925-832b-3f051cd21517

Runtime-Configurable Tree
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    #input trunk_height 5
    #input branch_count 8
    #define angle_step (360 / branch_count)

    branch_count * {rz angle_step y trunk_height} box

.. image:: https://github.com/user-attachments/assets/fcf449c2-b054-4493-91d1-05e9335cec6a
  :target: https://github.com/user-attachments/assets/fcf449c2-b054-4493-91d1-05e9335cec6a

Parameterized Rule
~~~~~~~~~~~~~~~~~~

::

    rule bar(length) {
        {x (length/2 + 0.5) s length 1 1} box
    }

    rule root {
        branch(10)
    }

    rule leaf {
        {s 0.2 0.2 3} box
    }

    rule branch(length) maxdepth 10 > leaf {
        {rz 15} branch((length + 0.7))
        bar(length)
    }

    root

.. image:: https://github.com/user-attachments/assets/6c77ee1e-ac87-47ea-bb7a-1483c2d5d1a0
  :target: https://github.com/user-attachments/assets/6c77ee1e-ac87-47ea-bb7a-1483c2d5d1a0


Octopus (from original EisenScript spec)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    set maxdepth 100
    10 * {ry 36 sat 0.9} 30 * {ry 10} 1 * {h 30 b 0.8 sat 0.8 a 0.3} r1

    rule r1 w 20 {
        {s 0.9 rz 5 h 5 rx 5 x 1} r1
        {s 1 0.2 0.5} box
    }

    rule r1 w 20 {
        {s 0.99 rz -5 h 5 rx -5 x 1} r1
        {s 1 0.2 0.5} box
    }

    rule r1 {}

.. image:: https://github.com/user-attachments/assets/a28eb0d7-16c3-4748-aafa-9261de9b53ff
  :target: https://github.com/user-attachments/assets/a28eb0d7-16c3-4748-aafa-9261de9b53ff

Koch Snowflake
~~~~~~~~~~~~~~

::

    #input depth 4

    #define main_radius (sqrt(3)/2)
    #define scale_step (1.0/3.0)
    #define dx 0.25
    #define dy (0.1 + scale_step)

    {y main_radius} R1
    {rz 120 y main_radius} R1
    {rz 240 y main_radius} R1

    rule R1 md depth > unit {
        {x -1 s scale_step} R1
        {x (-dx) y dy rz 60 s scale_step} R1
        {x dx y dy rz -60 s scale_step} R1
        {x 1 s scale_step} R1
    }

    rule unit {
        {s 3} line
    }

.. image:: https://github.com/user-attachments/assets/fb2ef5b7-199c-473e-ba77-a15197cd4c96

Gotchas
-------

The update mechanism doesn't process inputs or anything until the following
conditions are satisfied:

* The **Script** field must point to an existing Blender Text block.
* All required ``#input`` parameters (those without defaults) must be
  connected.

Keyboard Shortcut to Refresh
----------------------------

Changes made to the EisenScript text file are not propagated automatically.
To refresh the node, change a value on one of the incoming nodes, or click
one of the input or output sockets.
