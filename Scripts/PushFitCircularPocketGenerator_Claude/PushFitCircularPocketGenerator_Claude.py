#Author: Claude (Anthropic)
#Description: Push-Fit Circular Pocket Generator - Creates circular pockets with alignment slots
#             for push-fit applications like magnets, rods, or Qi chargers.

# =============================================================================
# SECTION 1: IMPORTS
# =============================================================================
import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# =============================================================================
# SECTION 2: GLOBAL VARIABLES
# =============================================================================
_app = None
_ui = None
_handlers = []

_commandId = 'PushFitCircularPocketGenerator_Claude'
_commandName = 'Push-Fit Circular Pocket Generator'
_commandDescription = 'Creates a circular pocket with alignment slot for push-fit applications'

# =============================================================================
# SECTION 3: MATERIAL TOLERANCE DEFINITIONS
# =============================================================================
MATERIAL_TOLERANCES = {
    'PLA': {
        'Tight': 0.05,
        'Standard': 0.125,
        'Loose': 0.2
    }
}

# =============================================================================
# SECTION 4: DEPTH OFFSET DEFINITIONS  
# =============================================================================
DEPTH_OFFSETS = {
    'Proud': 0.0,
    'Flush': 0.25,
    'Deep': 0.5
}

# =============================================================================
# SECTION 5: COMMAND CREATED HANDLER
# =============================================================================
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)
            
            onDestroy = CommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)
            
            inputs = cmd.commandInputs
            
            # Target Face
            faceSelection = inputs.addSelectionInput(
                'faceSelection',
                'Target Face',
                'Select the face to cut the pocket into'
            )
            faceSelection.addSelectionFilter('PlanarFaces')
            faceSelection.setSelectionLimits(1, 1)
            
            # Center Point
            pointSelection = inputs.addSelectionInput(
                'pointSelection',
                'Center Point',
                'Select a sketch point for pocket center'
            )
            pointSelection.addSelectionFilter('SketchPoints')
            pointSelection.addSelectionFilter('Vertices')
            pointSelection.addSelectionFilter('ConstructionPoints')
            pointSelection.setSelectionLimits(1, 1)
            
            # Alignment Line(s) - can select multiple for multiple slots
            lineSelection = inputs.addSelectionInput(
                'lineSelection',
                'Alignment Line(s)', 
                'Select one or more lines for slot alignment (each line creates a slot)'
            )
            lineSelection.addSelectionFilter('SketchLines')
            lineSelection.addSelectionFilter('LinearEdges')
            lineSelection.setSelectionLimits(1, 0)  # Minimum 1, no maximum (0 = unlimited)
            
            # Disk Diameter
            inputs.addValueInput(
                'diskDiameter',
                'Disk Diameter',
                'mm',
                adsk.core.ValueInput.createByReal(0.6)
            )
            
            # Disk Thickness
            inputs.addValueInput(
                'diskThickness',
                'Disk Thickness',
                'mm',
                adsk.core.ValueInput.createByReal(0.2)
            )
            
            # Material
            materialDropdown = inputs.addDropDownCommandInput(
                'material',
                'Material',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            materialDropdown.listItems.add('PLA', True)
            
            # Fit
            fitDropdown = inputs.addDropDownCommandInput(
                'fit',
                'Fit',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            fitDropdown.listItems.add('Tight', False)      # +0.05mm
            fitDropdown.listItems.add('Standard', True)    # +0.125mm
            fitDropdown.listItems.add('Loose', False)      # +0.2mm
            fitDropdown.listItems.add('Custom', False)     # User-defined
            
            # Custom Fit Offset (only shown when Fit = Custom)
            customFitInput = inputs.addValueInput(
                'customFitOffset',
                'Custom Fit Offset',
                'mm',
                adsk.core.ValueInput.createByReal(0.0)  # 0.0mm default
            )
            customFitInput.isEnabled = False  # Start disabled
            
            # Set Depth
            depthDropdown = inputs.addDropDownCommandInput(
                'setDepth',
                'Set Depth',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            depthDropdown.listItems.add('Proud', False)    # +0.0mm
            depthDropdown.listItems.add('Flush', True)     # +0.25mm
            depthDropdown.listItems.add('Deep', False)     # +0.5mm
            depthDropdown.listItems.add('Custom', False)   # User-defined
            
            # Custom Depth Offset (only shown when Set Depth = Custom)
            customDepthInput = inputs.addValueInput(
                'customDepthOffset',
                'Custom Depth Offset',
                'mm',
                adsk.core.ValueInput.createByReal(0.0)  # 0.0mm default
            )
            customDepthInput.isEnabled = False  # Start disabled
            
            # -----------------------------------------------------------------
            # Checkbox: Add Fillet
            # -----------------------------------------------------------------
            # Optional fillet on the pocket edge (top edge where it meets the face)
            filletCheckbox = inputs.addBoolValueInput(
                'addFillet',
                'Add Edge Fillet',
                True,
                '',
                False  # Default unchecked
            )
            
            # -----------------------------------------------------------------
            # Value Input: Fillet Radius
            # -----------------------------------------------------------------
            # Size of the fillet - only enabled when checkbox is checked
            filletRadiusInput = inputs.addValueInput(
                'filletRadius',
                'Fillet Radius',
                'mm',
                adsk.core.ValueInput.createByReal(0.05)  # 0.5mm default
            )
            filletRadiusInput.isEnabled = False  # Start disabled
            
            # -----------------------------------------------------------------
            # Checkbox: Multi-Pocket Cut
            # -----------------------------------------------------------------
            # Option to cut multiple pockets with the same settings at different centers
            multiPocketCheckbox = inputs.addBoolValueInput(
                'multiPockets',
                'Multi-Pocket Cut',
                True,
                '',
                False  # Default unchecked
            )
            
            # -----------------------------------------------------------------
            # Selection Input: Additional Center Points
            # -----------------------------------------------------------------
            # Extra center points for additional pockets (same settings as primary)
            extraPointsSelection = inputs.addSelectionInput(
                'extraPoints',
                'Additional Center Points',
                'Select additional center points for more pockets with same settings'
            )
            extraPointsSelection.addSelectionFilter('SketchPoints')
            extraPointsSelection.addSelectionFilter('Vertices')
            extraPointsSelection.addSelectionFilter('ConstructionPoints')
            extraPointsSelection.setSelectionLimits(0, 0)  # Min 0, unlimited max
            extraPointsSelection.isEnabled = False  # Start disabled
            
            # -----------------------------------------------------------------
            # Connect input changed handler for checkbox toggles
            # -----------------------------------------------------------------
            onInputChanged = CommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)
            
        except:
            if _ui:
                _ui.messageBox('Failed to create command:\n{}'.format(traceback.format_exc()))

# =============================================================================
# SECTION 5B: INPUT CHANGED HANDLER
# =============================================================================
# This handler responds when UI inputs change, specifically to enable/disable
# conditional inputs based on checkbox and dropdown states.

class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            changedInput = args.input
            inputs = args.inputs
            
            # When the fillet checkbox changes, enable/disable the radius input
            if changedInput.id == 'addFillet':
                filletCheckbox = adsk.core.BoolValueCommandInput.cast(changedInput)
                filletRadiusInput = inputs.itemById('filletRadius')
                filletRadiusInput.isEnabled = filletCheckbox.value
            
            # When the multi-pocket checkbox changes, enable/disable extra points
            if changedInput.id == 'multiPockets':
                multiCheckbox = adsk.core.BoolValueCommandInput.cast(changedInput)
                extraPointsInput = inputs.itemById('extraPoints')
                extraPointsInput.isEnabled = multiCheckbox.value
            
            # When Fit dropdown changes, enable/disable custom fit input
            if changedInput.id == 'fit':
                fitDropdown = adsk.core.DropDownCommandInput.cast(changedInput)
                customFitInput = inputs.itemById('customFitOffset')
                customFitInput.isEnabled = (fitDropdown.selectedItem.name == 'Custom')
            
            # When Set Depth dropdown changes, enable/disable custom depth input
            if changedInput.id == 'setDepth':
                depthDropdown = adsk.core.DropDownCommandInput.cast(changedInput)
                customDepthInput = inputs.itemById('customDepthOffset')
                customDepthInput.isEnabled = (depthDropdown.selectedItem.name == 'Custom')
                
        except:
            if _ui:
                _ui.messageBox('Failed in input changed:\n{}'.format(traceback.format_exc()))

# =============================================================================
# SECTION 6: COMMAND EXECUTE HANDLER
# =============================================================================
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            
            # -----------------------------------------------------------------
            # SECTION 6A: READ USER INPUTS
            # -----------------------------------------------------------------
            faceSelectionInput = inputs.itemById('faceSelection')
            targetFace = adsk.fusion.BRepFace.cast(faceSelectionInput.selection(0).entity)
            comp = targetFace.body.parentComponent
            
            # Primary center point
            pointSelectionInput = inputs.itemById('pointSelection')
            primaryCenterEntity = pointSelectionInput.selection(0).entity
            
            # Collect ALL selected alignment lines
            lineSelectionInput = inputs.itemById('lineSelection')
            alignmentEntities = []
            for i in range(lineSelectionInput.selectionCount):
                alignmentEntities.append(lineSelectionInput.selection(i).entity)
            
            numSlots = len(alignmentEntities)
            
            diskDiameter = inputs.itemById('diskDiameter').value
            diskThickness = inputs.itemById('diskThickness').value
            
            material = inputs.itemById('material').selectedItem.name
            fit = inputs.itemById('fit').selectedItem.name
            setDepth = inputs.itemById('setDepth').selectedItem.name
            
            # Custom fit offset (used when fit = Custom)
            customFitOffset = inputs.itemById('customFitOffset').value  # Already in cm
            
            # Custom depth offset (used when setDepth = Custom)
            customDepthOffset = inputs.itemById('customDepthOffset').value  # Already in cm
            
            # Fillet options
            addFillet = inputs.itemById('addFillet').value
            filletRadius = inputs.itemById('filletRadius').value if addFillet else 0
            
            # Multi-pocket options
            multiPockets = inputs.itemById('multiPockets').value
            extraPointsInput = inputs.itemById('extraPoints')
            
            # Build list of all center points (primary + extras)
            allCenterEntities = [primaryCenterEntity]
            if multiPockets:
                for i in range(extraPointsInput.selectionCount):
                    allCenterEntities.append(extraPointsInput.selection(i).entity)
            
            numPockets = len(allCenterEntities)
            
            # -----------------------------------------------------------------
            # SECTION 6B: CALCULATE DIMENSIONS
            # -----------------------------------------------------------------
            # Get tolerance based on fit selection
            if fit == 'Custom':
                tolerance = customFitOffset  # Already in cm from UI
            else:
                tolerance = MATERIAL_TOLERANCES[material][fit] / 10.0  # Convert mm to cm
            
            # Get depth offset based on set depth selection
            if setDepth == 'Custom':
                depthOffset = customDepthOffset  # Already in cm from UI
            else:
                depthOffset = DEPTH_OFFSETS[setDepth] / 10.0  # Convert mm to cm
            
            pocketDiameter = diskDiameter + tolerance
            pocketRadius = pocketDiameter / 2.0
            
            # Slot dimensions based on DISK diameter
            slotWidth = diskDiameter * 0.10
            slotHalfWidth = slotWidth / 2.0
            slotCenterToCenter = diskDiameter * 1.25
            slotHalfSpacing = slotCenterToCenter / 2.0
            
            # Extrusion depth (negative = into face)
            pocketDepth = diskThickness + depthOffset
            
            # -----------------------------------------------------------------
            # SECTION 6C: CREATE SKETCH ON TARGET FACE
            # -----------------------------------------------------------------
            sketches = comp.sketches
            sketch = sketches.add(targetFace)
            sketch.name = "PushFit Pocket Sketch"
            
            # -----------------------------------------------------------------
            # SECTION 6D: PROJECT ALL CENTER POINTS INTO SKETCH
            # -----------------------------------------------------------------
            projectedCenterPoints = []
            for centerEntity in allCenterEntities:
                projCenter = sketch.project(centerEntity)
                centerPointSketch = None
                for e in projCenter:
                    centerPointSketch = adsk.fusion.SketchPoint.cast(e)
                    if centerPointSketch:
                        break
                
                if centerPointSketch:
                    projectedCenterPoints.append(centerPointSketch)
                else:
                    _ui.messageBox('Could not project one of the Center Points into the sketch.')
                    return
            
            # -----------------------------------------------------------------
            # SECTION 6E: PROJECT ALL ALIGNMENT LINES INTO SKETCH
            # -----------------------------------------------------------------
            # Project each alignment line and store the projected sketch lines
            projectedAlignLines = []
            for alignEntity in alignmentEntities:
                projLine = sketch.project(alignEntity)
                alignLineSketch = None
                for e in projLine:
                    alignLineSketch = adsk.fusion.SketchLine.cast(e)
                    if alignLineSketch:
                        break
                
                if alignLineSketch:
                    projectedAlignLines.append(alignLineSketch)
                else:
                    _ui.messageBox('Could not project one of the Alignment Lines into the sketch.')
                    return
            
            # -----------------------------------------------------------------
            # SECTION 6F: PRE-CALCULATE ALIGNMENT DIRECTIONS
            # -----------------------------------------------------------------
            # Calculate normalized direction vectors for all alignment lines once
            # (these are reused for each pocket)
            alignmentDirections = []
            for alignLineSketch in projectedAlignLines:
                startGeo = alignLineSketch.startSketchPoint.geometry
                endGeo = alignLineSketch.endSketchPoint.geometry
                dx = endGeo.x - startGeo.x
                dy = endGeo.y - startGeo.y
                
                # Normalize direction
                length = math.sqrt(dx * dx + dy * dy)
                if length < 1e-6:
                    continue  # Skip zero-length lines
                ux = dx / length
                uy = dy / length
                
                # Store direction and perpendicular
                alignmentDirections.append({
                    'ux': ux, 'uy': uy,
                    'px': -uy, 'py': ux  # Perpendicular
                })
            
            # -----------------------------------------------------------------
            # SECTION 6G: DRAW ALL POCKETS
            # -----------------------------------------------------------------
            sketch.isComputeDeferred = True
            
            circles = sketch.sketchCurves.sketchCircles
            lines = sketch.sketchCurves.sketchLines
            
            # Loop through each center point and create a pocket
            for centerPointSketch in projectedCenterPoints:
                centerGeo = centerPointSketch.geometry
                cx = centerGeo.x
                cy = centerGeo.y
                
                # Main circular pocket for this center
                centerPt = adsk.core.Point3D.create(cx, cy, 0)
                circles.addByCenterRadius(centerPt, pocketRadius)
                
                # Draw slots for each alignment direction at this center
                for direction in alignmentDirections:
                    ux = direction['ux']
                    uy = direction['uy']
                    px = direction['px']
                    py = direction['py']
                    
                    # Slot end centers (along this alignment direction)
                    topCx = cx + ux * slotHalfSpacing
                    topCy = cy + uy * slotHalfSpacing
                    botCx = cx - ux * slotHalfSpacing
                    botCy = cy - uy * slotHalfSpacing
                    
                    # Slot end circles
                    topCenterPt = adsk.core.Point3D.create(topCx, topCy, 0)
                    botCenterPt = adsk.core.Point3D.create(botCx, botCy, 0)
                    circles.addByCenterRadius(topCenterPt, slotHalfWidth)
                    circles.addByCenterRadius(botCenterPt, slotHalfWidth)
                    
                    # Slot tangent lines (connecting the circles)
                    topLeftX = topCx + px * slotHalfWidth
                    topLeftY = topCy + py * slotHalfWidth
                    topRightX = topCx - px * slotHalfWidth
                    topRightY = topCy - py * slotHalfWidth
                    botLeftX = botCx + px * slotHalfWidth
                    botLeftY = botCy + py * slotHalfWidth
                    botRightX = botCx - px * slotHalfWidth
                    botRightY = botCy - py * slotHalfWidth
                    
                    topLeftPt = adsk.core.Point3D.create(topLeftX, topLeftY, 0)
                    topRightPt = adsk.core.Point3D.create(topRightX, topRightY, 0)
                    botLeftPt = adsk.core.Point3D.create(botLeftX, botLeftY, 0)
                    botRightPt = adsk.core.Point3D.create(botRightX, botRightY, 0)
                    
                    lines.addByTwoPoints(topLeftPt, botLeftPt)
                    lines.addByTwoPoints(topRightPt, botRightPt)
            
            sketch.isComputeDeferred = False
            
            # -----------------------------------------------------------------
            # SECTION 6H: SELECT PROFILES FOR EXTRUSION
            # -----------------------------------------------------------------
            allProfiles = list(sketch.profiles)
            profilesToExtrude = adsk.core.ObjectCollection.create()
            
            maxSize = pocketDiameter * 3.0
            
            for profile in allProfiles:
                bbox = profile.boundingBox
                width = abs(bbox.maxPoint.x - bbox.minPoint.x)
                height = abs(bbox.maxPoint.y - bbox.minPoint.y)
                if width <= maxSize and height <= maxSize:
                    profilesToExtrude.add(profile)
            
            if profilesToExtrude.count == 0:
                for profile in allProfiles:
                    profilesToExtrude.add(profile)
            
            # -----------------------------------------------------------------
            # SECTION 6I: CREATE THE EXTRUSION (CUT)
            # -----------------------------------------------------------------
            extrudes = comp.features.extrudeFeatures
            
            extrudeInput = extrudes.createInput(
                profilesToExtrude, 
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )
            
            # One-sided cut with negative depth
            depthVal = adsk.core.ValueInput.createByReal(-pocketDepth)
            extrudeInput.setDistanceExtent(False, depthVal)
            
            extrude = extrudes.add(extrudeInput)
            extrude.name = "PushFit Pocket Cut"
            
            # -----------------------------------------------------------------
            # SECTION 6J: CREATE OPTIONAL FILLET
            # -----------------------------------------------------------------
            # If fillet is enabled, apply it to the TOP edges only of the pocket
            # (the edges where the pocket meets the original face, not the bottom)
            filletApplied = False
            filletError = ''
            if addFillet and filletRadius > 0:
                try:
                    # We need to find edges that lie on the original target face plane
                    # These are the "top" edges of the pocket
                    
                    # Get the target face's geometry to determine its plane
                    targetGeom = targetFace.geometry
                    
                    # Get the plane's origin and normal for distance calculation
                    if hasattr(targetGeom, 'origin') and hasattr(targetGeom, 'normal'):
                        planeOrigin = targetGeom.origin
                        planeNormal = targetGeom.normal
                    else:
                        # Fallback - can't determine plane
                        filletError = 'Could not determine target face plane'
                        raise Exception(filletError)
                    
                    # Collect edges that are on the target face plane
                    topEdges = adsk.core.ObjectCollection.create()
                    
                    # Get all faces from the extrusion's side faces (walls of pocket)
                    sideFaces = extrude.sideFaces
                    
                    for face in sideFaces:
                        for edge in face.edges:
                            # Get both vertices of the edge
                            startPt = edge.startVertex.geometry
                            endPt = edge.endVertex.geometry
                            
                            # Calculate distance from each vertex to the target plane
                            # Distance = (point - planeOrigin) · planeNormal
                            startVec = adsk.core.Vector3D.create(
                                startPt.x - planeOrigin.x,
                                startPt.y - planeOrigin.y,
                                startPt.z - planeOrigin.z
                            )
                            endVec = adsk.core.Vector3D.create(
                                endPt.x - planeOrigin.x,
                                endPt.y - planeOrigin.y,
                                endPt.z - planeOrigin.z
                            )
                            
                            startDist = abs(startVec.dotProduct(planeNormal))
                            endDist = abs(endVec.dotProduct(planeNormal))
                            
                            # If BOTH vertices are very close to the plane, this is a top edge
                            tolerance = 0.0001  # 0.001mm tolerance
                            if startDist < tolerance and endDist < tolerance:
                                topEdges.add(edge)
                    
                    if topEdges.count > 0:
                        fillets = comp.features.filletFeatures
                        filletInput = fillets.createInput()
                        filletInput.addConstantRadiusEdgeSet(
                            topEdges,
                            adsk.core.ValueInput.createByReal(filletRadius),
                            True  # isTangentChain
                        )
                        fillet = fillets.add(filletInput)
                        fillet.name = "PushFit Pocket Fillet"
                        filletApplied = True
                    else:
                        filletError = 'No top edges found'
                except Exception as e:
                    if not filletError:
                        filletError = str(e)
            
            # -----------------------------------------------------------------
            # SECTION 6K: SUCCESS MESSAGE
            # -----------------------------------------------------------------
            filletMsg = ''
            if addFillet:
                if filletApplied:
                    filletMsg = 'Fillet Radius: {:.3f}mm\n'.format(filletRadius * 10)
                elif filletError:
                    filletMsg = 'Fillet: Failed - {}\n'.format(filletError)
                else:
                    filletMsg = 'Fillet: Failed to apply\n'
            
            _ui.messageBox(
                'Pocket(s) created successfully!\n\n' +
                'Number of Pockets: {}\n'.format(numPockets) +
                'Pocket Diameter: {:.3f}mm\n'.format(pocketDiameter * 10) +
                'Slots per Pocket: {}\n'.format(numSlots) +
                'Slot Width: {:.3f}mm\n'.format(slotWidth * 10) +
                'Slot Length (C-C): {:.3f}mm\n'.format(slotCenterToCenter * 10) +
                'Cut Depth: {:.3f}mm\n'.format(pocketDepth * 10) +
                filletMsg +
                'Profiles used: {}'.format(profilesToExtrude.count)
            )
            
        except:
            if _ui:
                _ui.messageBox('Failed to execute command:\n{}'.format(traceback.format_exc()))

# =============================================================================
# SECTION 7: COMMAND DESTROY HANDLER
# =============================================================================
class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            global _handlers
            _handlers = []
        except:
            if _ui:
                _ui.messageBox('Failed to destroy command:\n{}'.format(traceback.format_exc()))

# =============================================================================
# SECTION 8: RUN FUNCTION
# =============================================================================
def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        
        cmdDef = _ui.commandDefinitions.itemById(_commandId)
        if cmdDef:
            cmdDef.deleteMe()
        
        cmdDef = _ui.commandDefinitions.addButtonDefinition(
            _commandId,
            _commandName,
            _commandDescription
        )
        
        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)
        
        cmdDef.execute()
        adsk.autoTerminate(False)
        
    except:
        if _ui:
            _ui.messageBox('Failed to run script:\n{}'.format(traceback.format_exc()))

# =============================================================================
# SECTION 9: STOP FUNCTION
# =============================================================================
def stop(context):
    try:
        global _ui
        if _ui:
            cmdDef = _ui.commandDefinitions.itemById(_commandId)
            if cmdDef:
                cmdDef.deleteMe()
    except:
        if _ui:
            _ui.messageBox('Failed to stop script:\n{}'.format(traceback.format_exc()))