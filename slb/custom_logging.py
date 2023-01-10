"""
Module used to setup the default logging and messaging system.
The system contains on a python logging based approach with logfile,
console output and GUI output dependent on startup options and
message logLevel.
"""

import logging
import sys

from . import BASE_PATH, __version__ as str_version

# default options used if nothing is set in the configuration
CONSOLE_LEVEL, FILE_LEVEL, GUI_LEVEL = logging.WARNING, logging.DEBUG, logging.ERROR

# set log levels according to options
if "pdb" in list(sys.modules.keys()) or "pydevd" in list(sys.modules.keys()):
    # if common debugger modules have been loaded, assume a debug run
    CONSOLE_LEVEL, FILE_LEVEL, GUI_LEVEL = logging.INFO, logging.DEBUG, logging.ERROR
elif "--debug" in sys.argv:
    CONSOLE_LEVEL, FILE_LEVEL, GUI_LEVEL = logging.DEBUG, logging.DEBUG, logging.ERROR


def setup_system():
    logger = logging.getLogger()
    logger.setLevel(min(CONSOLE_LEVEL, FILE_LEVEL, GUI_LEVEL))

    # no console logger for windows (win32gui)
    console = logging.StreamHandler(sys.__stdout__)
    formatter = logging.Formatter("%(levelname) 7s: %(message)s")
    console.setFormatter(formatter)
    console.setLevel(CONSOLE_LEVEL)
    logger.addHandler(console)

    logfile = logging.FileHandler("sonos_gui.log", "w", encoding="utf-8")
    logger.setLevel(min(logger.getEffectiveLevel(), FILE_LEVEL))
    formatter = logging.Formatter(
        "%(levelname)s: %(asctime)s - " "%(threadName)s:%(filename)s:%(lineno)i:%(funcName)s " "| %(message)s", ""
    )
    logfile.setFormatter(formatter)
    logfile.setLevel(FILE_LEVEL)
    logger.addHandler(logfile)

    logging.info(f"*** Sonos Library Browser {str_version} Logging started ***")
    logging.debug(f'BASE_PATH at {BASE_PATH}')
    activate_excepthook()


_prev_excepthook = None


def excepthook_overwrite(*exc_info):
    # making sure all exceptions are displayed on GUI and logged
    # noinspection PyTypeChecker
    logging.critical("uncought python error", exc_info=exc_info, stacklevel=3)
    # noinspection PyCallingNonCallable
    return _prev_excepthook(*exc_info)


def activate_excepthook():
    logging.debug("replacing sys.excepthook with user function")
    global _prev_excepthook
    _prev_excepthook = sys.excepthook
    sys.excepthook = excepthook_overwrite
