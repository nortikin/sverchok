
import logging

# Logging setup
# we have to set up logging here separately, because dependencies.py is loaded before settings.py,
# so we can't use common settings.

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

info, debug, error = logger.info, logger.debug, logger.error

class SvDependency():
    def __init__(self, package, url, module=None, message=None):
        self.package = package
        self.module = module
        self.message = message
        self.url = url
        self.pip_installable = False

sv_dependencies = dict()

def get_icon(package):
    if package is None:
        return 'CANCEL'
    else:
        return 'CHECKMARK'

def draw_message(box, package, dependencies=None):
    if dependencies is None:
        dependencies = sv_dependencies

    dependency = dependencies[package]
    col = box.column(align=True)
    col.label(text=dependency.message, icon=get_icon(dependency.module))
    row = col.row(align=True)
    row.operator('wm.url_open', text="Visit package website").url = dependency.url
    if dependency.module is None and dependency.pip_installable and pip is not None:
        row.operator('node.sv_ex_pip_install', text="Install with PIP").package = dependency.package
    elif dependency.pip_installable and pip is not None:
        op = row.operator('node.sv_ex_pip_install', text="Upgrade with PIP").package = dependency.package
    return row

pip_d = sv_dependencies["pip"] = SvDependency("pip", "https://pypi.org/project/pip/")
try:
    import pip
    pip_d.message = "PIP is available"
    pip_d.module = pip
except ImportError:
    pip_d.message = "PIP is not installed"
    debug(pip_d.message)
    pip = None

if pip is None:
    try:
        import ensurepip
    except ImportError:
        ensurepip = None
        info("Ensurepip module is not available, user will not be able to install PIP automatically")
else:
    ensurepip = None
    debug("PIP is already installed, no need to call ensurepip")

scipy_d = sv_dependencies["scipy"] = SvDependency("scipy", "https://www.scipy.org/")
scipy_d.pip_installable = True
try:
    import scipy
    scipy_d.message = "SciPy is available"
    scipy_d.module = scipy
except ImportError:
    scipy_d.message = "SciPy package is not available. Voronoi nodes and RBF-based nodes will not be available."
    info(scipy_d.message)
    scipy = None

geomdl_d = sv_dependencies["geomdl"] = SvDependency("geomdl", "https://github.com/orbingol/NURBS-Python/tree/master/geomdl")
geomdl_d.pip_installable = True
try:
    import geomdl
    geomdl_d.message = "geomdl package is available"
    geomdl_d.module = geomdl
except ImportError:
    geomdl_d.message = "geomdl package is not available, some NURBS related nodes will not be available"
    info(geomdl_d.message)
    geomdl = None

skimage_d = sv_dependencies["skimage"] = SvDependency("scikit-image", "https://scikit-image.org/")
skimage_d.pip_installable = True
try:
    import skimage
    skimage_d.message = "SciKit-Image package is available"
    skimage_d.module = skimage
except ImportError:
    skimage_d.message = "SciKit-Image package is not available; SciKit-based implementation of Marching Cubes and Marching Squares will not be available"
    info(skimage_d.message)
    skimage = None

mcubes_d = sv_dependencies["mcubes"] = SvDependency("mcubes", "https://github.com/pmneila/PyMCubes")
try:
    import mcubes
    mcubes_d.message = "PyMCubes package is available"
    mcubes_d.module = mcubes
except ImportError:
    mcubes_d.message = "PyMCubes package is not available. PyMCubes-based implementation of Marching Cubes will not be available"
    info(mcubes_d.message)
    mcubes = None

circlify_d = sv_dependencies["circlify"] = SvDependency("circlify", "https://github.com/elmotec/circlify")
circlify_d.pip_installable = True
try:
    import circlify
    circlify_d.message = "Circlify package is available"
    circlify_d.module = circlify
except ImportError:
    circlify_d.message = "Circlify package is not available. Circlify node will not be available"
    info(circlify_d.message)
    circlify = None

ladydug_d = sv_dependencies["lbt-ladybug"] = SvDependency("lbt-ladybug", "https://github.com/ladybug-tools/ladybug")
try:
    import ladybug
    ladydug_d.message = "Ladybug package is available"
    ladydug_d.module = ladybug
except ImportError:
    ladydug_d.message = "Ladybug package is not available. Ladybug module will not be available"
    ladydug_d.pip_installable = True
    info(ladydug_d.message)
    ladybug = None

freecad_d = sv_dependencies["freecad"] = SvDependency("FreeCAD", "https://www.freecadweb.org/")
try:
    import FreeCAD
    freecad_d.message = "FreeCAD package is available"
    freecad_d.module = FreeCAD
except ImportError:
    freecad_d.message = "FreeCAD package is not available, Solids nodes will not be available"
    info(freecad_d.message)
    FreeCAD = None

cython_d = sv_dependencies["cython"] = SvDependency("Cython", "https://www.freecadweb.org/")
cython_d.pip_installable = True
try:
    import Cython
    cython_d.message = "Cython package is available"
    cython_d.module = Cython
except ImportError:
    cython_d.message = "Cython package is not available, Enhanched KDTree search will not be available"
    info(cython_d.message)
    Cython = None

good_names = [d.package for d in sv_dependencies.values() if d.module is not None and d.package is not None]
if good_names:
    info("Dependencies available: %s.", ", ".join(good_names))
else:
    info("No dependencies are available.")
