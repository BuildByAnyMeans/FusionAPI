# Arrange_Spacing_1d_CommandUI.py
# Fusion 360 Script: Evenly spaces selected bodies/components along one axis
# Uses CommandInputs for a full dialog UI

import adsk.core, adsk.fusion, adsk.cam, traceback

handlers = []

# ✅ 1. Define UI creation handler
class ArrangeCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            onExecute = ArrangeCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            selection_input = inputs.addSelectionInput("selection", "Objects", "Select bodies or components")
            selection_input.addSelectionFilter("Bodies")
            selection_input.addSelectionFilter("Occurrences")
            selection_input.setSelectionLimits(1)

            axis_dropdown = inputs.addDropDownCommandInput("axis", "Arrange Along Axis", adsk.core.DropDownStyles.TextListDropDownStyle)
            axis_dropdown.listItems.add("X", True)
            axis_dropdown.listItems.add("Y", False)
            axis_dropdown.listItems.add("Z", False)

            mode_dropdown = inputs.addDropDownCommandInput("mode", "Spacing Mode", adsk.core.DropDownStyles.TextListDropDownStyle)
            mode_dropdown.listItems.add("Spacing (Fixed Gap)", True)
            mode_dropdown.listItems.add("Extent (Total Distance)", False)

            spacing_type_dropdown = inputs.addDropDownCommandInput("spacingType", "Spacing Type", adsk.core.DropDownStyles.TextListDropDownStyle)
            spacing_type_dropdown.listItems.add("Bounding Box", True)
            spacing_type_dropdown.listItems.add("Center to Center", False)

            spacing_value_input = inputs.addValueInput("spacingValue", "Spacing Distance", "mm", adsk.core.ValueInput.createByString("10"))

            inputs.addBoolValueInput("respectOrder", "Respect Selection Order", True, "", False)
            inputs.addBoolValueInput("reverseOrder", "Reverse Order", True, "", False)
            inputs.addBoolValueInput("alignOtherAxes", "Align Along Other Axes", True, "", True)

        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Command creation failed:\n{}'.format(traceback.format_exc()))


