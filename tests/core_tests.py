
from pathlib import Path
import importlib

from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info, exception

class CoreTests(SverchokTestCase):
    
    def test_imports(self):
        """
        Test that all files can be imported.
        Theoretically, there can be cases when some sverchok modules
        are not imported at registration, but only by some event
        (for example, when the node is added into tree).
        This test is intended to check that there are no dangling / broken
        or cyclic imports in any module.
        """
        for subroot in ['core', 'utils', 'ui', 'nodes', 'old_nodes']:
            for path in Path(subroot).rglob('*.py'):
                with self.subTest(path = str(path)):
                    parts = list(path.parts)
                    parts[-1] = parts[-1][:-3] # remove .py suffix
                    module_name = "sverchok." + ".".join(parts)
                    try:
                        module = importlib.import_module(module_name)
                    except Exception as e:
                        exception(e)
                        self.fail(str(e))
                    self.assertIsNotNone(module)

