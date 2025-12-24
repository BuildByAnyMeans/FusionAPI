import adsk.core, adsk.fusion, traceback
import os
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

# ══════════════════════════════════════════════════════════════════════════════
# COMMAND IDENTITY & LOCATION
# ══════════════════════════════════════════════════════════════════════════════
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_centerBody'
CMD_NAME = 'Center Body'
CMD_Description = 'Move a body so its center aligns between selected references.'

IS_PROMOTED = True

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidModifyPanel'
COMMAND_BESIDE_ID = ''

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

local_handlers = []

# Center method options
CENTER_BOUNDING_BOX = "Bounding Box Center"
CENTER_OF_MASS = "Center of Mass"

AXIS_NAMES = ["X", "Y", "Z"]


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_entity_position(entity) -> adsk.core.Point3D:
    """
    Get the position of an entity as a Point3D.
    Returns the plane origin for planar faces/planes, midpoint for edges, etc.
    """
    if isinstance(entity, adsk.fusion.BRepFace):
        geom = entity.geometry
        if isinstance(geom, adsk.core.Plane):
            return geom.origin
        else:
            bbox = entity.boundingBox
            if bbox:
                return adsk.core.Point3D.create(
                    (bbox.minPoint.x + bbox.maxPoint.x) / 2,
                    (bbox.minPoint.y + bbox.maxPoint.y) / 2,
                    (bbox.minPoint.z + bbox.maxPoint.z) / 2
                )
            return None
    
    elif isinstance(entity, adsk.fusion.ConstructionPlane):
        return entity.geometry.origin
    
    elif isinstance(entity, adsk.fusion.BRepEdge):
        start_pt = entity.startVertex.geometry if entity.startVertex else None
        end_pt = entity.endVertex.geometry if entity.endVertex else None
        if start_pt and end_pt:
            return adsk.core.Point3D.create(
                (start_pt.x + end_pt.x) / 2,
                (start_pt.y + end_pt.y) / 2,
                (start_pt.z + end_pt.z) / 2
            )
        return None
    
    elif isinstance(entity, adsk.fusion.SketchLine):
        start_pt = entity.startSketchPoint.geometry
        end_pt = entity.endSketchPoint.geometry
        sketch = entity.parentSketch
        transform = sketch.transform
        start_world = adsk.core.Point3D.create(start_pt.x, start_pt.y, 0)
        end_world = adsk.core.Point3D.create(end_pt.x, end_pt.y, 0)
        start_world.transformBy(transform)
        end_world.transformBy(transform)
        return adsk.core.Point3D.create(
            (start_world.x + end_world.x) / 2,
            (start_world.y + end_world.y) / 2,
            (start_world.z + end_world.z) / 2
        )
    
    elif isinstance(entity, adsk.fusion.ConstructionAxis):
        return entity.geometry.origin
    
    elif isinstance(entity, adsk.fusion.ConstructionPoint):
        return entity.geometry
    
    elif isinstance(entity, adsk.fusion.SketchPoint):
        sketch = entity.parentSketch
        transform = sketch.transform
        pt = entity.geometry
        world_pt = adsk.core.Point3D.create(pt.x, pt.y, 0)
        world_pt.transformBy(transform)
        return world_pt
    
    return None


def get_face_normal_axis(entity) -> int:
    """
    For a planar face or construction plane, determine which global axis 
    the normal is most aligned with.
    Returns: 0=X, 1=Y, 2=Z, or None if not determinable
    """
    normal = None
    
    if isinstance(entity, adsk.fusion.BRepFace):
        geom = entity.geometry
        if isinstance(geom, adsk.core.Plane):
            normal = geom.normal
    elif isinstance(entity, adsk.fusion.ConstructionPlane):
        normal = entity.geometry.normal
    
    if normal is None:
        return None
    
    # Find which axis the normal is most aligned with
    ax = abs(normal.x)
    ay = abs(normal.y)
    az = abs(normal.z)
    
    if ax >= ay and ax >= az:
        return 0  # Face is perpendicular to X axis
    elif ay >= ax and ay >= az:
        return 1  # Face is perpendicular to Y axis
    else:
        return 2  # Face is perpendicular to Z axis


