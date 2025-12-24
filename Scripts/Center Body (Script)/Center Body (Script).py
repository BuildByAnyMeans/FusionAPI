#Author: Parker (spec) / Claude (implementation)
#Description: Move a body so its center aligns between selected references

import adsk.core, adsk.fusion, traceback
import math

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL HANDLERS LIST (prevents garbage collection)
# ══════════════════════════════════════════════════════════════════════════════
handlers = []

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
COMMAND_ID = "CenterBodyCommand"
COMMAND_NAME = "Center Body"
COMMAND_TOOLTIP = "Move a body so its center aligns between selected references."

# Center method options
CENTER_BOUNDING_BOX = "Bounding Box Center"
CENTER_OF_MASS = "Center of Mass"

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_plane_position_on_axis(entity, axis_index: int) -> float:
    """
    Extract the position of a planar entity along a specific axis.
    axis_index: 0=X, 1=Y, 2=Z
    
    Returns the coordinate value along that axis, or None if not determinable.
    """
    # Handle BRepFace (planar face)
    if isinstance(entity, adsk.fusion.BRepFace):
        geom = entity.geometry
        if isinstance(geom, adsk.core.Plane):
            origin = geom.origin
            return [origin.x, origin.y, origin.z][axis_index]
        else:
            # Non-planar face - try to use bounding box center
            bbox = entity.boundingBox
            if bbox:
                min_pt = bbox.minPoint
                max_pt = bbox.maxPoint
                center = [(min_pt.x + max_pt.x) / 2, 
                          (min_pt.y + max_pt.y) / 2, 
                          (min_pt.z + max_pt.z) / 2]
                return center[axis_index]
            return None
    
    # Handle ConstructionPlane
    elif isinstance(entity, adsk.fusion.ConstructionPlane):
        geom = entity.geometry
        origin = geom.origin
        return [origin.x, origin.y, origin.z][axis_index]
    
    # Handle BRepEdge (linear edge)
    elif isinstance(entity, adsk.fusion.BRepEdge):
        start_pt = entity.startVertex.geometry if entity.startVertex else None
        end_pt = entity.endVertex.geometry if entity.endVertex else None
        if start_pt and end_pt:
            mid = [(start_pt.x + end_pt.x) / 2,
                   (start_pt.y + end_pt.y) / 2,
                   (start_pt.z + end_pt.z) / 2]
            return mid[axis_index]
        return None
    
    # Handle SketchLine
    elif isinstance(entity, adsk.fusion.SketchLine):
        start_pt = entity.startSketchPoint.geometry
        end_pt = entity.endSketchPoint.geometry
        sketch = entity.parentSketch
        transform = sketch.transform
        start_world = adsk.core.Point3D.create(start_pt.x, start_pt.y, 0)
        end_world = adsk.core.Point3D.create(end_pt.x, end_pt.y, 0)
        start_world.transformBy(transform)
        end_world.transformBy(transform)
        mid = [(start_world.x + end_world.x) / 2,
               (start_world.y + end_world.y) / 2,
               (start_world.z + end_world.z) / 2]
        return mid[axis_index]
    
    # Handle ConstructionAxis
    elif isinstance(entity, adsk.fusion.ConstructionAxis):
        geom = entity.geometry
        origin = geom.origin
        return [origin.x, origin.y, origin.z][axis_index]
    
    # Handle ConstructionPoint
    elif isinstance(entity, adsk.fusion.ConstructionPoint):
        geom = entity.geometry
        return [geom.x, geom.y, geom.z][axis_index]
    
    # Handle SketchPoint
    elif isinstance(entity, adsk.fusion.SketchPoint):
        sketch = entity.parentSketch
        transform = sketch.transform
        pt = entity.geometry
        world_pt = adsk.core.Point3D.create(pt.x, pt.y, 0)
        world_pt.transformBy(transform)
        return [world_pt.x, world_pt.y, world_pt.z][axis_index]
    
    return None


def compute_center_between_refs(ref1, ref2, axis_index: int) -> float:
    """
    Compute the center coordinate between two reference entities along an axis.
    """
    pos1 = get_plane_position_on_axis(ref1, axis_index)
    pos2 = get_plane_position_on_axis(ref2, axis_index)
    
    if pos1 is not None and pos2 is not None:
        return (pos1 + pos2) / 2.0
    return None


