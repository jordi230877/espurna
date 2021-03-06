# coding=utf-8
# pylint: dummy-variables-rgx='(_+[a-zA-Z0-9]*?$)|dummy|env'
#
# Original extra_scripts.py
# Copyright (C) 2016-2019 by Xose Pérez <xose dot perez at gmail dot com>
#
# ldscripts, lwip patching, updated postmortem flags and git support
# Copyright (C) 2019-2020 by Maxim Prokhorov <prokhorov dot max at outlook dot com>

# Run this script every time building an env BEFORE platform-specific code is loaded

from __future__ import print_function

Import("env")

import os
import sys


from SCons.Script import ARGUMENTS


TRAVIS = os.environ.get("TRAVIS")
PIO_PLATFORM = env.PioPlatform()
CONFIG = env.GetProjectConfig()
VERBOSE = "1" == ARGUMENTS.get("PIOVERBOSE", "0")


class ExtraScriptError(Exception):
    pass


def log(message, verbose=False, file=sys.stderr):
    if verbose or VERBOSE:
        print(message, file=file)


# Most portable way, without depending on platformio internals
def subprocess_libdeps(lib_deps, storage=None, silent=True):
    import subprocess

    args = [env.subst("$PYTHONEXE"), "-mplatformio", "lib"]
    if not storage:
        args.append("-g")
    else:
        args.extend(["-d", storage])
    args.append("install")
    if silent:
        args.append("-s")

    args.extend(lib_deps)

    subprocess.check_call(args)


# Avoid spawning pio lib every time, hook into the LibraryManager API (sort-of internal)
def library_manager_libdeps(lib_deps, storage=None):
    from platformio.managers.lib import LibraryManager
    from platformio.project.helpers import get_project_global_lib_dir

    if not storage:
        manager = LibraryManager(get_project_global_lib_dir())
    else:
        manager = LibraryManager(storage)

    for lib in lib_deps:
        if manager.get_package_dir(*manager.parse_pkg_uri(lib)):
            continue
        log("installing: {}".format(lib))
        manager.install(lib)


def get_shared_libdeps_dir(section, name):

    if not CONFIG.has_option(section, name):
        raise ExtraScriptError("{}.{} is required to be set".format(section, name))

    opt = CONFIG.get(section, name)

    if not opt in env.GetProjectOption("lib_extra_dirs"):
        raise ExtraScriptError(
            "lib_extra_dirs must contain {}.{}".format(section, name)
        )

    return os.path.join(env["PROJECT_DIR"], opt)


def ensure_platform_updated():
    try:
        if PIO_PLATFORM.are_outdated_packages():
            log("updating platform packages")
            PIO_PLATFORM.update_packages()
    except Exception:
        log("Warning: no connection, cannot check for outdated packages", verbose=True)


# handle OTA uploads
# using env instead of ini to fix platformio ini changing hash on every change
env.Append(
    ESPURNA_BOARD=os.environ.get("ESPURNA_BOARD", ""),
    ESPURNA_AUTH=os.environ.get("ESPURNA_AUTH", ""),
    ESPURNA_FLAGS=os.environ.get("ESPURNA_FLAGS", "")
)

ESPURNA_OTA_PORT = os.environ.get("ESPURNA_IP")
if ESPURNA_OTA_PORT:
    env.Replace(UPLOAD_PROTOCOL="espota")
    env.Replace(UPLOAD_PORT=ESPURNA_OTA_PORT)
    env.Replace(UPLOAD_FLAGS="--auth=$ESPURNA_AUTH")
else:
    env.Replace(UPLOAD_PROTOCOL="esptool")

# latest toolchain is still optional with PIO (TODO: recheck after 2.6.0!)
# also updates arduino core git to the latest master commit
if TRAVIS and (
    env.GetProjectOption("platform") == CONFIG.get("common", "arduino_core_git")
):
    ensure_platform_updated()

# to speed-up build process, install libraries in either global or local shared storage
if os.environ.get("ESPURNA_PIO_SHARED_LIBRARIES"):
    if TRAVIS:
        storage = None
        log("using global library storage")
    else:
        storage = get_shared_libdeps_dir("common", "shared_libdeps_dir")
        log("using shared library storage: {}".format(storage))

    subprocess_libdeps(env.GetProjectOption("lib_deps"), storage)
