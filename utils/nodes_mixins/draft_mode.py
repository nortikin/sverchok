# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


class DraftMode:
    """Use class for nodes which should replace their properties upon draft mode changes"""

    # this should contain mapping from "standard"
    # mode property names to draft mode property names.
    # E.g., draft_properties_mapping = dict(count = 'count_draft').
    draft_properties_mapping = dict()

    def does_support_draft_mode(self):
        """
        Nodes that either store separate property values
        for draft mode, or perform another version of
        algorithm in draft mode, should return True here.
        """
        return False

    def on_draft_mode_changed(self, new_draft_mode):
        """
        This is triggered when Draft mode of the tree is toggled.
        Nodes should not usually override this, but may override
        sv_draft_mode_changed() instead.
        """
        if self.does_support_draft_mode():
            if new_draft_mode == True:
                with self.sv_throttle_tree_update():
                    if not self.was_in_draft_mode():
                        # Copy values from standard properties
                        # to draft mode ones, when the node enters the
                        # draft mode first time.
                        for prop_name, draft_prop_name in self.draft_properties_mapping.items():
                            setattr(self, draft_prop_name, getattr(self, prop_name))
                    self['_was_in_draft_mode'] = True
        self.sv_draft_mode_changed(new_draft_mode)

    def sv_draft_mode_changed(self, new_draft_mode):
        """
        This is triggered when Draft mode of the tree is toggled.
        Nodes may override this if they need to do something specific
        on this event.
        """
        pass

    def was_in_draft_mode(self):
        """
        Whether this instance of the node ever has been in Draft mode.
        Nodes should not usually override this.
        """
        return self.get('_was_in_draft_mode', False)