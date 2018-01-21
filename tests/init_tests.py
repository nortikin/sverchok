
import bpy

from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info

class InitTests(SverchokTestCase):

    def test_core_exists(self):
        bpy.ops.script.reload()
        import sverchok.core

