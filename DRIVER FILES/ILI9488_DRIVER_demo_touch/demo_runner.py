"""
demo_runner.py
==============

Memory-conscious dynamic demonstration loader.

Version: 0.7.1
"""

import gc
import sys


DEMO_MODULES = (
    "demo_primitives",
    "demo_text",
    "demo_advanced",
    "demo_media",
)


def _unload(module_name, module):
    """Release a dynamically imported demonstration module."""
    del module

    try:
        del sys.modules[module_name]
    except KeyError:
        pass

    gc.collect()


def run_module(
    module_name,
    gfx,
    lcd,
    touch=None,
    auto=False,
):
    """Import, run and unload one demonstration module."""
    gc.collect()

    module = __import__(module_name)

    try:
        module.run(
            gfx,
            lcd,
            touch=touch,
            auto=auto,
        )
    finally:
        _unload(
            module_name,
            module,
        )


def run_all(
    gfx,
    lcd,
    touch=None,
    auto=True,
):
    """Run the complete retained display demonstration suite."""
    for module_name in DEMO_MODULES:
        run_module(
            module_name,
            gfx,
            lcd,
            touch=touch,
            auto=auto,
        )
