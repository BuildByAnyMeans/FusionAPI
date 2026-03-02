# commands/commandDialog/entry.py
# Heat Insert Hole Generator Command
# Author: Parker

import adsk.core
import adsk.fusion
import os
import traceback
import math

# Get the application and UI
app = adsk.core.Application.get()
ui = app.userInterface

# Command identity
CMD_ID = 'HeatInsertHoleGenerator'
CMD_NAME = 'Heat Insert Hole'
CMD_DESC = 'Generate optimized holes for heat-set threaded inserts'

# Panel and workspace targeting
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'

# Global handlers list
handlers = []
_command_def = None
_button_control = None

# Taper angles for heat insert holes (in degrees)
TAPER_ANGLE_STRAIGHT = 1.0
TAPER_ANGLE_TAPERED = 8.0
TAPER_TAN_STRAIGHT = math.tan(math.radians(TAPER_ANGLE_STRAIGHT))
TAPER_TAN_TAPERED = math.tan(math.radians(TAPER_ANGLE_TAPERED))

# Base extra depth - hole is always 1mm deeper than insert length
BASE_EXTRA_DEPTH_MM = 1.0  # mm - hardcoded here to avoid config cache issues

# Import config
from ... import config

# =============================================================================
# COMMAND LIFECYCLE
# =============================================================================

def start():
    """Initialize and register the command."""
    global _command_def, _button_control
    
    try:
        cmd_defs = ui.commandDefinitions
        
        existing = cmd_defs.itemById(CMD_ID)
        if existing:
            existing.deleteMe()
        
        resource_path = os.path.join(os.path.dirname(__file__), 'resources')
        
        _command_def = cmd_defs.addButtonDefinition(
            CMD_ID,
            CMD_NAME,
            CMD_DESC,
            resource_path
        )
        
        on_command_created = CommandCreatedHandler()
        _command_def.commandCreated.add(on_command_created)
        handlers.append(on_command_created)
        
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if workspace:
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            if panel:
                existing_control = panel.controls.itemById(CMD_ID)
                if existing_control:
                    existing_control.deleteMe()
                _button_control = panel.controls.addCommand(_command_def)
                _button_control.isPromoted = False
        
    except:
        ui.messageBox(f'Failed to start command:\n{traceback.format_exc()}')


def stop():
    """Clean up command on add-in stop."""
    global _command_def, _button_control
    
    try:
        if _button_control:
            _button_control.deleteMe()
            _button_control = None
            
        if _command_def:
            _command_def.deleteMe()
            _command_def = None
            
    except:
        ui.messageBox(f'Failed to stop command:\n{traceback.format_exc()}')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_point_from_selection(entity):
    """Extract a Point3D from various selection types."""
    try:
        if hasattr(entity, 'worldGeometry'):
            return entity.worldGeometry
        
        if hasattr(entity, 'geometry'):
            geom = entity.geometry
            if isinstance(geom, adsk.core.Point3D):
                return geom
            if hasattr(geom, 'center'):
                return geom.center
        
        if entity.objectType == adsk.fusion.BRepVertex.classType():
            return entity.geometry
            
    except:
        pass
    
    return None


def calc_tapered_diameter(top_dia, depth, taper_tan):
    """Calculate bottom diameter for a tapered hole."""
    diameter_reduction = 2 * depth * taper_tan
    bottom_dia = top_dia - diameter_reduction
    return max(bottom_dia, 0.01)


def get_melt_relief_specs(spec):
    """Get melt relief specs with guardrails applied."""
    oversize = min(spec['melt_relief_oversize'], config.MAX_MELT_RELIEF_OVERSIZE)
    depth = min(spec['melt_relief_depth'], config.MAX_MELT_RELIEF_DEPTH)
    return oversize, depth


