
import bpy

import logging

from sverchok import bl_info

log_buffer_name = "sverchok.log"
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

internal_buffer_initialized = False
initialized = False

def get_log_buffer():
    try:
        if log_buffer_name in bpy.data.texts:
            return bpy.data.texts[log_buffer_name]
        else:
            return bpy.data.texts.new(name=log_buffer_name)
    except AttributeError as e:
        raise Exception("Can't initialize logging to internal buffer: get_log_buffer is called too early: {}".format(e))

def ensure_initialized():
    global internal_buffer_initialized
    global initialized

    if not internal_buffer_initialized:
        handler = logging.StreamHandler(get_log_buffer())
        handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(handler)
        internal_buffer_initialized = True

    if not initialized:
        logging.info("Initializing Sverchok logging. Blender version %s, Sverchok version %s", bpy.app.version_string, bl_info['version'])
        initialized = True


def getLogger(name=None):
    ensure_initialized()
    return logging.getLogger(name)

def register():
    logging.basicConfig(level=logging.DEBUG, format=log_format)

def unregister():
    logging.shutdown()

