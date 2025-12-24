"""
General Utilities for Fusion 360 Add-Ins
Common helper functions.
"""

import adsk.core
import adsk.fusion
import os


def get_app_objects():
    """
    Get the standard Fusion 360 application objects.
    
    Returns:
        tuple: (app, ui, design, root_comp) or None values if not available
    """
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    
    design = None
    root_comp = None
    
    if app and app.activeProduct:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design:
            root_comp = design.rootComponent
    
    return app, ui, design, root_comp


def get_add_in_path():
    """
    Get the path to the add-in folder.
    
    Returns:
        str: Path to the add-in folder
    """
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