# =============================================================================
# COMMAND CREATED HANDLER
# =============================================================================

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            
            cmd.isRepeatable = False
            cmd.okButtonText = 'Create Holes'
            cmd.isExecutedWhenPreEmpted = False
            
            # -----------------------------------------------------------------
            # SELECTION INPUTS
            # -----------------------------------------------------------------
            
            face_sel = inputs.addSelectionInput(
                'targetFace',
                'Target Face',
                'Select the face to place holes on'
            )
            face_sel.addSelectionFilter('PlanarFaces')
            face_sel.setSelectionLimits(1, 1)
            face_sel.tooltip = 'Select the planar face where holes will be cut'
            
            point_sel = inputs.addSelectionInput(
                'holePoints',
                'Hole Locations',
                'Select points for hole centers'
            )
            point_sel.addSelectionFilter('ConstructionPoints')
            point_sel.addSelectionFilter('SketchPoints')
            point_sel.addSelectionFilter('Vertices')
            point_sel.addSelectionFilter('CircularEdges')
            point_sel.setSelectionLimits(1, 0)
            point_sel.tooltip = 'Select points as hole centers'
            
            # -----------------------------------------------------------------
            # INSERT SPECIFICATION INPUTS
            # -----------------------------------------------------------------
            
            thread_input = inputs.addDropDownCommandInput(
                'threadSize',
                'Thread Size',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            for size in config.INSERT_SPECS.keys():
                is_default = (size == 'M3')
                thread_input.listItems.add(size, is_default)
            
            length_input = inputs.addDropDownCommandInput(
                'insertLength',
                'Insert Length',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            default_spec = config.INSERT_SPECS['M3']
            for i, opt_name in enumerate(default_spec['options'].keys()):
                length_input.listItems.add(opt_name, i == 0)
            
            # -----------------------------------------------------------------
            # HOLE STYLE OPTIONS
            # -----------------------------------------------------------------
            
            style_input = inputs.addDropDownCommandInput(
                'holeStyle',
                'Hole Style',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            style_input.listItems.add('Straight (1° taper)', True)
            style_input.listItems.add('Tapered (8°)', False)
            style_input.tooltip = 'Straight: 1° taper for knurled inserts | Tapered: 8° taper for tapered inserts'
            
            # -----------------------------------------------------------------
            # MELT RELIEF OPTION
            # -----------------------------------------------------------------
            
            melt_relief_input = inputs.addBoolValueInput(
                'meltRelief',
                'Melt Relief',
                True,
                '',
                config.DEFAULT_MELT_RELIEF
            )
            melt_relief_input.tooltip = 'Adds a shallow relief pocket at the hole entry to capture displaced plastic during heat-setting and keep the top surface cleaner.'
            
            # -----------------------------------------------------------------
            # ADJUSTMENT INPUTS
            # -----------------------------------------------------------------
            
            extra_depth_input = inputs.addValueInput(
                'extraDepth',
                'Extra Depth',
                'mm',
                adsk.core.ValueInput.createByReal(config.DEFAULT_EXTRA_DEPTH / 10)  # Default 0
            )
            extra_depth_input.tooltip = 'Additional depth beyond the built-in 1mm allowance'
            
            tolerance_input = inputs.addValueInput(
                'tolerance',
                'Diameter Adjustment',
                'mm',
                adsk.core.ValueInput.createByReal(config.DEFAULT_TOLERANCE / 10)
            )
            tolerance_input.tooltip = 'Adjust hole diameter (+ for looser, - for tighter)'
            
            # -----------------------------------------------------------------
            # INFO DISPLAY
            # -----------------------------------------------------------------
            
            info_text = inputs.addTextBoxCommandInput(
                'infoDisplay',
                'Hole Specs',
                get_info_text('M3', list(default_spec['options'].keys())[0], 'Straight (1° taper)', 
                             config.DEFAULT_MELT_RELIEF, 0, 0),
                6,
                True
            )
            
            # -----------------------------------------------------------------
            # EVENT HANDLERS
            # -----------------------------------------------------------------
            
            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)
            
            on_validate = ValidateInputsHandler()
            cmd.validateInputs.add(on_validate)
            handlers.append(on_validate)
            
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
            
            on_preview = CommandPreviewHandler()
            cmd.executePreview.add(on_preview)
            handlers.append(on_preview)
            
        except:
            ui.messageBox(f'Command created error:\n{traceback.format_exc()}')


def get_info_text(thread_size, insert_length, hole_style, melt_relief, extra_depth, tolerance):
    """Generate info text showing calculated dimensions."""
    spec = config.INSERT_SPECS.get(thread_size, {})
    if not spec:
        return 'Select options to see specifications'
    
    length_spec = spec['options'].get(insert_length, {})
    insert_len = length_spec.get('insert_length', 0)
    
    # Determine taper based on hole style
    if 'Tapered' in hole_style:
        taper_angle = TAPER_ANGLE_TAPERED
        taper_tan = TAPER_TAN_TAPERED
    else:
        taper_angle = TAPER_ANGLE_STRAIGHT
        taper_tan = TAPER_TAN_STRAIGHT
    
    top_dia = spec['hole_dia'] + (tolerance * 10)
    # Total depth = insert length + 1mm base + user extra depth
    total_depth = insert_len + BASE_EXTRA_DEPTH_MM + (extra_depth * 10)
    bottom_dia = top_dia - (2 * total_depth * taper_tan)
    
    chamfer_size = spec['chamfer_size']
    
    lines = [
        f"<b>Top Diameter:</b> {top_dia:.2f} mm",
        f"<b>Bottom Diameter:</b> {bottom_dia:.2f} mm",
        f"<b>Hole Depth:</b> {total_depth:.2f} mm (insert + 1mm + extra)",
        f"<b>Taper:</b> {taper_angle}°",
        f"<b>Chamfer:</b> {chamfer_size:.2f} mm @ 45°",
    ]
    
    if melt_relief:
        mr_oversize, mr_depth = get_melt_relief_specs(spec)
        mr_dia = top_dia + mr_oversize
        lines.append(f"<b>Melt Relief:</b> ⌀{mr_dia:.2f} × {mr_depth:.2f} mm")
    
    return '<br>'.join(lines)


# =============================================================================
# INPUT CHANGED HANDLER
# =============================================================================

class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.InputChangedEventArgs):
        try:
            inputs = args.inputs
            changed_input = args.input
            
            thread_input = inputs.itemById('threadSize')
            length_input = inputs.itemById('insertLength')
            style_input = inputs.itemById('holeStyle')
            melt_relief_input = inputs.itemById('meltRelief')
            extra_depth_input = inputs.itemById('extraDepth')
            tolerance_input = inputs.itemById('tolerance')
            info_display = inputs.itemById('infoDisplay')
            
            if changed_input.id == 'threadSize':
                thread_size = thread_input.selectedItem.name
                spec = config.INSERT_SPECS.get(thread_size, {})
                
                length_input.listItems.clear()
                for i, opt_name in enumerate(spec.get('options', {}).keys()):
                    length_input.listItems.add(opt_name, i == 0)
            
            if changed_input.id in ['threadSize', 'insertLength', 'holeStyle', 'meltRelief', 'extraDepth', 'tolerance']:
                thread_size = thread_input.selectedItem.name
                insert_length = length_input.selectedItem.name if length_input.selectedItem else ''
                hole_style = style_input.selectedItem.name if style_input.selectedItem else 'Straight (1° taper)'
                melt_relief = melt_relief_input.value
                extra_depth = extra_depth_input.value
                tolerance = tolerance_input.value
                
                info_display.text = get_info_text(
                    thread_size, insert_length, hole_style, melt_relief, extra_depth, tolerance
                )
                
        except:
            ui.messageBox(f'Input changed error:\n{traceback.format_exc()}')


# =============================================================================
# VALIDATE INPUTS HANDLER
# =============================================================================

class ValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.ValidateInputsEventArgs):
        try:
            inputs = args.inputs
            
            face_sel = inputs.itemById('targetFace')
            if face_sel.selectionCount < 1:
                args.areInputsValid = False
                return
            
            point_sel = inputs.itemById('holePoints')
            if point_sel.selectionCount < 1:
                args.areInputsValid = False
                return
            
            args.areInputsValid = True
            
        except:
            args.areInputsValid = False


