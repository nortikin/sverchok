FCurve In
=========

This node give you access to the FCurves bound to scene objects. 

Because this is an early version of the node, the UI is a bit rough. The Blender API is a little rough in this area too - don't expect huge future improvements. There doesn't appear to be a way to introspect the individual names of
the standard keyframed properties like Location's `X Location Y Location Z Location`. ID props and 
custom prop names however *can* be introspected, but i'm not adding it as a feature to the node.

The node operates in several modes, it automatically attempts to process the input in these two ways.

- default:  one value (take frame number, or if unconnected input uses `ctx.scene.current_frame`
- multi_sample: take a sequence (a range, or ranges) and generate the evaluated range (or ranges)

The node lets you generate a new Empty automatically, by typing in a name of a desired property 
and hitting Enter. Currently I'm assuming you want a float, it's the most useful out-of-the-box.

You can also pick the FCurve of an existing object, but selecting the curve is not super intuitive. 
Selection happens by property_index. Vector properties (like location) have an individual FCurve 
for each component. This may deserve a longer explanation but it's not an issue if you just use the
supplied auto-creation method (Typing a name into the property name box)

If you are picking an existing Object with multiple fcurves associated, you will want to know that 
the property index may change if you add new standard keyframe types (f.ex:  if you already have 6 
custom properties keyframed and you then decide to keyframe the location property, then the indices 
you picked for the other property index on the node will be invalidated. ( i think )


None of that made sense?
========================

OK, best you can do is look at the issue tracker examples associated with the first pullrequest for this node:

https://github.com/nortikin/sverchok/pull/2236
