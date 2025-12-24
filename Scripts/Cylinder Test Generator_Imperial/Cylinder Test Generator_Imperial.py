import adsk.core, adsk.fusion, adsk.cam, traceback
import math

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            ui.messageBox('Please switch to the Design workspace.')
            return
        root = design.rootComponent

        # --- user params ---
        start_diam_in = 0.125
        end_diam_in   = 2.0
        step_in       = 0.125
        block_thickness_mm = 10.0
        cyl_height_mm      = 20.0
        block_margin_mm    = 1.5
        spacing_margin_mm  = 6.0
        add_string_hole     = False
        hole_diam_mm        = 3.0
        hole_edge_offset_mm = 2.0

        # --- units/helpers ---
        mm_to_cm = 0.1
        in_to_mm = 25.4
        in_to_cm = in_to_mm * mm_to_cm

        count = int(math.floor((end_diam_in - start_diam_in) / step_in)) + 1
        end_diam_mm       = end_diam_in * in_to_mm
        max_block_side_mm = end_diam_mm + 2.0 * block_margin_mm
        center_pitch_mm   = max_block_side_mm + spacing_margin_mm

        # --- create a new sub-component and build inside it ---
        occs = root.occurrences
        newOcc = occs.addNewComponent(adsk.core.Matrix3D.create())
        comp = newOcc.component
        comp.name = 'Hole Tester — Scaled Blocks + Cylinders'

        xyPlane  = comp.xYConstructionPlane
        planes   = comp.constructionPlanes
        extrudes = comp.features.extrudeFeatures

        # offset plane at top of block
        plane_input = planes.createInput()
        plane_input.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(block_thickness_mm * mm_to_cm))
        topPlane = planes.add(plane_input)

        for i in range(count):
            diam_in = start_diam_in + i * step_in
            diam_mm = diam_in * in_to_mm
            radius_cm = (diam_mm * mm_to_cm) / 2.0
            block_side_mm = diam_mm + 2.0 * block_margin_mm
            x_cm = (i * center_pitch_mm) * mm_to_cm

            # block
            block_sketch = comp.sketches.add(xyPlane)
            cx, cy = x_cm, 0.0
            block_sketch.sketchCurves.sketchLines.addCenterPointRectangle(
                adsk.core.Point3D.create(cx, cy, 0),
                adsk.core.Point3D.create(
                    cx + (block_side_mm * mm_to_cm) / 2.0,
                    (block_side_mm * mm_to_cm) / 2.0,
                    0
                )
            )
            block_prof = block_sketch.profiles.item(0)
            blk_ext = extrudes.createInput(block_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            blk_ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(block_thickness_mm * mm_to_cm))
            extrudes.add(blk_ext)

            # cylinder
            cyl_sketch = comp.sketches.add(topPlane)
            cyl_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(cx, cy, 0), radius_cm
            )
            cyl_prof = cyl_sketch.profiles.item(0)
            cyl_ext = extrudes.createInput(cyl_prof, adsk.fusion.FeatureOperations.JoinFeatureOperation)
            cyl_ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cyl_height_mm * mm_to_cm))
            extrudes.add(cyl_ext)

            # optional string hole (through block only)
            if add_string_hole:
                hole_sketch = comp.sketches.add(xyPlane)
                hx = cx + (block_side_mm * mm_to_cm)/2.0 - (hole_edge_offset_mm * mm_to_cm)
                hy = (block_side_mm * mm_to_cm)/2.0 - (hole_edge_offset_mm * mm_to_cm)
                hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(hx, hy, 0),
                    (hole_diam_mm * mm_to_cm)/2.0
                )
                hole_prof = hole_sketch.profiles.item(0)
                cut = extrudes.createInput(hole_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
                cut.setDistanceExtent(False, adsk.core.ValueInput.createByReal(block_thickness_mm * mm_to_cm))
                extrudes.add(cut)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
