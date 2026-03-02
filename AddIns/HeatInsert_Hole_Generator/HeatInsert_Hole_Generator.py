# HeatInsert_Hole_Generator.py
# Fusion 360 Add-In: Generate Heat-Set Insert Holes
# Author: Parker

import adsk.core
import traceback

# Global handlers list to keep references alive
handlers = []

def run(context):
    """Called when the add-in is run."""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Import and start the command
        from .commands.commandDialog import entry as commandDialog
        commandDialog.start()

    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'Failed to start add-in:\n{traceback.format_exc()}')


def stop(context):
    """Called when the add-in is stopped."""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Stop the command
        from .commands.commandDialog import entry as commandDialog
        commandDialog.stop()

    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'Failed to stop add-in:\n{traceback.format_exc()}')
