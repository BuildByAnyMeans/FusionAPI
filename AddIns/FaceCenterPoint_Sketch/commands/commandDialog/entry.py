"""
Face Center Point Sketch Command
Places sketch points at the center of selected face(s) in the active sketch.
"""

import adsk.core
import adsk.fusion
import traceback
import os
import math

app = adsk.core.Application.get()
ui = app.userInterface

# Command identifiers and info
COMMAND_ID = 'FaceCenterPoint_Sketch_Cmd'
COMMAND_NAME = 'Face Center Point'
COMMAND_DESCRIPTION = 'Places a sketch point at the center of selected face(s) in the active sketch'

# Input IDs
FACE_SELECTION_INPUT_ID = 'faceSelection'
CENTER_METHOD_INPUT_ID = 'centerMethod'
CONSTRUCTION_INPUT_ID = 'isConstruction'

# Center calculation methods
CENTER_METHOD_PARAMETRIC = 'Parametric center'
CENTER_METHOD_BOUNDING = 'Bounding box center'

# Global handlers list to keep them alive
handlers = []

# Command definition reference
command_definition = None


def start():
    """Initialize and create the command."""
    global command_definition
    
    try:
        # Get the command definitions collection
        cmd_defs = ui.commandDefinitions
        
        # Check if command already exists, delete it if so
        existing_def = cmd_defs.itemById(COMMAND_ID)
        if existing_def:
            existing_def.deleteMe()
        
        # Get resource folder path for icons
        resource_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
        
        # Create command definition
        command_definition = cmd_defs.addButtonDefinition(
            COMMAND_ID,
            COMMAND_NAME,
            COMMAND_DESCRIPTION,
            resource_folder
        )
        
        # Add command created handler
        on_command_created = CommandCreatedHandler()
        command_definition.commandCreated.add(on_command_created)
        handlers.append(on_command_created)
        
        # Add command to the SKETCH toolbar - Create panel
        # Get the Sketch Create panel
        design_workspace = ui.workspaces.itemById('FusionSolidEnvironment')
        if design_workspace:
            sketch_panel = design_workspace.toolbarPanels.itemById('SketchCreatePanel')
            if sketch_panel:
                # Check if control already exists
                existing_control = sketch_panel.controls.itemById(COMMAND_ID)
                if not existing_control:
                    control = sketch_panel.controls.addCommand(command_definition)
                    control.isPromoted = True
                    control.isPromotedByDefault = True
        
    except:
        if ui:
            ui.messageBox(f'Failed to start command:\n{traceback.format_exc()}')


def stop():
    """Clean up the command when add-in stops."""
    try:
        # Remove the command from the panel
        design_workspace = ui.workspaces.itemById('FusionSolidEnvironment')
        if design_workspace:
            sketch_panel = design_workspace.toolbarPanels.itemById('SketchCreatePanel')
            if sketch_panel:
                control = sketch_panel.controls.itemById(COMMAND_ID)
                if control:
                    control.deleteMe()
        
        # Delete the command definition
        cmd_def = ui.commandDefinitions.itemById(COMMAND_ID)
        if cmd_def:
            cmd_def.deleteMe()
            
        # Clear handlers
        handlers.clear()
        
    except:
        if ui:
            ui.messageBox(f'Failed to stop command:\n{traceback.format_exc()}')


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Handler for command created event - sets up the command dialog UI."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            
            # Check if we're in an active sketch
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('No active design. Please open a design first.')
                return
            
            active_sketch = design.activeEditObject
            if not active_sketch or not isinstance(active_sketch, adsk.fusion.Sketch):
                ui.messageBox('Please enter sketch edit mode first.\n\nDouble-click a sketch to edit it, then run this command.')
                return
            
            # === Profile Selection Input ===
            face_selection = inputs.addSelectionInput(
                FACE_SELECTION_INPUT_ID,
                'Profiles',
                'Select one or more sketch profiles'
            )
            face_selection.addSelectionFilter('Profiles')
            face_selection.setSelectionLimits(1, 0)  # Minimum 1, no maximum
            
            # === Center Calculation Method Dropdown ===
            center_method = inputs.addDropDownCommandInput(
                CENTER_METHOD_INPUT_ID,
                'Center Method',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            center_method.listItems.add(CENTER_METHOD_PARAMETRIC, True)
            center_method.listItems.add(CENTER_METHOD_BOUNDING, False)
            
            # === Construction Point Checkbox ===
            construction_input = inputs.addBoolValueInput(
                CONSTRUCTION_INPUT_ID,
                'Construction Point',
                True,
                '',
                False
            )
            
            # Add event handlers for the command
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
            
            on_preview = CommandPreviewHandler()
            cmd.executePreview.add(on_preview)
            handlers.append(on_preview)
            
            on_validate = CommandValidateHandler()
            cmd.validateInputs.add(on_validate)
            handlers.append(on_validate)
            
            on_destroy = CommandDestroyHandler()
            cmd.destroy.add(on_destroy)
            handlers.append(on_destroy)
            
        except:
            if ui:
                ui.messageBox(f'Command created failed:\n{traceback.format_exc()}')


class CommandValidateHandler(adsk.core.ValidateInputsEventHandler):
    """Handler for validating inputs - enables/disables OK button."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.ValidateInputsEventArgs):
        try:
            inputs = args.inputs
            face_selection = inputs.itemById(FACE_SELECTION_INPUT_ID)
            
            # OK button is enabled only if at least one face is selected
            args.areInputsValid = face_selection.selectionCount > 0
            
        except:
            args.areInputsValid = False


class CommandPreviewHandler(adsk.core.CommandEventHandler):
    """Handler for command preview - shows preview of points."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            # Get the command inputs
            inputs = args.command.commandInputs
            
            # Create the points (preview)
            create_center_points(inputs, is_preview=True)
            
        except:
            if ui:
                ui.messageBox(f'Preview failed:\n{traceback.format_exc()}')


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    """Handler for command execute - creates the sketch points."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            # Get the command inputs
            inputs = args.command.commandInputs
            
            # Create the points (final)
            create_center_points(inputs, is_preview=False)
            
        except:
            if ui:
                ui.messageBox(f'Execute failed:\n{traceback.format_exc()}')


class CommandDestroyHandler(adsk.core.CommandEventHandler):
    """Handler for command destroy."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        # Clean up if needed
        pass


def get_profile_center_parametric(profile: adsk.fusion.Profile) -> adsk.core.Point3D:
    """
    Calculate the parametric center (area centroid) of a sketch profile.
    Uses the profile's area properties to get the true centroid.
    """
    try:
        # Get the area properties of the profile
        area_props = profile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy)
        
        if area_props:
            centroid = area_props.centroid
            return centroid
        else:
            # Fallback to bounding box center
            return get_profile_center_bounding(profile)
            
    except:
        return get_profile_center_bounding(profile)


