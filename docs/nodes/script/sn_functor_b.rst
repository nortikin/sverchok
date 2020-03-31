sn functor b
============

"ScriptNode Functor Version B" is an implementation of a script node, which is better described by the examples in the thread where this node was developed. This node is not used generally, because it is not entirely a completed project and i want to potentially radically change the way the node is syntactically controlled.

The rational behind this node is that the code that implements the node "behind the scenes" is relatively simple, has little error checking, and relatively easy to maintain and augment. The downside is that it, unlike SNLite nodes, has a more verbose initialization syntax. See the code below.

.. image:: https://user-images.githubusercontent.com/619340/48945189-b7bb4080-ef29-11e8-8d46-1d5f002a0a89.png

here's an example snippet::

    import sverchok
    from sverchok.utils.geom import arc_slice

    def functor_init(self, context):
        inew = self.inputs.new
        inew("StringsSocket", "outer radius").prop_name = "float_01"
        inew("StringsSocket", "inner radius").prop_name = "float_02"
        inew("StringsSocket", "angle").prop_name = "float_03"
        inew("StringsSocket", "phase").prop_name = "float_04"

        self.outputs.new("VerticesSocket", "verts")
        self.outputs.new("StringsSocket", "edges")
        self.outputs.new("StringsSocket", "faces")

    def draw_buttons(self, context, layout):
        pass

    def process(self):
        outer_radius = self.inputs['outer radius'].sv_get()[0][0]
        inner_radius = self.inputs['inner radius'].sv_get()[0][0]
        phase = self.inputs['phase'].sv_get()[0][0]
        angle = self.inputs['angle'].sv_get()[0][0]
            
        geom = arc_slice(outer_radius=outer_radius, inner_radius=inner_radius, phase=phase, angle=angle)
        
        for idx, data in enumerate(geom):
            self.outputs[idx].sv_set([data])

the **functor_init** function is where you add sockets and set attributes of those sockets, much like coding regular
sverchok nodes.

the **draw_buttons** is optional, and is called by the baseclass.

the **process** function is performed whenever the node is told to update, to understand when this happens you should
read up on how Sverchok implements the update mechanism. If you want to do stuff inside this function that would cause the nodetree to update then you will want to wrap that code in::

    with self.sv_throttle_tree_update():
        # the code you execute here will have no side effect of triggering another call up nodetree.process
        # this avoids infinite recursions.


https://github.com/nortikin/sverchok/issues/2312