def get_position_on_axis(entity, axis_index: int) -> float:
    """
    Get the position of an entity along a specific axis.
    For planar faces, projects a point onto that axis.
    """
    if isinstance(entity, adsk.fusion.BRepFace):
        geom = entity.geometry
        if isinstance(geom, adsk.core.Plane):
            # Use the plane's origin projected onto the axis
            origin = geom.origin
            return [origin.x, origin.y, origin.z][axis_index]
        else:
            bbox = entity.boundingBox
            if bbox:
                return (bbox.minPoint.asArray()[axis_index] + bbox.maxPoint.asArray()[axis_index]) / 2
            return None
    
    elif isinstance(entity, adsk.fusion.ConstructionPlane):
        origin = entity.geometry.origin
        return [origin.x, origin.y, origin.z][axis_index]
    
    # For other entity types, get position and extract axis coordinate
    pos = get_entity_position(entity)
    if pos:
        return [pos.x, pos.y, pos.z][axis_index]
    return None


def compute_center_and_axis(ref1, ref2) -> tuple:
    """
    Given two reference entities, compute the center point between them
    and auto-detect which axis they define.
    
    For planar faces: uses face normal to determine axis (most reliable)
    For other geometry: falls back to position difference
    
    Returns: (center_coordinate, axis_index) or (None, None) if failed
    """
    # Try to detect axis from face normals first (most reliable)
    axis1 = get_face_normal_axis(ref1)
    axis2 = get_face_normal_axis(ref2)
    
    # If both faces have normals and they agree, use that axis
    if axis1 is not None and axis2 is not None:
        if axis1 == axis2:
            axis_index = axis1
        else:
            # Faces point different directions - use the first one
            axis_index = axis1
    elif axis1 is not None:
        axis_index = axis1
    elif axis2 is not None:
        axis_index = axis2
    else:
        # Fallback: detect from position difference
        pos1 = get_entity_position(ref1)
        pos2 = get_entity_position(ref2)
        if pos1 is None or pos2 is None:
            return None, None
        
        dx = abs(pos2.x - pos1.x)
        dy = abs(pos2.y - pos1.y)
        dz = abs(pos2.z - pos1.z)
        
        if dx >= dy and dx >= dz:
            axis_index = 0
        elif dy >= dx and dy >= dz:
            axis_index = 1
        else:
            axis_index = 2
    
    # Get positions along the detected axis
    coord1 = get_position_on_axis(ref1, axis_index)
    coord2 = get_position_on_axis(ref2, axis_index)
    
    if coord1 is None or coord2 is None:
        return None, None
    
    center = (coord1 + coord2) / 2.0
    
    return center, axis_index