def get_body_bounding_box_center(body: adsk.fusion.BRepBody) -> adsk.core.Point3D:
    """Get the bounding box center of a body."""
    bbox = body.boundingBox
    if not bbox:
        return None
    
    min_pt = bbox.minPoint
    max_pt = bbox.maxPoint
    
    return adsk.core.Point3D.create(
        (min_pt.x + max_pt.x) / 2.0,
        (min_pt.y + max_pt.y) / 2.0,
        (min_pt.z + max_pt.z) / 2.0
    )


def get_body_center_of_mass(body: adsk.fusion.BRepBody) -> adsk.core.Point3D:
    """Get the center of mass of a body."""
    try:
        props = body.physicalProperties
        if props:
            com = props.centerOfMass
            return adsk.core.Point3D.create(com.x, com.y, com.z)
    except:
        pass
    return None


def get_occurrence_bounding_box_center(occ: adsk.fusion.Occurrence) -> adsk.core.Point3D:
    """Get the bounding box center of an occurrence."""
    bbox = occ.boundingBox
    if not bbox:
        return None
    
    min_pt = bbox.minPoint
    max_pt = bbox.maxPoint
    
    return adsk.core.Point3D.create(
        (min_pt.x + max_pt.x) / 2.0,
        (min_pt.y + max_pt.y) / 2.0,
        (min_pt.z + max_pt.z) / 2.0
    )


def move_body_by_vector(body: adsk.fusion.BRepBody, vector: adsk.core.Vector3D, 
                        feature_name: str = "Center Body") -> bool:
    """Move a body using a Move feature."""
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    
    parentComp = body.parentComponent
    moveFeatures = parentComp.features.moveFeatures
    
    inputEntities = adsk.core.ObjectCollection.create()
    inputEntities.add(body)
    
    transform = adsk.core.Matrix3D.create()
    transform.translation = vector
    
    moveInput = moveFeatures.createInput2(inputEntities)
    moveInput.defineAsFreeMove(transform)
    
    moveFeature = moveFeatures.add(moveInput)
    
    if moveFeature:
        timelineObj = moveFeature.timelineObject
        if timelineObj:
            timelineObj.name = feature_name
        return True
    
    return False


def move_occurrence_by_vector(occ: adsk.fusion.Occurrence, vector: adsk.core.Vector3D) -> bool:
    """Move an occurrence by modifying its transform."""
    try:
        currentTransform = occ.transform
        
        translationMatrix = adsk.core.Matrix3D.create()
        translationMatrix.translation = vector
        
        translationMatrix.transformBy(currentTransform)
        occ.transform = translationMatrix
        
        return True
    except:
        return False


def add_reference_selection_filters(selInput: adsk.core.SelectionCommandInput):
    """Add standard reference geometry filters to a selection input."""
    selInput.addSelectionFilter("PlanarFaces")
    selInput.addSelectionFilter("ConstructionPlanes")
    selInput.addSelectionFilter("LinearEdges")
    selInput.addSelectionFilter("SketchLines")
    selInput.addSelectionFilter("ConstructionPoints")
    selInput.addSelectionFilter("SketchPoints")


def update_axis_input_visibility(inputs: adsk.core.CommandInputs):
    """Update visibility of axis reference inputs based on checkboxes."""
    centerX = inputs.itemById("centerX")
    centerY = inputs.itemById("centerY")
    centerZ = inputs.itemById("centerZ")
    
    # X axis inputs
    xRef1 = inputs.itemById("xRef1")
    xRef2 = inputs.itemById("xRef2")
    xOffset = inputs.itemById("xOffset")
    if xRef1 and xRef2 and xOffset and centerX:
        xRef1.isVisible = centerX.value
        xRef2.isVisible = centerX.value
        xOffset.isVisible = centerX.value
    
    # Y axis inputs
    yRef1 = inputs.itemById("yRef1")
    yRef2 = inputs.itemById("yRef2")
    yOffset = inputs.itemById("yOffset")
    if yRef1 and yRef2 and yOffset and centerY:
        yRef1.isVisible = centerY.value
        yRef2.isVisible = centerY.value
        yOffset.isVisible = centerY.value
    
    # Z axis inputs
    zRef1 = inputs.itemById("zRef1")
    zRef2 = inputs.itemById("zRef2")
    zOffset = inputs.itemById("zOffset")
    if zRef1 and zRef2 and zOffset and centerZ:
        zRef1.isVisible = centerZ.value
        zRef2.isVisible = centerZ.value
        zOffset.isVisible = centerZ.value


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND EVENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

class CenterBodyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            
            # ─────────────────────────────────────────────────────────────────
            # TARGET SELECTION (flat, no group)
            # ─────────────────────────────────────────────────────────────────
            targetSelection = inputs.addSelectionInput(
                "targetSelection", 
                "Target Body/Component", 
                "Select the body or component to center"
            )
            targetSelection.addSelectionFilter("Bodies")
            targetSelection.addSelectionFilter("Occurrences")
            targetSelection.setSelectionLimits(1, 1)
            
            # ─────────────────────────────────────────────────────────────────
            # CENTER METHOD
            # ─────────────────────────────────────────────────────────────────
            centerMethodDropdown = inputs.addDropDownCommandInput(
                "centerMethod",
                "Center Method",
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            centerMethodDropdown.listItems.add(CENTER_BOUNDING_BOX, True)
            centerMethodDropdown.listItems.add(CENTER_OF_MASS, False)
            
            # ─────────────────────────────────────────────────────────────────
            # AXIS ENABLE CHECKBOXES
            # ─────────────────────────────────────────────────────────────────
            inputs.addBoolValueInput("centerX", "Center on X Axis", True, "", True)
            inputs.addBoolValueInput("centerY", "Center on Y Axis", True, "", True)
            inputs.addBoolValueInput("centerZ", "Center on Z Axis", True, "", False)
            
            # ─────────────────────────────────────────────────────────────────
            # X AXIS REFERENCES (flat)
            # ─────────────────────────────────────────────────────────────────
            xRef1 = inputs.addSelectionInput("xRef1", "X Ref 1 (Left)", "Select left reference")
            add_reference_selection_filters(xRef1)
            xRef1.setSelectionLimits(0, 1)
            
            xRef2 = inputs.addSelectionInput("xRef2", "X Ref 2 (Right)", "Select right reference")
            add_reference_selection_filters(xRef2)
            xRef2.setSelectionLimits(0, 1)
            
            inputs.addValueInput("xOffset", "X Offset", "mm", adsk.core.ValueInput.createByString("0 mm"))
            
            # ─────────────────────────────────────────────────────────────────
            # Y AXIS REFERENCES (flat)
            # ─────────────────────────────────────────────────────────────────
            yRef1 = inputs.addSelectionInput("yRef1", "Y Ref 1 (Front)", "Select front reference")
            add_reference_selection_filters(yRef1)
            yRef1.setSelectionLimits(0, 1)
            
            yRef2 = inputs.addSelectionInput("yRef2", "Y Ref 2 (Back)", "Select back reference")
            add_reference_selection_filters(yRef2)
            yRef2.setSelectionLimits(0, 1)
            
            inputs.addValueInput("yOffset", "Y Offset", "mm", adsk.core.ValueInput.createByString("0 mm"))
            
            # ─────────────────────────────────────────────────────────────────
            # Z AXIS REFERENCES (flat, initially hidden)
            # ─────────────────────────────────────────────────────────────────
            zRef1 = inputs.addSelectionInput("zRef1", "Z Ref 1 (Bottom)", "Select bottom reference")
            add_reference_selection_filters(zRef1)
            zRef1.setSelectionLimits(0, 1)
            zRef1.isVisible = False
            
            zRef2 = inputs.addSelectionInput("zRef2", "Z Ref 2 (Top)", "Select top reference")
            add_reference_selection_filters(zRef2)
            zRef2.setSelectionLimits(0, 1)
            zRef2.isVisible = False
            
            zOffsetInput = inputs.addValueInput("zOffset", "Z Offset", "mm", adsk.core.ValueInput.createByString("0 mm"))
            zOffsetInput.isVisible = False
            
            # ─────────────────────────────────────────────────────────────────
            # CONNECT EVENT HANDLERS
            # ─────────────────────────────────────────────────────────────────
            onExecute = CenterBodyCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            onInputChanged = CenterBodyInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
            
            onValidateInputs = CenterBodyValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            handlers.append(onValidateInputs)
            
            onPreview = CenterBodyPreviewHandler()
            cmd.executePreview.add(onPreview)
            handlers.append(onPreview)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox(f'CommandCreated failed:\n{traceback.format_exc()}')


class CenterBodyInputChangedHandler(adsk.core.InputChangedEventHandler):
    """Handle UI changes - show/hide reference inputs based on axis checkboxes."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.InputChangedEventArgs):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            changedInput = args.input
            
            # Update visibility when axis checkboxes change
            if changedInput.id in ["centerX", "centerY", "centerZ"]:
                update_axis_input_visibility(inputs)
                    
        except:
            pass


class CenterBodyValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    """Validate that required inputs are provided."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.ValidateInputsEventArgs):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            
            # Check target selection
            targetSelection = inputs.itemById("targetSelection")
            if not targetSelection or targetSelection.selectionCount < 1:
                args.areInputsValid = False
                return
            
            # Get axis states
            centerX = inputs.itemById("centerX").value
            centerY = inputs.itemById("centerY").value
            centerZ = inputs.itemById("centerZ").value
            
            # At least one axis must be enabled
            if not (centerX or centerY or centerZ):
                args.areInputsValid = False
                return
            
            # For each enabled axis, both references must be selected
            if centerX:
                xRef1 = inputs.itemById("xRef1")
                xRef2 = inputs.itemById("xRef2")
                if xRef1.selectionCount < 1 or xRef2.selectionCount < 1:
                    args.areInputsValid = False
                    return
            
            if centerY:
                yRef1 = inputs.itemById("yRef1")
                yRef2 = inputs.itemById("yRef2")
                if yRef1.selectionCount < 1 or yRef2.selectionCount < 1:
                    args.areInputsValid = False
                    return
            
            if centerZ:
                zRef1 = inputs.itemById("zRef1")
                zRef2 = inputs.itemById("zRef2")
                if zRef1.selectionCount < 1 or zRef2.selectionCount < 1:
                    args.areInputsValid = False
                    return
            
            args.areInputsValid = True
            
        except:
            args.areInputsValid = False


class CenterBodyPreviewHandler(adsk.core.CommandEventHandler):
    """Handle preview."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            execute_centering(inputs, preview=True)
        except:
            pass


class CenterBodyCommandExecuteHandler(adsk.core.CommandEventHandler):
    """Execute the centering operation."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs
            execute_centering(inputs, preview=False)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox(f'Execute failed:\n{traceback.format_exc()}')


def execute_centering(inputs: adsk.core.CommandInputs, preview: bool = False):
    """
    Core centering logic - compute translation and move target.
    """
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    
    # ─────────────────────────────────────────────────────────────────────────
    # GET TARGET
    # ─────────────────────────────────────────────────────────────────────────
    targetSelection = inputs.itemById("targetSelection")
    if targetSelection.selectionCount < 1:
        return
    targetEntity = targetSelection.selection(0).entity
    
    isBody = isinstance(targetEntity, adsk.fusion.BRepBody)
    isOccurrence = isinstance(targetEntity, adsk.fusion.Occurrence)
    
    # ─────────────────────────────────────────────────────────────────────────
    # GET CENTER METHOD
    # ─────────────────────────────────────────────────────────────────────────
    centerMethodDropdown = inputs.itemById("centerMethod")
    centerMethod = centerMethodDropdown.selectedItem.name
    
    # ─────────────────────────────────────────────────────────────────────────
    # COMPUTE TARGET CENTER POINT
    # ─────────────────────────────────────────────────────────────────────────
    targetCenter = None
    
    if isBody:
        body = targetEntity
        if centerMethod == CENTER_OF_MASS:
            targetCenter = get_body_center_of_mass(body)
            if not targetCenter:
                targetCenter = get_body_bounding_box_center(body)
                if not preview:
                    ui.messageBox("Center of mass unavailable. Using bounding box center.", 
                                  "Center Body - Warning")
        else:
            targetCenter = get_body_bounding_box_center(body)
    
    elif isOccurrence:
        occ = targetEntity
        targetCenter = get_occurrence_bounding_box_center(occ)
        if centerMethod == CENTER_OF_MASS and not preview:
            ui.messageBox("Center of mass not supported for occurrences. Using bounding box.", 
                          "Center Body - Info")
    
    if not targetCenter:
        if not preview:
            ui.messageBox("Could not determine target center point.", "Center Body - Error")
        return
    
    # ─────────────────────────────────────────────────────────────────────────
    # GET AXIS STATES AND COMPUTE DESIRED CENTERS
    # ─────────────────────────────────────────────────────────────────────────
    centerX = inputs.itemById("centerX").value
    centerY = inputs.itemById("centerY").value
    centerZ = inputs.itemById("centerZ").value
    
    deltaX = 0.0
    deltaY = 0.0
    deltaZ = 0.0
    
    # ─────────────────────────────────────────────────────────────────────────
    # X AXIS
    # ─────────────────────────────────────────────────────────────────────────
    if centerX:
        xRef1Sel = inputs.itemById("xRef1")
        xRef2Sel = inputs.itemById("xRef2")
        if xRef1Sel.selectionCount > 0 and xRef2Sel.selectionCount > 0:
            xRef1 = xRef1Sel.selection(0).entity
            xRef2 = xRef2Sel.selection(0).entity
            xOffset = inputs.itemById("xOffset").value
            
            desiredX = compute_center_between_refs(xRef1, xRef2, 0)
            if desiredX is not None:
                deltaX = (desiredX - targetCenter.x) + xOffset
            elif not preview:
                ui.messageBox("Could not compute X center from references.", "Center Body - Warning")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Y AXIS
    # ─────────────────────────────────────────────────────────────────────────
    if centerY:
        yRef1Sel = inputs.itemById("yRef1")
        yRef2Sel = inputs.itemById("yRef2")
        if yRef1Sel.selectionCount > 0 and yRef2Sel.selectionCount > 0:
            yRef1 = yRef1Sel.selection(0).entity
            yRef2 = yRef2Sel.selection(0).entity
            yOffset = inputs.itemById("yOffset").value
            
            desiredY = compute_center_between_refs(yRef1, yRef2, 1)
            if desiredY is not None:
                deltaY = (desiredY - targetCenter.y) + yOffset
            elif not preview:
                ui.messageBox("Could not compute Y center from references.", "Center Body - Warning")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Z AXIS
    # ─────────────────────────────────────────────────────────────────────────
    if centerZ:
        zRef1Sel = inputs.itemById("zRef1")
        zRef2Sel = inputs.itemById("zRef2")
        if zRef1Sel.selectionCount > 0 and zRef2Sel.selectionCount > 0:
            zRef1 = zRef1Sel.selection(0).entity
            zRef2 = zRef2Sel.selection(0).entity
            zOffset = inputs.itemById("zOffset").value
            
            desiredZ = compute_center_between_refs(zRef1, zRef2, 2)
            if desiredZ is not None:
                deltaZ = (desiredZ - targetCenter.z) + zOffset
            elif not preview:
                ui.messageBox("Could not compute Z center from references.", "Center Body - Warning")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CREATE TRANSLATION VECTOR AND MOVE
    # ─────────────────────────────────────────────────────────────────────────
    translationVector = adsk.core.Vector3D.create(deltaX, deltaY, deltaZ)
    
    if translationVector.length < 0.0001:
        if not preview:
            ui.messageBox("Target is already centered (or very close).", "Center Body - Info")
        return
    
    # Build descriptive feature name
    axisParts = []
    if centerX:
        axisParts.append("X")
    if centerY:
        axisParts.append("Y")
    if centerZ:
        axisParts.append("Z")
    axisStr = "+".join(axisParts)
    featureName = f"Center Body ({axisStr})"
    
    # Execute move
    if isBody:
        success = move_body_by_vector(targetEntity, translationVector, featureName)
    elif isOccurrence:
        success = move_occurrence_by_vector(targetEntity, translationVector)
    
    if not success and not preview:
        ui.messageBox("Failed to move target.", "Center Body - Error")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINTS
# ══════════════════════════════════════════════════════════════════════════════

def run(context):
    """Script entry point."""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmdDefs = ui.commandDefinitions
        
        existingDef = cmdDefs.itemById(COMMAND_ID)
        if existingDef:
            existingDef.deleteMe()
        
        cmdDef = cmdDefs.addButtonDefinition(
            COMMAND_ID,
            COMMAND_NAME,
            COMMAND_TOOLTIP,
            ""
        )
        
        onCommandCreated = CenterBodyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        cmdDef.execute()
        
        adsk.autoTerminate(False)
        
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'Failed to run:\n{traceback.format_exc()}')


def stop(context):
    """Clean up when script stops."""
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmdDef = ui.commandDefinitions.itemById(COMMAND_ID)
        if cmdDef:
            cmdDef.deleteMe()
            
    except:
        pass