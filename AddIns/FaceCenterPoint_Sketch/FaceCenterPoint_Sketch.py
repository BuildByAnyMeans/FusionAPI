"""
FaceCenterPoint_Sketch Add-In
Places sketch points at the center of selected face(s) while editing a sketch.

Author: Parker
"""

import adsk.core
import adsk.fusion
import traceback
import os

# Import the command modules
from .commands.commandDialog import entry as commandDialog

# Global list to keep command definitions alive
commands = []
app = adsk.core.Application.get()
ui = app.userInterface


def run(context):
    """Called when the add-in is run."""
    try:
        # Initialize the command
        commandDialog.start()
        commands.append(commandDialog)
        
    except:
        if ui:
            ui.messageBox(f'Failed to start FaceCenterPoint_Sketch:\n{traceback.format_exc()}')


def stop(context):
    """Called when the add-in is stopped."""
    try:
        # Stop and clean up commands
        for cmd in commands:
            cmd.stop()
        commands.clear()
        
    except:
        if ui:
            ui.messageBox(f'Failed to stop FaceCenterPoint_Sketch:\n{traceback.format_exc()}')
