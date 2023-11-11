# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
This module contains some general code to support external dependencies in
Sverchok, and declarations of specific dependencies.

In most cases, one imports required dependency modules from this module.
If the corresponding library is not installed, this will import None value
instead of actual module, so that one can execute another version of code:

    from sverchok.dependencies import scipy

    if scipy is None:
        print("SciPy is not available, will try to do without it")
    else:
        from scipy.optimize import minimize_scalar
        ...

todo: Create dependencies.txt file and import modules from there
"""
import logging

import sverchok.settings as settings


logger = logging.getLogger('sverchok')


class SvDependency():
    """
    Definition of external dependency package.
    """
    def __init__(self, package, url, module=None):
        """
        Args:
            package: name of package
            url: home URL of the package
            module: main package module object
        """
        self.package = package
        self.module = module
        self.url = url
        self.pip_installable = False

    @property
    def message(self):
        return f"{self.package} package is {'' if self.module else 'not '}available"


"""
Dictionary with Sverchok dependencies
"""
sv_dependencies = dict()

def get_icon(package):
    """
    Return name of icon to be displayed in preferences dialog, depending on
    whether the dependency is available or not.
    """
    if package is None:
        return 'CANCEL'
    else:
        return 'CHECKMARK'

def draw_message(box, package, dependencies=None):
    """
    Draw standard set of UI elements about dependency in preferences dialog:

    * message about whether the dependency is installed
    * visit package website
    * install or upgrade with PIP, if possible
    """
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
    pip_d.module = pip
except ImportError:
    print(pip_d.message)
    pip = None

if pip is None:
    try:
        import ensurepip
    except ImportError:
        ensurepip = None
        # print("Ensurepip module is not available, user will not be able to install PIP automatically")
else:
    ensurepip = None
    # print("PIP is already installed, no need to call ensurepip")

scipy_d = sv_dependencies["scipy"] = SvDependency("scipy", "https://www.scipy.org/")
scipy_d.pip_installable = True
try:
    import scipy
    scipy_d.module = scipy
except ImportError:
    scipy = None

geomdl_d = sv_dependencies["geomdl"] = SvDependency("geomdl", "https://github.com/orbingol/NURBS-Python/tree/master/geomdl")
geomdl_d.pip_installable = True
try:
    import geomdl
    geomdl_d.module = geomdl
except ImportError:
    geomdl = None

skimage_d = sv_dependencies["skimage"] = SvDependency("scikit-image", "https://scikit-image.org/")
skimage_d.pip_installable = True
try:
    import skimage
    skimage_d.module = skimage
except ImportError:
    skimage = None

mcubes_d = sv_dependencies["mcubes"] = SvDependency("mcubes", "https://github.com/pmneila/PyMCubes")
try:
    import mcubes
    mcubes_d.module = mcubes
except ImportError:
    mcubes = None

circlify_d = sv_dependencies["circlify"] = SvDependency("circlify", "https://github.com/elmotec/circlify")
circlify_d.pip_installable = True
try:
    import circlify
    circlify_d.module = circlify
except ImportError:
    circlify = None

freecad_d = sv_dependencies["freecad"] = SvDependency("FreeCAD", "https://www.freecadweb.org/")
try:
    import FreeCAD
    freecad_d.module = FreeCAD
except ImportError:
    FreeCAD = None

cython_d = sv_dependencies["cython"] = SvDependency("Cython", "https://cython.org/")
cython_d.pip_installable = True
try:
    import Cython
    cython_d.module = Cython
except ImportError:
    Cython = None

numba_d = sv_dependencies["numba"] = SvDependency("Numba", "https://numba.pydata.org/")
numba_d.pip_installable = True
try:
    import numba
    numba_d.module = numba
except ImportError:
    numba = None

pyOpenSubdiv_d = sv_dependencies["pyOpenSubdiv"] = SvDependency("pyOpenSubdiv","https://github.com/GeneralPancakeMSTR/pyOpenSubdivision")
pyOpenSubdiv_d.pip_installable = True
try:
    import pyOpenSubdiv
    pyOpenSubdiv_d.module = pyOpenSubdiv
except ImportError:
    pyOpenSubdiv = None 

numexpr_d = sv_dependencies["numexpr"] = SvDependency("numexpr","https://github.com/pydata/numexpr")
numexpr_d.pip_installable = True
try:
    import numexpr
    numexpr_d.module = numexpr
except ImportError:
    numexpr = None 

ezdxf_d = sv_dependencies["ezdxf"] = SvDependency("ezdxf","https://github.com/mozman/ezdxf")
ezdxf_d.pip_installable = True
try:
    import ezdxf
    ezdxf_d.module = ezdxf
except ImportError:
    ezdxf = None 

settings.pip = pip
settings.sv_dependencies = sv_dependencies
settings.ensurepip = ensurepip
settings.draw_message = draw_message
settings.get_icon = get_icon


def register():
    good_names = [d.package for d in sv_dependencies.values()
                  if d.module is not None and d.package is not None]
    if good_names:
        logger.info("Dependencies available: %s.", ", ".join(good_names))
    else:
        logger.info("No dependencies are available.")
