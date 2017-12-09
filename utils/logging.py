
import bpy

import inspect
import logging
import logging.handlers

from sverchok.ui.development import get_version_string
from sverchok.utils.context_managers import sv_preferences

# Hardcoded for now
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Whether logging to internal blender's text buffer is initialized
internal_buffer_initialized = False
# Whether logging to external text file is initialized
file_initialized = False
# Whether logging is initialized
initialized = False

def get_log_buffer(log_buffer_name):
    """
    Get internal blender text buffer for logging.
    """
    try:
        if log_buffer_name in bpy.data.texts:
            return bpy.data.texts[log_buffer_name]
        else:
            return bpy.data.texts.new(name=log_buffer_name)
    except AttributeError as e:
        #logging.debug("Can't initialize logging to internal buffer: get_log_buffer is called too early: {}".format(e))
        return None

def try_initialize():
    """
    Try to initialize logging subsystem.
    Does nothing if everything is already initialized.
    Prints an error if it is called too early.
    """
    global internal_buffer_initialized
    global file_initialized
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

                    for area in bpy.context.screen.areas:
                        if area.type == 'TEXT_EDITOR':
                            if area.spaces[0].text is None:
                                area.spaces[0].text = buffer
                                break
                    internal_buffer_initialized = True
            else:
                internal_buffer_initialized = True

        if not file_initialized:
            if prefs.log_to_file:
                handler = logging.handlers.RotatingFileHandler(prefs.log_file_name, 
                            maxBytes = 10*1024*1024,
                            backupCount = 3)
                handler.setFormatter(logging.Formatter(log_format))
                logging.getLogger().addHandler(handler)

            file_initialized = True

        if internal_buffer_initialized and file_initialized and not initialized:
            setLevel(prefs.log_level)

            logging.info("Initializing Sverchok logging. Blender version %s, Sverchok version %s", bpy.app.version_string, get_version_string())
            logging.debug("Current log level: %s, log to text buffer: %s, log to file: %s",
                    prefs.log_level,
                    ("no" if not prefs.log_to_buffer else prefs.log_buffer_name),
                    ("no" if not prefs.log_to_file else prefs.log_file_name) )
            initialized = True

# Convinience functions

def with_module_logger(method_name):
    """
    Returns a method of Logger class instance.
    Logger name is obtained from caller module name.
    """
    def wrapper(*args, **kwargs):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__
        try_initialize()
        logger = logging.getLogger(name)
        method = getattr(logger, method_name)
        return method(*args, **kwargs)

    wrapper.__name__ = method_name
    wrapper.__doc__ = "Call `{}' method on a Logger. Logger name is obtained from caller module name.".format(method_name)

    return wrapper

debug = with_module_logger("debug")
info = with_module_logger("info")
warning = with_module_logger("warning")
error = with_module_logger("error")
exception = with_module_logger("exception")

def getLogger(name=None):
    """
    Get Logger instance.
    If name is None, then logger name is obtained from caller module name.
    """
    if name is None:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__
    try_initialize()
    return logging.getLogger(name)

def setLevel(level):
    """
    Set logging level for all handlers.
    """
    if type(level) != int:
        level = getattr(logging, level)

    logging.getLogger().setLevel(level)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)

def register():
    with sv_preferences() as prefs:
        level = getattr(logging, prefs.log_level)
        logging.basicConfig(level=level, format=log_format)
    logging.captureWarnings(True)
    info("Registering Sverchok addon. Messages issued during registration will be only available in the console and in file (if configured).")

def unregister():
    logging.shutdown()

