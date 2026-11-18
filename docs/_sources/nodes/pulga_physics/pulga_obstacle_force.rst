Pulga Obstacle Force
====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d60e18cd-99b0-458c-a06c-9aa3c0580864
  :target: https://github.com/nortikin/sverchok/assets/14288520/d60e18cd-99b0-458c-a06c-9aa3c0580864

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/359e71c7-205f-4a71-9a8b-51288765fb38
  :target: https://github.com/nortikin/sverchok/assets/14288520/359e71c7-205f-4a71-9a8b-51288765fb38

This node creates a force to be applied with the Pulga Physics Solver node.

Obstacles (meshes) that will collide with the system particles (vertices)


Input
-----

- **Vertices**: Vertices of the obstacles.
- **Polygons**: Polygons of the obstacles.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/58982fee-8fc5-4d1c-9f59-d74a0ce804ce
      :target: https://github.com/nortikin/sverchok/assets/14288520/58982fee-8fc5-4d1c-9f59-d74a0ce804ce
    
    * Generator-> :doc:`Box </nodes/generator/box_mk2>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

- **Absorption**: Amount of energy that will be absorbed by the obstacle (reducing speed and acceleration). 0 means no absorption and 1 full absorption

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6e1dad7e-d2e5-480e-b452-2f279835ee7a
      :target: https://github.com/nortikin/sverchok/assets/14288520/6e1dad7e-d2e5-480e-b452-2f279835ee7a

    * Number-> :doc:`Number Range </nodes/number/number_range>`
    * Vector-> :doc:`Vector In </nodes/vector/vector_in>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

Examples
--------

Grid of vertices colliding with a soft Cylindrical mesh:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e1c0bcac-5b33-40c7-bea6-9c25c1b5b647
  :target: https://github.com/nortikin/sverchok/assets/14288520/e1c0bcac-5b33-40c7-bea6-9c25c1b5b647

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

--------

Grid of vertices colliding with a soft spherical mesh:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_obstacle_force/blender_sverchok_pulga_obstacle_force_example_01.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_obstacle_force/blender_sverchok_pulga_obstacle_force_example_01.png


* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`


--------

Trajectories of vertices colliding with a hard spherical mesh.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/da62baed-63c5-4a67-98b3-41f57f54f8f0
  :target: https://github.com/nortikin/sverchok/assets/14288520/da62baed-63c5-4a67-98b3-41f57f54f8f0

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e4e95fa6-9b2d-4c6e-8ccc-0e8754cfbac4
  :target: https://github.com/nortikin/sverchok/assets/14288520/e4e95fa6-9b2d-4c6e-8ccc-0e8754cfbac4

Obstacle geometry domains
-------------------------

The **Domain** selector provides **Vertices**, **Edges**, and **Polygons**.
The default **Polygons** mode keeps the existing BVH-based response intact,
including the original ``Vertices``, ``Pols`` and ``Absorption`` inputs.

* **Vertices**: stationary point obstacles, using the supplied vertex positions.
  **Auto** uses a cached SciPy ``cKDTree`` when available; **NumPy** and
  **Numba** use their explicitly selected closest-point kernels.
* **Edges**: stationary line segments defined by ``Vertices`` and ``Edges``
  index pairs. Each particle is corrected toward the closest point on the
  nearest segment. Auto uses a Numba kernel when available.
* **Polygons**: the existing polygonal BVH obstacles, unchanged.

**Thickness**, visible for point and edge obstacles, adds to the solver's
particle radius; unlike the source polygon response, point/edge obstacles do
not require a surface normal. ``Absorption`` retains its existing meaning.
When a new point/edge contact is approached, velocity is reflected and damped;
forces are likewise reflected when directed into the obstacle.

External obstacle geometry remains fixed throughout solver iterations. These
modes use discrete closest-point tests, not continuous collision detection.

See also :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
and :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`.

Parametric obstacle domains
---------------------------

The **Domain** selector adds **Curve**, **Surface** and **Solid** to the
existing **Vertices**, **Edges** and **Polygons** obstacle modes. These are
**stationary external obstacles**, not deformable self-collision geometry.
The original **Polygons** mode and its absorption response are unchanged.

For parametric obstacles, the **Method** selector offers:

* **Fast**: Precompute a discretized obstacle once for the simulation. Curves
  become polyline segments, surfaces become a triangular UV grid, and FreeCAD
  solids become a tessellated surface. The nearest-point calculations are
  exact for that *discretized representation*, not for the original shape.
* **Precise**: Query nearest points directly on the parametric curve or
  surface using Sverchok's numerical closest-point solvers (SciPy required),
  or on a FreeCAD solid using its geometric ``distToShape`` operation. These
  are more expensive and numerical solvers do not guarantee the global
  mathematical minimum for all geometries.

**Curve** inputs:

* **Curve**: ``SvCurve`` geometry. Collisions act like a tube around it,
  with radius equal to particle radius plus **Thickness**.
* **Resolution**: number of sampled points in Fast mode, including endpoints.
* **Initial Samples**: initial samples for the Precise optimization.

**Surface** inputs:

* **Surface**: ``SvSurface`` geometry, with two-sided contact.
* **Resolution U**, **Resolution V**: numbers of sample points in the two
  parameter directions in Fast mode. Each grid cell becomes two triangles.
* **Initial Samples U**, **Initial Samples V**: independent initial
  sampling counts for Surface Precise.

**Solid** inputs (FreeCAD required):

* **Solid**: a FreeCAD ``Part.Shape``. The boundary is the collision surface.
* **Deflection**: absolute tessellation deflection in Fast mode. Smaller
  values yield a finer (slower and larger) collision mesh.
* **Fast** classifies a particle as inside/outside using the nearest BVH
  triangle normal, as in **Mesh (Volume)**. It requires a closed, outward-
  oriented tessellation and does not call ``FreeCAD.isInside`` each step.
* **Precise** uses FreeCAD's ``distToShape`` and ``isInside`` on the
  original B-Rep. Both methods project contacts toward the boundary.

**Absorption** retains its role as a multiplier on the reflected velocity and
force. **Thickness** adds to the radius of each simulated particle. The Fast
representations are cached in the force object, which is reconstructed when
Sverchok rebuilds the simulation; they are not recomputed per Pulga step.

Limitations
^^^^^^^^^^^

The simulation uses discrete positional correction, not continuous collision
sweeps, so fast-moving particles may tunnel through thin obstacles. Fast UV
sampling currently covers the rectangular parametric domain and does not
explicitly process trim boundaries. Precise surface queries use numerical
minimization and may require more initial samples on complex surfaces.
Fast Solid classification assumes a closed, outward-oriented mesh; Precise
uses the FreeCAD solid for inside/outside checks.

Precise surface initial sampling
--------------------------------

In **Surface** / **Precise** mode, **Initial Samples U / Initial Samples V**
control the number of samples along each parameter direction used to generate
an initial guess for the numerical nearest-point optimization. These settings
are independent of **Resolution U / Resolution V**, which apply only to
**Fast** tessellation. For example, U=30 and V=8 builds 240 initial samples.
Higher initial sampling can improve convergence but increases preparation cost
for every nearest-point search. Curve / Precise retains its single
**Initial Samples** value.