# =============================================================================
# COMMAND PREVIEW HANDLER
# =============================================================================

class CommandPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            create_heat_insert_holes(args, is_preview=True)
            args.isValidResult = True
        except:
            args.isValidResult = False


# =============================================================================
# COMMAND EXECUTE HANDLER
# =============================================================================

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args: adsk.core.CommandEventArgs):
        try:
            create_heat_insert_holes(args, is_preview=False)
        except:
            ui.messageBox(f'Execution error:\n{traceback.format_exc()}')


# =============================================================================
# MAIN HOLE CREATION LOGIC
# =============================================================================

def create_heat_insert_holes(args, is_preview=False):
    """Create heat insert holes at selected points using loft cuts."""
    
    cmd = args.firingEvent.sender
    inputs = cmd.commandInputs
    
    # Get inputs
    face = inputs.itemById('targetFace').selection(0).entity
    body = face.body
    point_sel = inputs.itemById('holePoints')
    thread_size = inputs.itemById('threadSize').selectedItem.name
    insert_length = inputs.itemById('insertLength').selectedItem.name
    hole_style = inputs.itemById('holeStyle').selectedItem.name
    melt_relief_enabled = inputs.itemById('meltRelief').value
    extra_depth = inputs.itemById('extraDepth').value * 10  # cm to mm
    tolerance = inputs.itemById('tolerance').value * 10  # cm to mm
    
    # Determine taper based on hole style
    if 'Tapered' in hole_style:
        taper_tan = TAPER_TAN_TAPERED
    else:
        taper_tan = TAPER_TAN_STRAIGHT
    
    # Get spec
    spec = config.INSERT_SPECS[thread_size]
    length_spec = spec['options'][insert_length]
    
    # Calculate dimensions (in cm for Fusion API)
    hole_dia = (spec['hole_dia'] + tolerance) / 10
    # Hole depth = insert length + 1mm base + user extra depth
    hole_depth = (length_spec['insert_length'] + BASE_EXTRA_DEPTH_MM + extra_depth) / 10
    chamfer_size = spec['chamfer_size'] / 10
    
    # Melt relief dimensions (with guardrails)
    mr_oversize, mr_depth = get_melt_relief_specs(spec)
    mr_oversize = mr_oversize / 10  # Convert to cm
    mr_depth = mr_depth / 10
    
    # Get design and component
    design = adsk.fusion.Design.cast(app.activeProduct)
    comp = face.body.parentComponent
    if comp is None:
        comp = design.rootComponent
    
    # Collect all selected points
    points = []
    for i in range(point_sel.selectionCount):
        entity = point_sel.selection(i).entity
        pt = get_point_from_selection(entity)
        if pt:
            points.append(pt)
    
    if not points:
        if not is_preview:
            ui.messageBox('No valid points selected.')
        return
    
    # Get face normal
    face_eval = face.evaluator
    result, normal = face_eval.getNormalAtPoint(face.pointOnFace)
    if not result:
        if face.geometry.objectType == adsk.core.Plane.classType():
            normal = face.geometry.normal
        else:
            if not is_preview:
                ui.messageBox('Could not determine face normal.')
            return
    
    cut_direction = adsk.core.Vector3D.create(-normal.x, -normal.y, -normal.z)
    
    # Calculate melt relief diameter (based on the hole's top diameter)
    melt_relief_dia = hole_dia + mr_oversize
    
    # Create holes at each point
    for idx, point in enumerate(points):
        
        if melt_relief_enabled:
            # MELT RELIEF ON:
            # 1. Create melt relief counterbore first (wider pocket)
            # 2. Chamfer the counterbore top edge
            # 3. Create tapered hole inside
            
            # Step 1: Melt relief counterbore
            mr_feature = create_melt_relief(
                comp, body, face, point, idx,
                melt_relief_dia, mr_depth,
                thread_size
            )
            
            # Step 2: Chamfer the melt relief top edge
            # Cap chamfer size to 60% of melt relief depth so it fits
            mr_chamfer_size = min(chamfer_size, mr_depth * 0.6)
            chamfer_melt_relief_edge(
                comp, mr_feature, face, mr_chamfer_size,
                thread_size, idx
            )
            
            # Step 3: Create tapered hole inside
            create_tapered_hole(
                comp, body, face, point, cut_direction, idx,
                hole_dia, hole_depth, taper_tan,
                thread_size
            )
        else:
            # MELT RELIEF OFF:
            # 1. Create tapered hole
            # 2. Chamfer the hole top edge
            
            # Step 1: Create tapered hole
            create_tapered_hole(
                comp, body, face, point, cut_direction, idx,
                hole_dia, hole_depth, taper_tan,
                thread_size
            )
            
            # Step 2: Chamfer the hole top edge
            apply_top_chamfer(
                comp, body, face, point, idx,
                hole_dia, chamfer_size,
                thread_size
            )
    
    # Show summary
    if not is_preview:
        hole_count = len(points)
        taper_desc = "8°" if 'Tapered' in hole_style else "1°"
        ui.messageBox(
            f'Created {hole_count} heat insert hole{"s" if hole_count > 1 else ""}\n'
            f'Thread: {thread_size} | Insert: {insert_length}\n'
            f'Taper: {taper_desc} | Melt Relief: {"Yes" if melt_relief_enabled else "No"}',
            'Heat Insert Holes Created'
        )