def get_body_bounding_box_center(body: adsk.fusion.BRepBody) -> adsk.core.Point3D:
    """Get the bounding box center of a body."""
    bbox = body.boundingBox
    if not bbox:
        return None
    return adsk.core.Point3D.create(
        (bbox.minPoint.x + bbox.maxPoint.x) / 2.0,
        (bbox.minPoint.y + bbox.maxPoint.y) / 2.0,
        (bbox.minPoint.z + bbox.maxPoint.z) / 2.0
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
    return adsk.core.Point3D.create(
        (bbox.minPoint.x + bbox.maxPoint.x) / 2.0,
        (bbox.minPoint.y + bbox.maxPoint.y) / 2.0,
        (bbox.minPoint.z + bbox.maxPoint.z) / 2.0
    )


def move_body_by_vector(body: adsk.fusion.BRepBody, vector: adsk.core.Vector3D, 
                        feature_name: str = "Center Body") -> bool:
    """Move a body using a Move feature."""
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


def update_reference_visibility(inputs: adsk.core.CommandInputs):
    """Update visibility of reference inputs based on checkboxes."""
    for i in range(1, 4):
        checkbox = inputs.itemById(f"enablePair{i}")
        refInput = inputs.itemById(f"refPair{i}")
        offsetInput = inputs.itemById(f"offset{i}")
        
        if checkbox and refInput and offsetInput:
            refInput.isVisible = checkbox.value
            offsetInput.isVisible = checkbox.value


def execute_centering(inputs: adsk.core.CommandInputs, preview: bool = False):
    """Core centering logic - compute translation and move target."""
    targetSelection = inputs.itemById("targetSelection")
    if targetSelection.selectionCount < 1:
        return
    targetEntity = targetSelection.selection(0).entity
    
    isBody = isinstance(targetEntity, adsk.fusion.BRepBody)
    isOccurrence = isinstance(targetEntity, adsk.fusion.Occurrence)
    
    centerMethodDropdown = inputs.itemById("centerMethod")
    centerMethod = centerMethodDropdown.selectedItem.name
    
    # Compute target center point
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
        targetCenter = get_occurrence_bounding_box_center(targetEntity)
        if centerMethod == CENTER_OF_MASS and not preview:
            ui.messageBox("Center of mass not supported for occurrences. Using bounding box.", 
                          "Center Body - Info")
    
    if not targetCenter:
        if not preview:
            ui.messageBox("Could not determine target center point.", "Center Body - Error")
        return
    
    # Track which axes we've centered on and their deltas
    deltas = [0.0, 0.0, 0.0]  # X, Y, Z
    axes_used = set()
    axis_labels = []
    
    # Process each reference pair
    for i in range(1, 4):
        checkbox = inputs.itemById(f"enablePair{i}")
        if not checkbox or not checkbox.value:
            continue
            
        refInput = inputs.itemById(f"refPair{i}")
        offsetInput = inputs.itemById(f"offset{i}")
        
        if refInput.selectionCount < 2:
            continue
        
        ref1 = refInput.selection(0).entity
        ref2 = refInput.selection(1).entity
        offset = offsetInput.value if offsetInput else 0.0
        
        # Auto-detect axis and compute center
        desiredCenter, axisIndex = compute_center_and_axis(ref1, ref2)
        
        if desiredCenter is None:
            if not preview:
                ui.messageBox(f"Could not compute center from Reference Pair {i}.", "Center Body - Warning")
            continue
        
        # Check for duplicate axis
        if axisIndex in axes_used:
            if not preview:
                ui.messageBox(f"Reference Pair {i} detected same axis ({AXIS_NAMES[axisIndex]}) as another pair. Skipping.", 
                              "Center Body - Warning")
            continue
        
        axes_used.add(axisIndex)
        axis_labels.append(AXIS_NAMES[axisIndex])
        
        # Compute delta for this axis
        targetCoords = [targetCenter.x, targetCenter.y, targetCenter.z]
        deltas[axisIndex] = (desiredCenter - targetCoords[axisIndex]) + offset
    
    # Create translation vector
    translationVector = adsk.core.Vector3D.create(deltas[0], deltas[1], deltas[2])
    
    if translationVector.length < 0.0001:
        if not preview:
            ui.messageBox("Target is already centered (or very close).", "Center Body - Info")
        return
    
    # Build feature name
    if axis_labels:
        featureName = f"Center Body ({'+'.join(axis_labels)})"
    else:
        featureName = "Center Body"
    
    # Execute move
    if isBody:
        success = move_body_by_vector(targetEntity, translationVector, featureName)
    elif isOccurrence:
        success = move_occurrence_by_vector(targetEntity, translationVector)
    
    if not success and not preview:
        ui.messageBox("Failed to move target.", "Center Body - Error")


# ══════════════════════════════════════════════════════════════════════════════
# ADD-IN LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════════

def start():
    """Executed when add-in is run."""
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    
    futil.add_handler(cmd_def.commandCreated, command_created)
    
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED


def stop():
    """Executed when add-in is stopped."""
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    
    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()


# ══════════════════════════════════════════════════════════════════════════════
# COMMAND EVENT HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

def command_created(args: adsk.core.CommandCreatedEventArgs):
    """Called when the command button is clicked. Defines the dialog UI."""
    futil.log(f'{CMD_NAME} Command Created Event')
    
    inputs = args.command.commandInputs
    
    # ─────────────────────────────────────────────────────────────────────────
    # TARGET SELECTION
    # ─────────────────────────────────────────────────────────────────────────
    targetSelection = inputs.addSelectionInput(
        "targetSelection", 
        "Target Body", 
        "Select the body or component to center"
    )
    targetSelection.addSelectionFilter("Bodies")
    targetSelection.addSelectionFilter("Occurrences")
    targetSelection.setSelectionLimits(1, 1)
    
    # ─────────────────────────────────────────────────────────────────────────
    # CENTER METHOD
    # ─────────────────────────────────────────────────────────────────────────
    centerMethodDropdown = inputs.addDropDownCommandInput(
        "centerMethod",
        "Center Method",
        adsk.core.DropDownStyles.TextListDropDownStyle
    )
    centerMethodDropdown.listItems.add(CENTER_BOUNDING_BOX, True)
    centerMethodDropdown.listItems.add(CENTER_OF_MASS, False)
    
    # ─────────────────────────────────────────────────────────────────────────
    # REFERENCE PAIR 1 (enabled by default)
    # ─────────────────────────────────────────────────────────────────────────
    inputs.addBoolValueInput("enablePair1", "Reference Pair 1", True, "", True)
    
    refPair1 = inputs.addSelectionInput("refPair1", "Select 2 Faces", "Select two opposing faces/planes")
    add_reference_selection_filters(refPair1)
    refPair1.setSelectionLimits(0, 2)
    
    inputs.addValueInput("offset1", "Offset 1", "mm", adsk.core.ValueInput.createByString("0 mm"))
    
    # ─────────────────────────────────────────────────────────────────────────
    # REFERENCE PAIR 2 (enabled by default)
    # ─────────────────────────────────────────────────────────────────────────
    inputs.addBoolValueInput("enablePair2", "Reference Pair 2", True, "", True)
    
    refPair2 = inputs.addSelectionInput("refPair2", "Select 2 Faces", "Select two opposing faces/planes")
    add_reference_selection_filters(refPair2)
    refPair2.setSelectionLimits(0, 2)
    
    inputs.addValueInput("offset2", "Offset 2", "mm", adsk.core.ValueInput.createByString("0 mm"))
    
    # ─────────────────────────────────────────────────────────────────────────
    # REFERENCE PAIR 3 (disabled by default)
    # ─────────────────────────────────────────────────────────────────────────
    inputs.addBoolValueInput("enablePair3", "Reference Pair 3", True, "", False)
    
    refPair3 = inputs.addSelectionInput("refPair3", "Select 2 Faces", "Select two opposing faces/planes")
    add_reference_selection_filters(refPair3)
    refPair3.setSelectionLimits(0, 2)
    refPair3.isVisible = False
    
    offset3 = inputs.addValueInput("offset3", "Offset 3", "mm", adsk.core.ValueInput.createByString("0 mm"))
    offset3.isVisible = False
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONNECT EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────────
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def command_execute(args: adsk.core.CommandEventArgs):
    """Called when the user clicks OK."""
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs
    execute_centering(inputs, preview=False)


def command_preview(args: adsk.core.CommandEventArgs):
    """Called to compute a preview in the graphics window."""
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs
    execute_centering(inputs, preview=True)


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    """Called when the user changes any input in the dialog."""
    changed_input = args.input
    inputs = args.inputs
    
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')
    
    # Toggle visibility when checkboxes change
    if changed_input.id in ["enablePair1", "enablePair2", "enablePair3"]:
        update_reference_visibility(inputs)


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    """Called to verify inputs are valid. Controls if OK button is enabled."""
    futil.log(f'{CMD_NAME} Validate Input Event')
    
    inputs = args.inputs
    
    # Check target selection
    targetSelection = inputs.itemById("targetSelection")
    if not targetSelection or targetSelection.selectionCount < 1:
        args.areInputsValid = False
        return
    
    # At least one reference pair must be enabled and have 2 selections
    hasValidPair = False
    
    for i in range(1, 4):
        checkbox = inputs.itemById(f"enablePair{i}")
        refInput = inputs.itemById(f"refPair{i}")
        
        if checkbox and checkbox.value:
            if refInput and refInput.selectionCount == 2:
                hasValidPair = True
            elif refInput and refInput.selectionCount > 0 and refInput.selectionCount < 2:
                # Partially filled - invalid
                args.areInputsValid = False
                return
    
    args.areInputsValid = hasValidPair


def command_destroy(args: adsk.core.CommandEventArgs):
    """Called when the command terminates."""
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers
    local_handlers = []