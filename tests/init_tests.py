
import bpy
import addon_utils

from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info

class InitTests(SverchokTestCase):

    def test_core_exists(self):
        bpy.ops.script.reload()
        import sverchok.core

    def test_disable_enable(self):
        addon_utils.disable("sverchok")
        addon_utils.enable("sverchok")