def create_tapered_hole(comp, body, face, point, cut_direction, index,
                        top_dia, depth, taper_tan, thread_size):
    """Create a single tapered hole using loft cut."""
    
    sketches = comp.sketches
    planes = comp.constructionPlanes
    lofts = comp.features.loftFeatures
    
    bottom_dia = calc_tapered_diameter(top_dia, depth, taper_tan)
    
    # Create top plane at face level using XY plane as reference
    top_plane_input = planes.createInput()
    top_plane_input.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(point.z))
    top_plane = planes.add(top_plane_input)
    top_plane.name = f'HeatInsert_{thread_size}_TopPlane_{index + 1}'
    top_plane.isLightBulbOn = False
    
    # Top sketch on construction plane
    top_sketch = sketches.add(top_plane)
    top_sketch.name = f'HeatInsert_{thread_size}_Top_{index + 1}'
    
    top_center = top_sketch.modelToSketchSpace(point)
    top_sketch.sketchCurves.sketchCircles.addByCenterRadius(top_center, top_dia / 2)
    
    top_profile = get_circle_profile(top_sketch, top_dia)
    
    # Bottom plane offset from top plane
    bottom_plane_input = planes.createInput()
    bottom_plane_input.setByOffset(top_plane, adsk.core.ValueInput.createByReal(-depth))
    bottom_plane = planes.add(bottom_plane_input)
    bottom_plane.name = f'HeatInsert_{thread_size}_BottomPlane_{index + 1}'
    bottom_plane.isLightBulbOn = False
    
    # Bottom sketch
    bottom_sketch = sketches.add(bottom_plane)
    bottom_sketch.name = f'HeatInsert_{thread_size}_Bottom_{index + 1}'
    
    bottom_point = adsk.core.Point3D.create(
        point.x + cut_direction.x * depth,
        point.y + cut_direction.y * depth,
        point.z + cut_direction.z * depth
    )
    
    bottom_center = bottom_sketch.modelToSketchSpace(bottom_point)
    bottom_sketch.sketchCurves.sketchCircles.addByCenterRadius(bottom_center, bottom_dia / 2)
    
    bottom_profile = bottom_sketch.profiles.item(0)
    
    # Loft cut
    loft_input = lofts.createInput(adsk.fusion.FeatureOperations.CutFeatureOperation)
    loft_input.loftSections.add(top_profile)
    loft_input.loftSections.add(bottom_profile)
    loft_input.isSolid = True
    loft_input.participantBodies = [body]
    
    loft_feature = lofts.add(loft_input)
    loft_feature.name = f'HeatInsert_{thread_size}_Hole_{index + 1}'


