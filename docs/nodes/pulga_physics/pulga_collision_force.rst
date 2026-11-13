Pulga Collision Force
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/211c68f3-e0b1-4de8-93f5-45bf09367729
  :target: https://github.com/nortikin/sverchok/assets/14288520/211c68f3-e0b1-4de8-93f5-45bf09367729

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force will be applied when de particles (vertices) are nearer than the sum of particle radius.

The force direction will be the difference of the verts location

The force magnitude will be:  (Distance - Radius Sum) * Force Strength

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0d6e942b-c487-4746-aac2-632f389fcaaf
  :target: https://github.com/nortikin/sverchok/assets/14288520/0d6e942b-c487-4746-aac2-632f389fcaaf

Input
-----

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

Options
-------

**Mode**: Algorithm used to calculate collisions. Offers '**Brute Force**' and '**Kd-tree**'

- **Kd-tree**: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6
      :target: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6

- **Brute-Force**: This mode is much slower but does not need any dependencies to work.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/07394e3c-c5bc-4280-98ab-9c0e5349b839
  :target: https://github.com/nortikin/sverchok/assets/14288520/07394e3c-c5bc-4280-98ab-9c0e5349b839

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e9d04904-58a5-4e8f-b8c1-61fd51c545a5
  :target: https://github.com/nortikin/sverchok/assets/14288520/e9d04904-58a5-4e8f-b8c1-61fd51c545a5

Collision geometry domains
--------------------------

The **Domain** selector appears on the node. The default **Vertices** mode is
unchanged and preserves existing ``Strength`` and ``Brute Force / Kd-tree``
settings. **Edges** and **Polygons** use the current particle positions as the
deforming geometry and require connectivity indices into the Pulga solver's
initial particle list.

* **Edges**: each particle interacts with all non-incident segments. Its
  reaction force is shared between segment endpoints according to the
  closest-point factor. Connected edges never repel their own vertices.
* **Polygons**: contacts are **two-sided**. Triangles use barycentric reaction
  weights. Convex quads use a bilinear surface and four weights (the center
  distributes the reaction equally to all four corners). Planar n-gons with
  five or more vertices use **mean value coordinates** to distribute the
  reaction over the complete polygon rather than only one of its triangles.
  Triangulation is retained to locate contacts, with at most **one contact per
  original face and query particle**, avoiding duplicated forces on diagonals.
  Moderately warped n-gons use a reconstructed mean-value surface, keeping
  all their vertices active across deformation. Invalid projected polygons
  still fall back to triangle weights.
  The vertices of the original face are excluded from self-collision with it.
  The bilinear quad surface may differ from the triangulated mesh for warped
  quads; use well-formed, non-self-intersecting quads.

Additional inputs for both modes:

* **Thickness**: extra radius added to each query particle's solver radius.
* **Damping**: damping of the relative incoming normal velocity at contact.

``Strength``, ``Thickness`` and ``Damping`` can vary per particle (repeat-last
matching). A particle can contact multiple edges/faces in the same iteration.

**Engine**, on the N-panel, offers Auto / NumPy / Numba. Auto selects Numba when
available; the serial reference is used otherwise. Discrete collision detection
cannot prevent tunnelling with excessively large time steps.

See also :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
and :doc:`Pulga Obstacles Force </nodes/pulga_physics/pulga_obstacle_force>`.

Quad collision behavior
-----------------------

A quad is treated as one bilinear patch, ``Q(u,v)``. The closest-point query
finds ``u`` and ``v`` on the patch (with multiple numerical initial guesses);
contact reaction is then distributed with weights ``(1-u)(1-v)``,
``u(1-v)``, ``uv``, ``(1-u)v``. For a symmetric central impact, each of the
four vertices receives one quarter of the opposite force, rather than only
the endpoints of an artificial triangulation diagonal.

The weights sum to one, preserving overall force and, with the bilinear
contact position, torque of the normal contact. **This does not make a quad
rigid**: add spring/angle constraints for structural stiffness. Geometry is
discrete, not continuous collision detection. On highly folded/nonconvex
quads, the numerical closest-point solver is not guaranteed to find the
global minimum.

N-gon collision behavior
------------------------

For simple convex n-gons (five or more vertices), the triangulation locates
an initial contact. Mean value coordinates in a stable 2D projection are then
used to lift the point onto a continuous interpolated 3D polygon patch, and
the reaction is distributed to **all** vertices with the same weights. For a normal impact at the
center of a regular pentagon or hexagon, each corner receives respectively
one fifth or one sixth of the reaction. The coordinates vary continuously
inside the polygon, including across its triangulation diagonals.

Mean value coordinates reproduce the projected contact as a weighted sum
of the projected corners, including for warped faces. The contact point in
3D is consistently reconstructed with those weights. Consequently, the
reaction sums to the opposite particle force and reproduces the contact
torque within numerical tolerance. The
implementation also handles impacts exactly on a polygon edge by distributing
the reaction to the edge's two endpoints.

**Limitations:** N-gons are modeled by a mean-value-coordinate patch over a
projected polygon, so highly warped faces may differ significantly from the
triangulated mesh used for initial contact search. Degenerate, folded,
self-intersecting or non-convex projections may still fall back to a triangle;
exact boundary contacts intentionally weight only the edge's endpoints.
This is not an exact closest-point solver for arbitrary warped polygons.
The collision response is elastic force, not a rigid-body constraint.

Additional examples: deformable self-collision
----------------------------------------------

Polygon self-collision: particles and a deformable shell
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/6641eb88-ab2f-45d3-b0ab-f59b9a3f851c
   :target: https://github.com/user-attachments/assets/6641eb88-ab2f-45d3-b0ab-f59b9a3f851c

The shell starts from an IcoSphere converted to polygonal faces using
**Dual Mesh** and **Polygon Boom**, with the resulting geometry combined in
**Mesh Join**. A separate group of particles starts with randomized initial
velocities. Both the shell vertices and the moving particles are passed to
**Pulga Physics Solver** as one particle system.

**Pulga Collision Force** is set to **Polygons**, using the shell's polygon
indices. Incoming particles interact with the deformable faces from either
side, and the contact reaction is distributed among the vertices of each
face. For quads, bilinear weights are used; for supported n-gons,
mean value coordinates spread the reaction over the original polygon rather
than only an internal triangle. **Pulga Springs Force** supplies structural
stiffness through the shell's edges, so the polygons can deform while
responding to impacts.

Edge self-collision: moving particles and flexible segments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/9b5d5f1a-cda0-4b41-88fa-c5842b210af0
   :target: https://github.com/user-attachments/assets/9b5d5f1a-cda0-4b41-88fa-c5842b210af0

The **Segment** node provides the vertices and edges of the deformable
segments. Another set of particles is initialized with its own positions
and velocity. Their data is combined before entering **Pulga Physics Solver**.
The same segment connectivity is supplied to **Pulga Springs Force** and to
**Pulga Collision Force** in **Edges** mode.

As moving particles approach a segment, the collision force pushes them away
and distributes the opposite reaction to the segment's two endpoints according
to the closest-point factor. A vertex does not collide with edges that contain
that same vertex. The springs hold the connected structure together while it
bends and moves in response to contact.
