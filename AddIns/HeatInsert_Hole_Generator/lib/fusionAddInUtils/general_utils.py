# lib/fusionAddInUtils/general_utils.py
# General utility functions for Fusion 360 add-ins

import adsk.core
import adsk.fusion


def get_app():
    """Get the Fusion 360 application instance."""
    return adsk.core.Application.get()


def get_ui():
    """Get the Fusion 360 user interface instance."""
    return get_app().userInterface


def get_design():
    """Get the active design, or None if not in a design workspace."""
    app = get_app()
    product = app.activeProduct
    if product and product.objectType == adsk.fusion.Design.classType():
        return adsk.fusion.Design.cast(product)
    return None


def show_message(message, title='Heat Insert Hole Generator'):
    """Show a message box to the user."""
    get_ui().messageBox(message, title)


def cm_to_mm(cm_value):
    """Convert centimeters to millimeters."""
    return cm_value * 10


def mm_to_cm(mm_value):
    """Convert millimeters to centimeters (Fusion internal units)."""
    return mm_value / 10