def create_melt_relief(comp, body, face, point, index, diameter, depth, thread_size):
    """Create a melt relief counterbore at the top of the hole.
    
    Returns the extrude feature so we can chamfer its edges.
    """
    
    sketches = comp.sketches
    extrudes = comp.features.extrudeFeatures
    
    # Create sketch on face
    mr_sketch = sketches.add(face)
    mr_sketch.name = f'HeatInsert_{thread_size}_MeltRelief_Sketch_{index + 1}'
    
    center = mr_sketch.modelToSketchSpace(point)
    mr_sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter / 2)
    
    # Get the circle profile
    mr_profile = get_circle_profile(mr_sketch, diameter)
    
    # Extrude cut
    extrude_input = extrudes.createInput(mr_profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(depth))
    extrude_input.setOneSideExtent(extent, adsk.fusion.ExtentDirections.NegativeExtentDirection)
    extrude_input.participantBodies = [body]
    
    extrude_feature = extrudes.add(extrude_input)
    extrude_feature.name = f'HeatInsert_{thread_size}_MeltRelief_{index + 1}'
    
    return extrude_feature


def chamfer_melt_relief_edge(comp, mr_feature, face, chamfer_size, thread_size, index):
    """Chamfer the top edge of a melt relief pocket using the extrude feature's edges."""
    
    chamfers = comp.features.chamferFeatures
    
    # Get the Z level of the original face (top surface)
    face_z = face.pointOnFace.z
    
    # The extrude feature has side faces (cylindrical wall)
    # The top edge of that wall is what we want to chamfer
    side_faces = mr_feature.sideFaces
    
    if side_faces.count == 0:
        return
    
    best_edge = None
    best_z_diff = float('inf')
    
    # Look through all edges of all side faces
    for i in range(side_faces.count):
        side_face = side_faces.item(i)
        
        for edge in side_face.edges:
            geom = edge.geometry
            
            # We want circular edges
            if not hasattr(geom, 'center'):
                continue
            
            # Find the edge closest to the original face level (the top edge)
            edge_z = geom.center.z
            z_diff = abs(edge_z - face_z)
            
            if z_diff < best_z_diff:
                best_z_diff = z_diff
                best_edge = edge
    
    if best_edge is None:
        return
    
    try:
        edge_collection = adsk.core.ObjectCollection.create()
        edge_collection.add(best_edge)
        
        chamfer_input = chamfers.createInput2()
        chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edge_collection,
            adsk.core.ValueInput.createByReal(chamfer_size),
            False  # Disable tangent chain
        )
        
        chamfer_feature = chamfers.add(chamfer_input)
        chamfer_feature.name = f'HeatInsert_{thread_size}_Chamfer_{index + 1}'
        
    except:
        pass


