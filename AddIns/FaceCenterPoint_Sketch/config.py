"""
Configuration for FaceCenterPoint_Sketch Add-In
"""

import os

# Add-in information
ADDIN_NAME = 'FaceCenterPoint_Sketch'
COMPANY_NAME = ''

# Command information - will appear in SKETCH toolbar
COMMAND_ID = 'FaceCenterPoint_Sketch_Cmd'
COMMAND_NAME = 'Face Center Point'
COMMAND_DESCRIPTION = 'Places a sketch point at the center of selected face(s)'
IS_PROMOTED = True

# Panel location - SKETCH toolbar, Create panel
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SketchCreatePanel'
COMMAND_BESIDE_ID = ''

# Resources
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commands', 'commandDialog', 'resources')

# Input IDs
FACE_SELECTION_INPUT_ID = 'faceSelection'
CENTER_METHOD_INPUT_ID = 'centerMethod'
CONSTRUCTION_INPUT_ID = 'isConstruction'

# Center calculation methods
CENTER_METHOD_PARAMETRIC = 'Parametric center'
CENTER_METHOD_BOUNDING = 'Bounding box center'
