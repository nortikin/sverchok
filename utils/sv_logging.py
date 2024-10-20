from pathlib import Path
from typing import Type, Dict, Optional

import bpy

import inspect
import traceback
import logging
import logging.handlers
from contextlib import contextmanager

import sverchok

if not sverchok.reload_event:  # otherwise it leeds to infinite recursion
    old_factory = logging.getLogRecordFactory()


def add_relative_path_factory(name, *args, **kwargs):
    record = old_factory(name, *args, **kwargs)
    if name.startswith('sverchok'):
        path = Path(record.pathname)

        # search root path of the add-on
        for root in path.parents:
            if root.parent.name == 'addons':  # add-ons are not always in the folder
                break
        else:
            root = None

        if root is not None:
            record.relative_path = path.relative_to(root)
        else:  # it can if there is several instances of sverchok (as add-on and a separate folder)
            record.relative_path = path
    return record


if not sverchok.reload_event:  # otherwise it leeds to infinite recursion
    logging.setLogRecordFactory(add_relative_path_factory)

log_format = "%(asctime)s.%(msecs)03d [%(levelname)-5s] %(name)s %(relative_path)s:%(lineno)d - %(message)s"
sv_logger = logging.getLogger('sverchok')  # root logger

# set any level whatever you desire,
# it will be overridden by the add-on settings after the last one will be registered
if not sverchok.reload_event:
    sv_logger.setLevel(logging.ERROR)


class ColorFormatter(logging.Formatter):
    START_COLOR = '\033[{}m'
    RESET_COLOR = '\033[0m'
    COLORS = {
        'DEBUG': '1;30',  # grey
        'INFO': 32,  # green
        'WARNING': 33,  # yellow
        'ERROR': 31,  # red
        'CRITICAL': 41,  # white on red bg
    }

    def format(self, record):
        color = self.START_COLOR.format(self.COLORS[record.levelname])
        color_format = color + self._fmt + self.RESET_COLOR
        formatter = logging.Formatter(color_format, datefmt=self.datefmt)
        return formatter.format(record)


console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorFormatter(log_format, datefmt='%H:%M:%S'))
sv_logger.addHandler(console_handler)


def add_node_error_location(record: logging.LogRecord):
    # https://docs.python.org/3/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
    # should be called with logger.error(msg, exc_info=True)
    frame_info = inspect.getinnerframes(record.exc_info[-1])[-1]
    record.relative_path = Path(frame_info.filename).name
    record.lineno = frame_info.lineno
    if not is_enabled_for('DEBUG'):  # show traceback only in DEBUG mode
        record.exc_info = None
    return True


node_error_logger = logging.getLogger('sverchok.node_error')
node_error_logger.addFilter(add_node_error_location)


def add_file_handler(file_path):
    sv_logger.debug(f'Logging to file="{file_path}"')
    handler = logging.handlers.RotatingFileHandler(file_path,
                                                   maxBytes=10 * 1024 * 1024,
                                                   backupCount=3)
    handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
    sv_logger.addHandler(handler)


def remove_console_handler():
    # Remove console output handler.
    logging.debug("Log output to console is disabled. Further messages will"
                  " be available only in text buffer and file (if configured).")
    sv_logger.removeHandler(console_handler)
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    sv_logger.addHandler(logging.NullHandler())


@contextmanager
def catch_log_error():
    """Catch logging errors"""
    try:
        yield
    except Exception as e:
        frame, _, line, *_ = inspect.trace()[-1]
        module = inspect.getmodule(frame)
        name = module.__name__ or "<Unknown Module>"
        _logger = logging.getLogger(f'{name} {line}')
        _logger.error(e)
        if _logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()


@contextmanager
def fix_error_msg(msgs: Dict[Type[Exception], str]):
    try:
        yield
    except Exception as e:
        err_class = type(e)
        if err_class in msgs:
            e.args = (msgs[err_class], )
        raise


class TextBufferHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to Blender's internal text buffer.
    """

    terminator = '\n'

    def __init__(self, name):
        """
        Initialize the handler.
        """
        super().__init__()
        self.buffer_name = name
        if self.buffer is None:
            raise RuntimeError("Can't create TextBufferHandler, "
                               "most likely because Blender is not fully loaded")

    def emit(self, record):
        """
        Emit a record.
        If a formatter is specified, it is used to format the record.
        The record is then written to the buffer with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # wen user enables a Sverchok extension it seems disables all Blender
        # collections until the extension will be registered
        # for now ignore such cases
        if self.buffer is None:
            return

        try:
            msg = self.format(record)
            self.buffer.write(msg)
            self.buffer.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    def clear(self):
        """Clear all records"""
        self.buffer.clear()
        sv_logger.debug("Internal text buffer cleared")

    @property
    def buffer(self) -> Optional:
        """
        Get internal blender text buffer for logging.
        """
        try:
            return bpy.data.texts.get(self.buffer_name) \
                   or bpy.data.texts.new(name=self.buffer_name)
        except AttributeError as e:
            # logging.debug("Can't initialize logging to internal buffer: get_log_buffer is called too early: {}".format(e))
            return None

    @classmethod
    def add_to_main_logger(cls):
        """This handler can work only after Blender is fully loaded"""
        addon = bpy.context.preferences.addons.get(sverchok.__name__)
        prefs = addon.preferences
        if prefs.log_to_buffer:
            sv_logger.debug(f'Logging to Blender text editor="{prefs.log_buffer_name}"')
            handler = cls(prefs.log_buffer_name)
            handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
            sv_logger.addHandler(handler)

    def __repr__(self):
        level = logging.getLevelName(self.level)
        name = getattr(self.buffer, 'name', '')
        if name:
            name += ' '
        return '<%s %s(%s)>' % (self.__class__.__name__, name, level)


# Convenience functions


def get_logger(name=None):
    """Get Logger instance. Logger name is obtained from caller module name."""
    if name is None:
        frame, *_ = inspect.stack()[1]
        module = inspect.getmodule(frame)
        name = module.__name__
    return logging.getLogger(name)


def is_enabled_for(log_level="DEBUG") -> bool:
    """This check should be used for improving performance of calling disabled loggers"""
    addon = bpy.context.preferences.addons.get(sverchok.__name__)
    current_level = getattr(logging, addon.preferences.log_level)
    given_level = getattr(logging, log_level)
    return given_level >= current_level