def apply_top_chamfer(comp, body, face, point, index, hole_diameter, chamfer_size, thread_size):
    """Apply a chamfer to the top edge of the hole."""
    
    chamfers = comp.features.chamferFeatures
    
    # Find the circular edge at the top of the hole
    target_radius = hole_diameter / 2
    tolerance = 0.1  # 1mm tolerance for matching radius and position
    
    face_point = face.pointOnFace
    
    best_edge = None
    best_distance = float('inf')
    
    for edge in body.edges:
        geom = edge.geometry
        if not hasattr(geom, 'radius'):
            continue
        
        radius_diff = abs(geom.radius - target_radius)
        if radius_diff > tolerance:
            continue
        
        if hasattr(geom, 'center'):
            edge_center = geom.center
            xy_dist = math.sqrt((edge_center.x - point.x)**2 + (edge_center.y - point.y)**2)
            
            if xy_dist < tolerance:
                z_diff = abs(edge_center.z - face_point.z)
                
                if z_diff < best_distance:
                    best_distance = z_diff
                    best_edge = edge
    
    if best_edge is None:
        for edge in body.edges:
            geom = edge.geometry
            if not hasattr(geom, 'radius'):
                continue
            
            if hasattr(geom, 'center'):
                edge_center = geom.center
                xy_dist = math.sqrt((edge_center.x - point.x)**2 + (edge_center.y - point.y)**2)
                
                if xy_dist < 0.15:  # 1.5mm tolerance
                    radius_diff = abs(geom.radius - target_radius)
                    if radius_diff < 0.15:  # 1.5mm tolerance
                        z_diff = abs(edge_center.z - face_point.z)
                        if z_diff < best_distance:
                            best_distance = z_diff
                            best_edge = edge
    
    if best_edge is None:
        return
    
    try:
        edge_collection = adsk.core.ObjectCollection.create()
        edge_collection.add(best_edge)
        
        chamfer_input = chamfers.createInput2()
        chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edge_collection,
            adsk.core.ValueInput.createByReal(chamfer_size),
            True
        )
        
        chamfer_feature = chamfers.add(chamfer_input)
        chamfer_feature.name = f'HeatInsert_{thread_size}_Chamfer_{index + 1}'
        
    except Exception as e:
        pass


def get_circle_profile(sketch, expected_dia):
    """Get the profile that matches the expected circle diameter."""
    expected_area = math.pi * (expected_dia / 2) ** 2
    
    best_profile = None
    best_diff = float('inf')
    
    for i in range(sketch.profiles.count):
        prof = sketch.profiles.item(i)
        area = abs(prof.areaProperties().area)
        diff = abs(area - expected_area)
        
        if diff < best_diff:
            best_diff = diff
            best_profile = prof
    
    if best_profile is None or best_diff > expected_area * 0.5:
        smallest_area = float('inf')
        for i in range(sketch.profiles.count):
            prof = sketch.profiles.item(i)
            area = abs(prof.areaProperties().area)
            if area < smallest_area:
                smallest_area = area
                best_profile = prof
    
    return best_profile