def get_profile_center_bounding(profile: adsk.fusion.Profile) -> adsk.core.Point3D:
    """
    Calculate the center using the profile's bounding box.
    """
    try:
        bbox = profile.boundingBox
        
        center_x = (bbox.minPoint.x + bbox.maxPoint.x) / 2.0
        center_y = (bbox.minPoint.y + bbox.maxPoint.y) / 2.0
        center_z = (bbox.minPoint.z + bbox.maxPoint.z) / 2.0
        
        return adsk.core.Point3D.create(center_x, center_y, center_z)
        
    except:
        if ui:
            ui.messageBox(f'Failed to get bounding box center:\n{traceback.format_exc()}')
        return None


def create_center_points(inputs: adsk.core.CommandInputs, is_preview: bool = False):
    """
    Create sketch points at the center of each selected profile.
    
    Args:
        inputs: The command inputs containing selections and options
        is_preview: Whether this is a preview (True) or final execution (False)
    """
    try:
        # Get the design and active sketch
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            return
        
        active_sketch = design.activeEditObject
        if not active_sketch or not isinstance(active_sketch, adsk.fusion.Sketch):
            if not is_preview:
                ui.messageBox('No active sketch. Please edit a sketch first.')
            return
        
        # Get input values
        profile_selection = inputs.itemById(FACE_SELECTION_INPUT_ID)
        center_method_input = inputs.itemById(CENTER_METHOD_INPUT_ID)
        construction_input = inputs.itemById(CONSTRUCTION_INPUT_ID)
        
        if profile_selection.selectionCount == 0:
            return
        
        # Get options
        use_parametric = center_method_input.selectedItem.name == CENTER_METHOD_PARAMETRIC
        is_construction = construction_input.value
        
        # Get the sketch points collection
        sketch_points = active_sketch.sketchPoints
        
        # Process each selected profile
        for i in range(profile_selection.selectionCount):
            profile = adsk.fusion.Profile.cast(profile_selection.selection(i).entity)
            if not profile:
                continue
            
            # Calculate center point based on selected method
            if use_parametric:
                center_3d = get_profile_center_parametric(profile)
            else:
                center_3d = get_profile_center_bounding(profile)
            
            if not center_3d:
                continue
            
            # Create sketch point at the center location
            sketch_point = sketch_points.add(center_3d)
            
            # Set as construction if requested
            if is_construction and sketch_point:
                sketch_point.isConstruction = True
        
    except:
        if not is_preview and ui:
            ui.messageBox(f'Failed to create center points:\n{traceback.format_exc()}')