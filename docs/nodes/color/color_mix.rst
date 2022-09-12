Color Mix
=========

.. image:: https://user-images.githubusercontent.com/14288520/189637346-17f6026c-f23a-45bd-881b-f9fbb1186a7c.png
  :target: https://user-images.githubusercontent.com/14288520/189637346-17f6026c-f23a-45bd-881b-f9fbb1186a7c.png

Functionality
-------------

This node allows you mix colors using many standard methods.

Inputs
------

**Fac**: Amount of mixture to be applied.

**Color A**: Base color.

**Color B**: Top color.


Parameters
----------

This node has the following parameters:

* **Function**. Offers Mix, Darken, Multiply, Burn, Lighten, Screen, Dodge, Add, Overlay, Soft Light, Vivid Light, Pin Light, Hard Mix, Subtract, Difference, Divide, Reflect, Hue, Saturation, Value.

* **Clamp**. Clamp result of the node to 0..1 range.

Outputs
-------

This node has only one output: **Color**. It is RGB or RGBA vector, depending on the inputted colors.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189637424-1c11fb70-8a77-4beb-9246-d3a56ed1f444.png
  :target: https://user-images.githubusercontent.com/14288520/189637424-1c11fb70-8a77-4beb-9246-d3a56ed1f444.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

.. image:: https://user-images.githubusercontent.com/14288520/189637924-d205352a-dc24-4ff2-a6e6-3eaa5825cd27.png
  :target: https://user-images.githubusercontent.com/14288520/189637924-d205352a-dc24-4ff2-a6e6-3eaa5825cd27.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

.. image:: https://user-images.githubusercontent.com/14288520/189637489-60c76248-466d-4d13-bf9d-e971cc22e271.png
  :target: https://user-images.githubusercontent.com/14288520/189637489-60c76248-466d-4d13-bf9d-e971cc22e271.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`