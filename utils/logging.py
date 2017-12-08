
import bpy

import inspect
import logging
import logging.handlers

from sverchok import bl_info
from sverchok.utils.context_managers import sv_preferences

log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

internal_buffer_initialized = False
initialized = False

def get_log_buffer(log_buffer_name):
    try:
        if log_buffer_name in bpy.data.texts:
            return bpy.data.texts[log_buffer_name]
        else:
            return bpy.data.texts.new(name=log_buffer_name)
    except AttributeError as e:
        logging.debug("Can't initialize logging to internal buffer: get_log_buffer is called too early: {}".format(e))
        return None

def ensure_initialized():
    global internal_buffer_initialized
    global initialized

    with sv_preferences() as prefs:
        if not prefs:
            logging.error("Can't obtain logging preferences, it's too early")
            return

        if not internal_buffer_initialized:
            if prefs.log_to_buffer:
                buffer = get_log_buffer(prefs.log_buffer_name)
                if buffer is not None:
                    if prefs.log_to_buffer_clean:
                        buffer.clear()
                        logging.debug("Internal text buffer cleared")
                    handler = logging.StreamHandler(buffer)
                    handler.setFormatter(logging.Formatter(log_format))
                    logging.getLogger().addHandler(handler)
                    internal_buffer_initialized = True
            else:
                internal_buffer_initialized = True

        if not initialized:
            if prefs.log_to_file:
                handler = logging.handlers.RotatingFileHandler(prefs.log_file_name, 
                            maxBytes = 10*1024*1024,
                            backupCount = 3)
                handler.setFormatter(logging.Formatter(log_format))
                logging.getLogger().addHandler(handler)

            setLevel(prefs.log_level)

            logging.info("Initializing Sverchok logging. Blender version %s, Sverchok version %s", bpy.app.version_string, bl_info['version'])
            logging.debug("Current log level: %s, log to text buffer: %s, log to file: %s",
                    prefs.log_level,
                    ("no" if not prefs.log_to_buffer else prefs.log_buffer_name),
                    ("no" if not prefs.log_to_file else prefs.log_file_name) )
            initialized = True

# Convinience functions

def with_module_logger(method_name):
    def wrapper(*args, **kwargs):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__
        ensure_initialized()
        logger = logging.getLogger(name)
        method = getattr(logger, method_name)
        return method(*args, **kwargs)

    wrapper.__name__ = method_name

    return wrapper

debug = with_module_logger("debug")
info = with_module_logger("info")
warning = with_module_logger("warning")
error = with_module_logger("error")
exception = with_module_logger("exception")

def getLogger(name=None):
    if name is None:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__
    ensure_initialized()
    return logging.getLogger(name)

def setLevel(level):
    if type(level) != int:
        level = getattr(logging, level)

    for handler in logging.getLogger().handlers:
        handler.setLevel(level)

def register():
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    logging.captureWarnings(True)

def unregister():
    logging.shutdown()

