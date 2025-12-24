import adsk.core, adsk.fusion, traceback

# Global variables
app = None
ui = None
handlers = []
commandId = 'FaceCenterPoints_BodyCmd'
commandName = 'Face Center Points'
commandDescription = 'Add center points to selected faces'

# Location in UI
workspaceId = 'FusionSolidEnvironment'
panelId = 'SolidCreatePanel'


def run(context):
    """Called when add-in is started."""
    global app, ui
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the Create panel in the Solid workspace
        workspace = ui.workspaces.itemById(workspaceId)
        panel = workspace.toolbarPanels.itemById(panelId)
        
        # Check if command already exists (from previous run)
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if cmdDef:
            cmdDef.deleteMe()
        
        # Create command definition with icon
        cmdDef = ui.commandDefinitions.addButtonDefinition(
            commandId,
            commandName,
            commandDescription,
            './resources/icons'
        )
        
        # Connect command created handler
        onCommandCreated = FaceCenterCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # Add button to the panel
        buttonControl = panel.controls.addCommand(cmdDef)
        buttonControl.isPromoted = True
        
    except:
        if ui:
            ui.messageBox(f'Failed to start add-in:\n{traceback.format_exc()}')


def stop(context):
    """Called when add-in is stopped."""
    try:
        # Clean up UI
        workspace = ui.workspaces.itemById(workspaceId)
        panel = workspace.toolbarPanels.itemById(panelId)
        
        # Remove the button
        buttonControl = panel.controls.itemById(commandId)
        if buttonControl:
            buttonControl.deleteMe()
        
        # Remove command definition
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if cmdDef:
            cmdDef.deleteMe()
            
    except:
        if ui:
            ui.messageBox(f'Failed to stop add-in:\n{traceback.format_exc()}')


class FaceCenterCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Handler for when the command is created (dialog opens)."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            
            # Face selection input (multiple allowed)
            faceSelect = inputs.addSelectionInput(
                'faceSelection',
                'Faces',
                'Select faces to add center points'
            )
            faceSelect.addSelectionFilter('Faces')
            faceSelect.setSelectionLimits(1, 0)
            
            # Sketch organization dropdown
            sketchOption = inputs.addDropDownCommandInput(
                'sketchOrganization',
                'Sketch Organization',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            sketchOption.listItems.add('One sketch per face', True)
            sketchOption.listItems.add('Single consolidated sketch', False)
            
            # Center calculation method
            centerMethod = inputs.addDropDownCommandInput(
                'centerMethod',
                'Center Calculation',
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            centerMethod.listItems.add('Parametric center', True)
            centerMethod.listItems.add('Bounding box center', False)
            centerMethod.listItems.add('Area centroid', False)
            
            # Construction point toggle
            constructionToggle = inputs.addBoolValueInput(
                'useConstruction',
                'Construction points',
                True,
                '',
                False
            )
            
            # Connect execute handler
            onExecute = FaceCenterExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            # Connect destroy handler
            onDestroy = FaceCenterDestroyHandler()
            cmd.destroy.add(onDestroy)
            handlers.append(onDestroy)
            
        except:
            ui.messageBox(f'Command created failed:\n{traceback.format_exc()}')


class FaceCenterExecuteHandler(adsk.core.CommandEventHandler):
    """Handler for when user clicks OK."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            
            if not design:
                ui.messageBox('No active Fusion design.')
                return
            
            rootComp = design.rootComponent
            inputs = args.command.commandInputs
            
            # Get input values
            faceSelect = inputs.itemById('faceSelection')
            sketchOption = inputs.itemById('sketchOrganization')
            centerMethod = inputs.itemById('centerMethod')
            constructionToggle = inputs.itemById('useConstruction')
            
            oneSketchPerFace = sketchOption.selectedItem.index == 0
            useConstruction = constructionToggle.value
            methodIndex = centerMethod.selectedItem.index
            
            # Collect selected faces
            faces = []
            for i in range(faceSelect.selectionCount):
                face = adsk.fusion.BRepFace.cast(faceSelect.selection(i).entity)
                if face:
                    faces.append(face)
            
            if not faces:
                ui.messageBox('No valid faces selected.')
                return
            
            pointsAdded = 0
            
            if oneSketchPerFace:
                for idx, face in enumerate(faces):
                    center = self.calculateCenter(face, methodIndex)
                    if center:
                        sketch = rootComp.sketches.add(face)
                        sketch.name = f'FaceCenter_{idx + 1}'
                        sketchCenter = sketch.modelToSketchSpace(center)
                        point = sketch.sketchPoints.add(sketchCenter)
                        if useConstruction:
                            point.isConstruction = True
                        pointsAdded += 1
            else:
                baseFace = faces[0]
                sketch = rootComp.sketches.add(baseFace)
                sketch.name = f'FaceCenters_x{len(faces)}'
                
                for face in faces:
                    center = self.calculateCenter(face, methodIndex)
                    if center:
                        sketchCenter = sketch.modelToSketchSpace(center)
                        point = sketch.sketchPoints.add(sketchCenter)
                        if useConstruction:
                            point.isConstruction = True
                        pointsAdded += 1
            
            ui.messageBox(f'Added {pointsAdded} center point(s) to {len(faces)} face(s).')
            
        except:
            ui.messageBox(f'Execute failed:\n{traceback.format_exc()}')
    
    def calculateCenter(self, face, method):
        """Calculate face center using specified method."""
        try:
            if method == 0:
                # Parametric center
                evaluator = face.evaluator
                paramRange = face.evaluator.parametricRange()
                uMid = (paramRange.minPoint.x + paramRange.maxPoint.x) / 2
                vMid = (paramRange.minPoint.y + paramRange.maxPoint.y) / 2
                (success, center) = evaluator.getPointAtParameter(
                    adsk.core.Point2D.create(uMid, vMid)
                )
                if success:
                    return center
                    
            elif method == 1:
                # Bounding box center
                box = face.boundingBox
                return adsk.core.Point3D.create(
                    (box.minPoint.x + box.maxPoint.x) / 2,
                    (box.minPoint.y + box.maxPoint.y) / 2,
                    (box.minPoint.z + box.maxPoint.z) / 2
                )
                
            elif method == 2:
                # Area centroid using mesh triangulation
                mesh = face.meshManager.displayMeshes.bestMesh
                if mesh:
                    totalArea = 0
                    centroidX = centroidY = centroidZ = 0
                    
                    coords = mesh.nodeCoordinates
                    indices = mesh.nodeIndices
                    
                    for i in range(0, mesh.triangleCount):
                        i0 = indices[i * 3]
                        i1 = indices[i * 3 + 1]
                        i2 = indices[i * 3 + 2]
                        
                        p0 = coords[i0]
                        p1 = coords[i1]
                        p2 = coords[i2]
                        
                        # Triangle centroid
                        cx = (p0.x + p1.x + p2.x) / 3
                        cy = (p0.y + p1.y + p2.y) / 3
                        cz = (p0.z + p1.z + p2.z) / 3
                        
                        # Triangle area
                        v1 = adsk.core.Vector3D.create(
                            p1.x - p0.x, p1.y - p0.y, p1.z - p0.z
                        )
                        v2 = adsk.core.Vector3D.create(
                            p2.x - p0.x, p2.y - p0.y, p2.z - p0.z
                        )
                        cross = v1.crossProduct(v2)
                        area = cross.length / 2
                        
                        totalArea += area
                        centroidX += cx * area
                        centroidY += cy * area
                        centroidZ += cz * area
                    
                    if totalArea > 0:
                        return adsk.core.Point3D.create(
                            centroidX / totalArea,
                            centroidY / totalArea,
                            centroidZ / totalArea
                        )
            
            # Fallback to bounding box
            box = face.boundingBox
            return adsk.core.Point3D.create(
                (box.minPoint.x + box.maxPoint.x) / 2,
                (box.minPoint.y + box.maxPoint.y) / 2,
                (box.minPoint.z + box.maxPoint.z) / 2
            )
            
        except:
            return None


class FaceCenterDestroyHandler(adsk.core.CommandEventHandler):
    """Handler for when command dialog is closed."""
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        pass