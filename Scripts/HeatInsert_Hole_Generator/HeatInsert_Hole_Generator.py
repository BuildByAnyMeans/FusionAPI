# HeatInsert_Hole_Generator.py
# Fusion 360 Script: Generate Heat-Set Insert Holes with Optional Counterbores
# Author: Parker + ChatGPT

import adsk.core, adsk.fusion, traceback

app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

insert_specs = {
    'M2': {
        'options': {
            'M2x2': {'depth': 2.2},
            'M2x3': {'depth': 3.2},
            'M2x4': {'depth': 4.2}
        },
        'top_dia': 2.8, 'bottom_dia': 2.5, 'od': 2.7, 'screw_head_dia': 4.0, 'screw_head_height': 2.2
    },
    'M3': {
        'options': {
            'M3x3': {'depth': 3.2},
            'M3x4': {'depth': 4.2},
            'M3x5': {'depth': 5.2},
            'M3x6': {'depth': 6.2},
            'M3x8': {'depth': 8.2}
        },
        'top_dia': 4.4, 'bottom_dia': 4.0, 'od': 4.2, 'screw_head_dia': 6.0, 'screw_head_height': 3.2
    },
    'M4': {
        'options': {
            'M4x8': {'depth': 8.2},
            'M4x10': {'depth': 10.2}
        },
        'top_dia': 5.8, 'bottom_dia': 5.4, 'od': 5.6, 'screw_head_dia': 7.5, 'screw_head_height': 4.2
    },
    'M5': {
        'options': {
            'M5x10': {'depth': 10.2},
            'M5x12': {'depth': 12.2}
        },
        'top_dia': 6.7, 'bottom_dia': 6.3, 'od': 6.5, 'screw_head_dia': 9.2, 'screw_head_height': 5.2
    }
}

def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('No active Fusion 360 design found.')
            return

        cmd_defs = ui.commandDefinitions
        existing_def = cmd_defs.itemById('HeatInsert_Hole_Generator')
        if existing_def:
            existing_def.deleteMe()

        cmd_def = cmd_defs.addButtonDefinition('HeatInsert_Hole_Generator', 'Heat Insert Hole Generator', 'Create insert holes')
        on_command_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_command_created)
        handlers.append(on_command_created)
        cmd_def.execute()
        adsk.autoTerminate(False)

    except Exception as e:
        ui.messageBox(f'Run Error: {str(e)}\n{traceback.format_exc()}')

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            inputs = cmd.commandInputs

            body_sel = inputs.addSelectionInput('targetBody', 'Target Body', 'Select the target body to cut')
            body_sel.addSelectionFilter('Bodies')
            body_sel.setSelectionLimits(1, 1)

            point_sel = inputs.addSelectionInput('pointSel', 'Select Points', 'Choose point(s) for insert holes')
            point_sel.addSelectionFilter('ConstructionPoints')
            point_sel.addSelectionFilter('SketchPoints')
            point_sel.addSelectionFilter('Vertices')
            point_sel.setSelectionLimits(1, 0)

            thread_input = inputs.addDropDownCommandInput('threadSize', 'Thread Size', adsk.core.DropDownStyles.TextListDropDownStyle)
            for size in insert_specs:
                thread_input.listItems.add(size, size == 'M3')

            insert_length_input = inputs.addDropDownCommandInput('insertLength', 'Insert Length', adsk.core.DropDownStyles.TextListDropDownStyle)
            for key in insert_specs['M3']['options'].keys():
                insert_length_input.listItems.add(key, key == 'M3x5')

            fit_style = inputs.addDropDownCommandInput('fitStyle', 'Insert Fit Style', adsk.core.DropDownStyles.TextListDropDownStyle)
            fit_style.listItems.add('Flush Insert', True)
            fit_style.listItems.add('Flush Screw', False)

            extra_depth = inputs.addValueInput('extraDepth', 'Extra Depth (optional)', 'mm', adsk.core.ValueInput.createByReal(0.0))

            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)

            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)

        except Exception as e:
            ui.messageBox(f'Command Creation Error: {str(e)}')

class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        try:
            inputs = args.inputs
            thread_input = inputs.itemById('threadSize')
            insert_length_input = inputs.itemById('insertLength')
            if args.input.id == 'threadSize':
                insert_length_input.listItems.clear()
                for key in insert_specs[thread_input.selectedItem.name]['options'].keys():
                    insert_length_input.listItems.add(key, True)

        except Exception as e:
            ui.messageBox(f'Input Changed Error: {str(e)}')

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            cmd = args.firingEvent.sender
            inputs = cmd.commandInputs

            body = inputs.itemById('targetBody').selection(0).entity

            selection_input = inputs.itemById('pointSel')
            selected_points = [selection_input.selection(i).entity for i in range(selection_input.selectionCount)]

            thread_size = inputs.itemById('threadSize').selectedItem.name
            insert_length = inputs.itemById('insertLength').selectedItem.name
            fit_style = inputs.itemById('fitStyle').selectedItem.name
            extra_depth = inputs.itemById('extraDepth').value

            spec = insert_specs[thread_size]
            length_spec = spec['options'][insert_length]
            insert_depth = length_spec['depth'] + extra_depth

            top_dia = spec['top_dia']
            bottom_dia = spec['bottom_dia']
            screw_dia = spec['screw_head_dia'] if fit_style == 'Flush Screw' else spec['od'] + 0.3
            screw_depth = spec['screw_head_height'] if fit_style == 'Flush Screw' else 0.5

            root_comp = adsk.fusion.Design.cast(app.activeProduct).rootComponent
            sketches = root_comp.sketches
            extrudes = root_comp.features.extrudeFeatures
            planes = root_comp.constructionPlanes

            for i, point in enumerate(selected_points):
                # create offset plane at selected Z
                z_plane_input = planes.createInput()
                offset = adsk.core.ValueInput.createByReal(point.geometry.z)
                z_plane_input.setByOffset(root_comp.xYConstructionPlane, offset)
                offset_plane = planes.add(z_plane_input)

                # create sketch on that plane
                sketch = sketches.add(offset_plane)
                sketch.name = f"InsertHole_{i}"

                # convert 3D point to sketch space and draw circles centered on selected point
                center2d = sketch.modelToSketchSpace(point.geometry)
                sketch_circles = sketch.sketchCurves.sketchCircles
                outer_circle = sketch_circles.addByCenterRadius(center2d, screw_dia / 2)
                inner_circle = sketch_circles.addByCenterRadius(center2d, bottom_dia / 2)

                # cut counterbore into target body
                prof = sketch.profiles.item(0)
                extrude_input = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
                extrude_input.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(-screw_depth)), adsk.fusion.ExtentDirections.NegativeExtentDirection)
                extrude_input.targetBodies = [body]
                extrudes.add(extrude_input)

        except Exception as e:
            ui.messageBox(f'Execution Error: {str(e)}\n{traceback.format_exc()}')
