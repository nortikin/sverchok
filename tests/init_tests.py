
import addon_utils

from sverchok.utils.testing import *


@unittest.skip("Disabled temporarily")
class InitTests(SverchokTestCase):

    def test_core_exists(self):
        with self.assert_logs_no_errors():
            bpy.ops.script.reload()
            import sverchok.core

    def test_disable_enable(self):
        with self.assert_logs_no_errors():
            sv_logger.info("Disabling Sverchok")
            addon_utils.disable("sverchok")
            sv_logger.info("Enabling Sverchok")
            addon_utils.enable("sverchok")

