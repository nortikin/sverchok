
class SvDependency():
    def __init__(self, package, url, module=None, message=None):
        self.package = package
        self.module = module
        self.message = message
        self.url = url
        self.pip_installable = False

sv_dependencies = dict()

freecad_d = sv_dependencies["freecad"] = SvDependency("FreeCAD", "https://www.freecadweb.org/")
try:
    import FreeCAD
    freecad_d.message = "FreeCAD package is available"
    freecad_d.module = FreeCAD
except ImportError:
    freecad_d.message = "FreeCAD package is not available, Solids nodes will not be available"
    print(freecad_d.message)
    FreeCAD = None
