# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


class ModifierNode:
    @property
    def sv_internal_links(self):
        mapping = [
            (self.inputs[0], self.outputs[0]),
            (self.inputs[1], self.outputs[1]),
            (self.inputs[2], self.outputs[2]),
        ]
        if 'FaceData' in self.outputs:
            mapping.append((self.inputs['FaceData'], self.outputs['FaceData']))
        return mapping


class ModifierLiteNode:
    @property
    def sv_internal_links(self):
        return [
            (self.inputs[0], self.outputs[0]),
            (self.inputs[1], self.outputs[1]),
        ]


class TransformNode:
    @property
    def sv_internal_links(self):
        return [(self.inputs[0], self.outputs[0])]


class EdgeGeneratorNode:
    @property
    def sv_internal_links(self):
        return [
            (self.inputs[0], self.outputs[0]),
            (self.inputs[1], self.outputs[1]),
        ]


class EdgeGeneratorLiteNode:
    @property
    def sv_internal_links(self):
        return [
            (self.inputs[0], self.outputs[0]),
        ]
