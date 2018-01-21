
import bpy
import addon_utils

from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info

class InitTests(SverchokTestCase):

    def test_core_exists(self):
        bpy.ops.script.reload()
        import sverchok.core

    def test_disable_enable(self):
        info("Disabling Sverchok")
        addon_utils.disable("sverchok")
        info("Enabling Sverchok")
        addon_utils.enable("sverchok")

