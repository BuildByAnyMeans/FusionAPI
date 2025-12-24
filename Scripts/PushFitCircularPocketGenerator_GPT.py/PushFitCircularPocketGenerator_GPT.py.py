# PushFitCircularPocketGenerator_GPT.py
# ------------------------------------------------------------
# "Push-Fit Circular Pocket Generator" (GPT version, Face-aware)
#
# Creates a circular push-fit pocket plus an alignment slot.
#
# UI INPUTS (in order):
#   1) Center Point   : SketchPoint / Vertex / ConstructionPoint
#   2) Alignment Line : SketchLine / Linear edge (slot direction)
#   3) Target Face    : planar face to receive the pocket
#   4) Disk Diameter  : nominal insert diameter (mm)
#   5) Disk Thickness : insert thickness (mm)
#   6) Material       : PLA (placeholder)
#   7) Fit            : Standard (+0.125 mm) or Loose (+0.20 mm)
#   8) Set Depth      : Proud (T), Flush (T+0.25), Deep (T+0.50)
#   9) Add Fillet     : checkbox (optional chamfer on pocket rim)
#  10) Fillet Radius  : radius in mm (default 0.5 mm)
# ------------------------------------------------------------

import adsk.core, adsk.fusion, adsk.cam, traceback, math

handlers = []  # keep event handlers alive


# =====================================================================
# Helper functions
# =====================================================================

def normalize2d(dx, dy):
    """Return unit vector (ux, uy) for (dx, dy), or (None, None) if zero-length."""
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        return None, None
    return dx / length, dy / length


def offset_point_2d(px, py, vx, vy, dist):
    """Offset (px, py) along (vx, vy) by dist; assumes (vx, vy) is unit."""
    return px + vx * dist, py + vy * dist


# =====================================================================
# Execute handler
# =====================================================================

class PushFitPocketExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('No active Fusion 360 design. Open a design and try again.')
                return

            unitsMgr = design.unitsManager
            designUnits = unitsMgr.defaultLengthUnits  # e.g. "cm"

            # ------------------------------------------------------------
            # 1. Read inputs
            # ------------------------------------------------------------

            # Center Point
            centerSelInput = adsk.core.SelectionCommandInput.cast(
                inputs.itemById('centerPoint')
            )
            if centerSelInput.selectionCount != 1:
                ui.messageBox('Please select a single Center Point.')
                return
            centerEntity = centerSelInput.selection(0).entity

            # Alignment Line
            lineSelInput = adsk.core.SelectionCommandInput.cast(
                inputs.itemById('alignmentLine')
            )
            if lineSelInput.selectionCount != 1:
                ui.messageBox('Please select a single Alignment Line.')
                return
            alignEntity = lineSelInput.selection(0).entity

            # Target Face
            faceSelInput = adsk.core.SelectionCommandInput.cast(
                inputs.itemById('targetFace')
            )
            if faceSelInput.selectionCount != 1:
                ui.messageBox('Please select a single Target Face.')
                return
            targetFace = adsk.fusion.BRepFace.cast(faceSelInput.selection(0).entity)
            comp = targetFace.body.parentComponent

            # Disk diameter & thickness
            diaInput = adsk.core.ValueCommandInput.cast(
                inputs.itemById('diskDiameter')
            )
            thickInput = adsk.core.ValueCommandInput.cast(
                inputs.itemById('diskThickness')
            )
            diskDiameter = diaInput.value      # design units
            diskThickness = thickInput.value   # design units

            # Material (placeholder)
            matDrop = adsk.core.DropDownCommandInput.cast(
                inputs.itemById('materialDrop')
            )
            materialName = matDrop.selectedItem.name

            # Fit
            fitDrop = adsk.core.DropDownCommandInput.cast(
                inputs.itemById('fitDrop')
            )
            fitName = fitDrop.selectedItem.name

            # Set Depth
            seatDrop = adsk.core.DropDownCommandInput.cast(
                inputs.itemById('seatDrop')
            )
            seatName = seatDrop.selectedItem.name

            # Fillet options
            filletCheck = adsk.core.BoolValueCommandInput.cast(
                inputs.itemById('addFillet')
            )
            doFillet = filletCheck and filletCheck.value

            filletRadiusInput = adsk.core.ValueCommandInput.cast(
                inputs.itemById('filletRadius')
            )
            filletRadius = filletRadiusInput.value  # design units

            # ------------------------------------------------------------
            # 2. Derived dimensions (tolerances, depth, slot sizes)
            # ------------------------------------------------------------

            # 2a. Tolerance offset (mm → designUnits)
            if fitName.lower().startswith('standard'):
                tolOffset_mm = 0.125
            else:
                tolOffset_mm = 0.20

            tolOffset = unitsMgr.evaluateExpression(
                f"{tolOffset_mm} mm", designUnits
            )

            holeDiameter = diskDiameter + tolOffset
            holeRadius = holeDiameter / 2.0

            # 2b. Seating offset (mm → designUnits)
            if seatName.lower().startswith('proud'):
                seatOffset_mm = 0.0
            elif seatName.lower().startswith('flush'):
                seatOffset_mm = 0.25
            else:
                seatOffset_mm = 0.50

            seatOffset = unitsMgr.evaluateExpression(
                f"{seatOffset_mm} mm", designUnits
            )

            # Depth is based on THICKNESS (T, T+0.25, T+0.50)
            pocketDepth = diskThickness + seatOffset  # design units

            # 2c. Slot sizes (in design units)
            slotWidth = holeDiameter * 0.10
            slotHalfWidth = slotWidth / 2.0
            slotCenterSpacing = holeDiameter * 1.25
            slotHalfSpacing = slotCenterSpacing / 2.0

            # ------------------------------------------------------------
            # 3. New sketch on Target Face, project center & line
            # ------------------------------------------------------------

            sketches = comp.sketches
            sketch = sketches.add(targetFace)

            # Project center point
            projCenter = sketch.project(centerEntity)
            centerPointSketch = None
            for e in projCenter:
                centerPointSketch = adsk.fusion.SketchPoint.cast(e)
                if centerPointSketch:
                    break
            if not centerPointSketch:
                ui.messageBox('Could not project the Center Point into the sketch.')
                return

            # Project alignment line
            projLine = sketch.project(alignEntity)
            alignLineSketch = None
            for e in projLine:
                alignLineSketch = adsk.fusion.SketchLine.cast(e)
                if alignLineSketch:
                    break
            if not alignLineSketch:
                ui.messageBox('Could not project the Alignment Line into the sketch.')
                return

            # ------------------------------------------------------------
            # 4. Build circle + slot in sketch space
            # ------------------------------------------------------------

            centerGeo = centerPointSketch.geometry
            cx = centerGeo.x
            cy = centerGeo.y

            startGeo = alignLineSketch.startSketchPoint.geometry
            endGeo = alignLineSketch.endSketchPoint.geometry
            dx = endGeo.x - startGeo.x
            dy = endGeo.y - startGeo.y

            ux, uy = normalize2d(dx, dy)
            if ux is None:
                ui.messageBox('Alignment Line has zero length; cannot determine direction.')
                return

            px = -uy
            py = ux

            # Slot end centers
            topCx, topCy = offset_point_2d(cx, cy, ux, uy, slotHalfSpacing)
            botCx, botCy = offset_point_2d(cx, cy, ux, uy, -slotHalfSpacing)

            # Rectangle corners
            topLeft_x, topLeft_y = offset_point_2d(topCx, topCy, px, py, -slotHalfWidth)
            topRight_x, topRight_y = offset_point_2d(topCx, topCy, px, py, slotHalfWidth)
            botLeft_x, botLeft_y = offset_point_2d(botCx, botCy, px, py, -slotHalfWidth)
            botRight_x, botRight_y = offset_point_2d(botCx, botCy, px, py, slotHalfWidth)

            sketch.isComputeDeferred = True

            circles = sketch.sketchCurves.sketchCircles
            lines = sketch.sketchCurves.sketchLines

            # Main circular pocket
            centerPt = adsk.core.Point3D.create(cx, cy, 0)
            circles.addByCenterRadius(centerPt, holeRadius)

            # Slot circles
            topCenterPt = adsk.core.Point3D.create(topCx, topCy, 0)
            botCenterPt = adsk.core.Point3D.create(botCx, botCy, 0)
            circles.addByCenterRadius(topCenterPt, slotHalfWidth)
            circles.addByCenterRadius(botCenterPt, slotHalfWidth)

            # Slot rectangle
            topLeftPt = adsk.core.Point3D.create(topLeft_x, topLeft_y, 0)
            topRightPt = adsk.core.Point3D.create(topRight_x, topRight_y, 0)
            botLeftPt = adsk.core.Point3D.create(botLeft_x, botLeft_y, 0)
            botRightPt = adsk.core.Point3D.create(botRight_x, botRight_y, 0)

            lines.addByTwoPoints(topLeftPt, topRightPt)
            lines.addByTwoPoints(topRightPt, botRightPt)
            lines.addByTwoPoints(botRightPt, botLeftPt)
            lines.addByTwoPoints(botLeftPt, topLeftPt)

            sketch.isComputeDeferred = False

            # ------------------------------------------------------------
            # 5. One-sided extrude-cut of ONLY the pocket profiles
            # ------------------------------------------------------------

            allProfiles = list(sketch.profiles)
            profs = adsk.core.ObjectCollection.create()

            # Filter: keep only "small" profiles near the hole
            # (face outline is huge compared to circle+slot)
            maxSize = holeDiameter * 3.0  # bounding-box width/height limit

            for prof in allProfiles:
                bb = prof.boundingBox
                w = abs(bb.maxPoint.x - bb.minPoint.x)
                h = abs(bb.maxPoint.y - bb.minPoint.y)
                if w <= maxSize and h <= maxSize:
                    profs.add(prof)

            # Fallback: if filter got nothing (shouldn't happen), use all.
            if profs.count == 0:
                for prof in allProfiles:
                    profs.add(prof)

            extrudes = comp.features.extrudeFeatures
            depthVal = adsk.core.ValueInput.createByReal(-pocketDepth)  # negative = into body

            extInput = extrudes.createInput(
                profs,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )

            # One-sided distance extent (negative direction into the part)
            extInput.setDistanceExtent(False, depthVal)
            extInput.isSolid = True

            extrudeFeature = extrudes.add(extInput)

            # ------------------------------------------------------------
            # 6. Optional fillet on pocket rim
            # ------------------------------------------------------------

            if doFillet and filletRadius > 0:
                edgesToFillet = adsk.core.ObjectCollection.create()

                # Tolerances for matching radius & center
                radTol = unitsMgr.evaluateExpression("0.01 mm", designUnits)
                cenTol = unitsMgr.evaluateExpression("0.01 mm", designUnits)

                # World-space center of our pocket (from projected sketch point)
                cpWorld = centerPointSketch.worldGeometry

                body = targetFace.body
                for edge in body.edges:
                    geom = edge.geometry
                    # We only care about circular edges
                    if geom.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                        circle = adsk.core.Circle3D.cast(geom)
                        # Radius close to our pocket radius?
                        if abs(circle.radius - holeRadius) <= radTol:
                            # Center close to our pocket center?
                            if circle.center.distanceTo(cpWorld) <= cenTol:
                                # Edge must lie on the target face (front rim)
                                onFace = False
                                for f in edge.faces:
                                    if f == targetFace:
                                        onFace = True
                                        break
                                if onFace:
                                    edgesToFillet.add(edge)

                if edgesToFillet.count > 0:
                    fillets = comp.features.filletFeatures
                    filletInput = fillets.createInput()
                    filletInput.addConstantRadiusEdgeSet(
                        edgesToFillet,
                        adsk.core.ValueInput.createByReal(filletRadius),
                        True
                    )
                    fillets.add(filletInput)

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# =====================================================================
# InputChanged handler (to enable/disable fillet radius)
# =====================================================================

class PushFitPocketInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs
            changedInput = eventArgs.input

            if changedInput.id == 'addFillet':
                filletCheck = adsk.core.BoolValueCommandInput.cast(changedInput)
                filletRadiusInput = adsk.core.ValueCommandInput.cast(
                    inputs.itemById('filletRadius')
                )
                # Enable radius field only when checkbox is on
                filletRadiusInput.isEnabled = filletCheck.value

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# =====================================================================
# CommandCreated handler (builds the UI)
# =====================================================================

class PushFitPocketCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        app = adsk.core.Application.get()
        ui = app.userInterface
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Hook up execute + input-changed handlers
            onExecute = PushFitPocketExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            onInputChanged = PushFitPocketInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

            design = adsk.fusion.Design.cast(app.activeProduct)
            unitsMgr = design.unitsManager if design else None
            designUnits = unitsMgr.defaultLengthUnits if unitsMgr else 'cm'

            # Precompute correct defaults in internal units
            defaultDia = unitsMgr.evaluateExpression("6 mm", designUnits) if unitsMgr else 0.6
            defaultThk = unitsMgr.evaluateExpression("2 mm", designUnits) if unitsMgr else 0.2
            defaultFillet = unitsMgr.evaluateExpression("0.5 mm", designUnits) if unitsMgr else 0.05

            # 1) Center Point
            centerSel = inputs.addSelectionInput(
                'centerPoint',
                'Center Point',
                'Select a point for the pocket center (sketch point, vertex, or construction point).'
            )
            centerSel.addSelectionFilter('SketchPoints')
            centerSel.addSelectionFilter('Vertices')
            centerSel.addSelectionFilter('ConstructionPoints')
            centerSel.setSelectionLimits(1, 1)

            # 2) Alignment Line
            lineSel = inputs.addSelectionInput(
                'alignmentLine',
                'Alignment Line',
                'Select a line or edge to control slot direction.'
            )
            lineSel.addSelectionFilter('SketchLines')
            lineSel.addSelectionFilter('LinearEdges')
            lineSel.setSelectionLimits(1, 1)

            # 3) Target Face
            faceSel = inputs.addSelectionInput(
                'targetFace',
                'Target Face',
                'Select the planar face where the pocket should be created.'
            )
            faceSel.addSelectionFilter('PlanarFaces')
            faceSel.setSelectionLimits(1, 1)

            # 4) Disk Diameter (6 mm default)
            inputs.addValueInput(
                'diskDiameter',
                'Disk Diameter',
                'mm',
                adsk.core.ValueInput.createByReal(defaultDia)
            )

            # 5) Disk Thickness (2 mm default)
            inputs.addValueInput(
                'diskThickness',
                'Disk Thickness',
                'mm',
                adsk.core.ValueInput.createByReal(defaultThk)
            )

            # 6) Material
            matDrop = inputs.addDropDownCommandInput(
                'materialDrop',
                'Material',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            matDrop.listItems.add('PLA', True)

            # 7) Fit
            fitDrop = inputs.addDropDownCommandInput(
                'fitDrop',
                'Fit',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            fitDrop.listItems.add('Standard (+0.125 mm)', True)
            fitDrop.listItems.add('Loose (+0.20 mm)', False)

            # 8) Set Depth
            seatDrop = inputs.addDropDownCommandInput(
                'seatDrop',
                'Set Depth',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            seatDrop.listItems.add('Proud (depth = T)', False)
            seatDrop.listItems.add('Flush (T + 0.25 mm)', True)
            seatDrop.listItems.add('Deep (T + 0.50 mm)', False)

            # 9) Add Fillet checkbox
            filletCheck = inputs.addBoolValueInput(
                'addFillet',
                'Add Fillet',
                True,   # display check icon
                '',
                False   # default unchecked
            )

            # 10) Fillet Radius (0.5 mm default)
            filletRadiusInput = inputs.addValueInput(
                'filletRadius',
                'Fillet Radius',
                'mm',
                adsk.core.ValueInput.createByReal(defaultFillet)
            )
            filletRadiusInput.isEnabled = filletCheck.value  # disabled when unchecked

        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# =====================================================================
# run() / stop()
# =====================================================================

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        cmdDefs = ui.commandDefinitions
        cmdDef = cmdDefs.itemById('PushFitCircularPocketCmd_GPT')
        if not cmdDef:
            cmdDef = cmdDefs.addButtonDefinition(
                'PushFitCircularPocketCmd_GPT',
                'Push-Fit Circular Pocket Generator (GPT)',
                'Creates a circular push-fit pocket with an alignment slot.',
                ''
            )

        onCommandCreated = PushFitPocketCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        cmdDef.execute()
        adsk.autoTerminate(False)

    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    pass
