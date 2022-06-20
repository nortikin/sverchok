from multiprocessing import Pool

import sverchok.core.update_system as us
import sverchok.core.events as ev


def control_center(event):
    """
    1. Update tree model lazily
    2. Check whether the event should be processed
    3. Process event or create task to process via timer"""
    print("CONCUURENT")
    was_executed = True

    # frame update
    # This event can't be handled via NodesUpdater during animation rendering
    # because new frame change event can arrive before timer finishes its tusk.
    # Or timer can start working before frame change is handled.
    if type(event) is ev.AnimationEvent:
        if event.tree.sv_animate:
            ConcurrentUpdateTree.get(event.tree).is_animation_updated = False
            ConcurrentUpdateTree.test_update(event.tree)  # todo to replace

    # something changed in the scene
    elif type(event) is ev.SceneEvent:
        if event.tree.sv_scene_update and event.tree.sv_process:
            ConcurrentUpdateTree.get(event.tree).is_scene_updated = False
            ConcurrentUpdateTree.test_update(event.tree)  # todo to replace

    # nodes changed properties
    elif type(event) is ev.PropertyEvent:
        tree = ConcurrentUpdateTree.get(event.tree)
        tree.add_outdated(event.updated_nodes)
        if event.tree.sv_process:
            ConcurrentUpdateTree.test_update(event.tree)  # todo to replace

    # update the whole tree anyway
    elif type(event) is ev.ForceEvent:
        ConcurrentUpdateTree.reset_tree(event.tree)
        ConcurrentUpdateTree.test_update(event.tree)  # todo to replace

    # mark that the tree topology has changed
    # also this can be called (by Blender) during undo event in this case all
    # nodes will have another hash id and the comparison method will decide that
    # all nodes are new, and won't be able to detect changes, and will update all
    elif type(event) is ev.TreeEvent:
        ConcurrentUpdateTree.get(event.tree).is_updated = False
        if event.tree.sv_process:
            ConcurrentUpdateTree.test_update(event.tree)  # todo to replace

    # new file opened
    elif type(event) is ev.FileEvent:
        ConcurrentUpdateTree.reset_tree()

    else:
        was_executed = False
    return was_executed


class ConcurrentUpdateTree(us.UpdateTree):
    @classmethod
    def test_update(cls, tree):
        up_tree = cls.get(tree, refresh_tree=True)
        walker = up_tree._walk()
        # walker = up_tree._debug_color(walker)
        for node, prev_socks in walker:
            us.prepare_input_data(prev_socks, node.inputs)
        with Pool() as p:
            p.map(up_tree._concurrent_update_node, [getattr(n, 'process') for n, _ in walker])

        if up_tree._tree.show_time_mode == "Cumulative":
            times = up_tree._calc_cam_update_time()
        else:
            times = None
        us.update_ui(tree, times)

    def _walk(self):
        return [(n, self.previous_sockets(n)) for n in self._tree.nodes]

    def _concurrent_update_node(self, method):
        # todo grab stats
        method()