# ✅ 2. Define execution handler
class ArrangeCommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = adsk.fusion.Design.cast(app.activeProduct)
            root = design.rootComponent

            inputs = args.firingEvent.sender.commandInputs

            selection_input = inputs.itemById("selection")
            selected = [selection_input.selection(i).entity for i in range(selection_input.selectionCount)]

            if len(selected) < 2:
                ui.messageBox("Select at least two bodies or components.")
                return

            axis = inputs.itemById("axis").selectedItem.name
            axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]

            spacing_type = inputs.itemById("spacingType").selectedItem.name.lower()
            mode = inputs.itemById("mode").selectedItem.name.lower()

            respect_order = inputs.itemById("respectOrder").value
            reverse_order = inputs.itemById("reverseOrder").value
            align_other = inputs.itemById("alignOtherAxes").value

            spacing_value = inputs.itemById("spacingValue").value

            bodies = []
            for entity in selected:
                if isinstance(entity, adsk.fusion.BRepBody):
                    bodies.append(entity)
                elif isinstance(entity, adsk.fusion.Occurrence):
                    for body in entity.bRepBodies:
                        bodies.append(body)

            def get_position(body):
                box = body.boundingBox
                if spacing_type == "bounding box":
                    return box.minPoint.asArray(), box.maxPoint.asArray()
                else:
                    center = body.physicalProperties.centerOfMass.asArray()
                    return center, center

            bodies_with_pos = [(get_position(b)[0], get_position(b)[1], b) for b in bodies]

            if align_other:
                ref_min = bodies_with_pos[0][0]
                for i, (min_pt, max_pt, body) in enumerate(bodies_with_pos):
                    move_vec = [0, 0, 0]
                    for j in range(3):
                        if j != axis_index:
                            move_vec[j] = ref_min[j] - min_pt[j]
                    if any(move_vec):
                        move = adsk.core.Vector3D.create(*move_vec)
                        matrix = adsk.core.Matrix3D.create()
                        matrix.translation = move
                        if body.assemblyContext:
                            occurrence = body.assemblyContext
                            new_transform = occurrence.transform.copy()
                            new_transform.transformBy(matrix)
                            occurrence.transform = new_transform
                        else:
                            body.transformBy(matrix)
                bodies_with_pos = [(get_position(b)[0], get_position(b)[1], b) for b in bodies]

            if not respect_order:
                bodies_with_pos.sort(key=lambda x: x[0][axis_index])
            if reverse_order:
                bodies_with_pos.reverse()

            if mode == "extent":
                extent_input = ui.inputBox("Enter total extent distance in mm:", "Total Extent", "100")
                total_extent = float(extent_input)
                num_gaps = len(bodies_with_pos) - 1
                if num_gaps < 1:
                    ui.messageBox("Need at least two objects for extent spacing.")
                    return

                if spacing_type == "bounding box":
                    widths = [max_pt[axis_index] - min_pt[axis_index] for min_pt, max_pt, _ in bodies_with_pos]
                    total_width = sum(widths)
                    available_gap = total_extent - total_width
                    if available_gap < 0:
                        ui.messageBox("Total extent is too small to fit all objects without overlap.")
                        return
                    gap = available_gap / num_gaps
                   
                    # Start at zero extent
                    curr_pos = bodies_with_pos[0][0][axis_index]

                    for i, (min_pt, max_pt, body) in enumerate(bodies_with_pos):
                        body_min = min_pt[axis_index]
                        delta = curr_pos - body_min

                        move_vec = [0, 0, 0]
                        move_vec[axis_index] = delta
                        move = adsk.core.Vector3D.create(*move_vec)
                        matrix = adsk.core.Matrix3D.create()
                        matrix.translation = move

                        if body.assemblyContext:
                            occurrence = body.assemblyContext
                            new_transform = occurrence.transform.copy()
                            new_transform.transformBy(matrix)
                            occurrence.transform = new_transform
                        else:
                            body.transformBy(matrix)

                        # Advance for next body
                        curr_pos += widths[i] + (gap if i < len(bodies_with_pos) - 1 else 0)


                else:
                    centers = [(min_pt[axis_index] + max_pt[axis_index]) / 2 for min_pt, max_pt, _ in bodies_with_pos]
                    total_span = centers[-1] - centers[0]
                    available_span = total_extent - total_span
                    step = total_extent / num_gaps
                    start_center = centers[0]
                    curr_pos = start_center

                    for i in range(1, len(bodies_with_pos)):
                        min_pt, max_pt, body = bodies_with_pos[i]
                        center = (min_pt[axis_index] + max_pt[axis_index]) / 2
                        target_center = start_center + i * step
                        delta = target_center - center

                        move_vec = [0, 0, 0]
                        move_vec[axis_index] = delta
                        move = adsk.core.Vector3D.create(*move_vec)
                        matrix = adsk.core.Matrix3D.create()
                        matrix.translation = move

                        if body.assemblyContext:
                            occurrence = body.assemblyContext
                            new_transform = occurrence.transform.copy()
                            new_transform.transformBy(matrix)
                            occurrence.transform = new_transform
                        else:
                            body.transformBy(matrix)

            else:
                _, prev_max, prev_body = bodies_with_pos[0]
                curr_pos = prev_max[axis_index]

                for i in range(1, len(bodies_with_pos)):
                    _, _, body = bodies_with_pos[i]
                    box = body.boundingBox

                    if spacing_type == "bounding box":
                        body_min = box.minPoint.asArray()
                        body_max = box.maxPoint.asArray()
                        move_from = body_min[axis_index]
                        move_to = curr_pos + spacing_value
                        curr_pos = move_to + (body_max[axis_index] - body_min[axis_index])
                    else:
                        center = body.physicalProperties.centerOfMass.asArray()
                        move_from = center[axis_index]
                        move_to = curr_pos + spacing_value
                        curr_pos = move_to

                    delta = move_to - move_from
                    move_vec = [0, 0, 0]
                    move_vec[axis_index] = delta
                    move = adsk.core.Vector3D.create(*move_vec)
                    matrix = adsk.core.Matrix3D.create()
                    matrix.translation = move

                    if body.assemblyContext:
                        occurrence = body.assemblyContext
                        new_transform = occurrence.transform.copy()
                        new_transform.transformBy(matrix)
                        occurrence.transform = new_transform
                    else:
                        body.transformBy(matrix)

        except Exception as e:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox(f"Execution failed:\n{traceback.format_exc()}")


# ✅ 3. Run logic
def run(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        cmdDefs = ui.commandDefinitions

        existing_cmd = cmdDefs.itemById("ArrangeSpacing1d")
        if existing_cmd:
            existing_cmd.deleteMe()

        cmdDef = cmdDefs.addButtonDefinition(
            "ArrangeSpacing1d",
            "Arrange Spacing 1D",
            "Evenly space selected bodies/components along one axis."
        )

        onCommandCreated = ArrangeCommandCreatedEventHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        cmdDef.execute()
        adsk.autoTerminate(False)

    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Script failed:\n{}'.format(traceback.format_exc()))
