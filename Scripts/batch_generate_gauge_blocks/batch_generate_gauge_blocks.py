import adsk.core, adsk.fusion, adsk.cam, traceback
import csv
import os
import codecs

def run(context):
    try:
        # === BASE PATHS ===
        base_path = '/Users/jpcunnenair/Documents/CAD/Assest_CAD/Dimensional Tools/Gauge Blocks'
        csv_path = os.path.join(base_path, 'GaugeBlock_Creator.csv')
        output_dir = os.path.join(base_path, 'Output')

        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        if not design:
            ui.messageBox('No active Fusion design')
            return

        root_comp = design.rootComponent
        params = design.userParameters
        export_mgr = design.exportManager

        # ✅ Auto-create Output folder if missing
        os.makedirs(output_dir, exist_ok=True)

        with codecs.open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Original label from CSV
                    label = row['label']

                    # Sanitize label for safe filenames and folder names
                    safe_label = label.replace('/', '_').replace('\\', '_')

                    # Read parameter values from CSV
                    length = float(row['length'])
                    width = float(row['width'])
                    thickness = float(row['thickness'])

                    # Set model parameters
                    params.itemByName('length').expression = f"{length} in"
                    params.itemByName('width').expression = f"{width} in"
                    params.itemByName('thickness').expression = f"{thickness} in"

                    # ✅ Create a subfolder for this part
                    block_dir = os.path.join(output_dir, safe_label)
                    os.makedirs(block_dir, exist_ok=True)

                    # Export .f3d
                    f3d_path = os.path.join(block_dir, f"{safe_label}.f3d")
                    fusion_export = export_mgr.createFusionArchiveExportOptions(f3d_path)
                    export_mgr.execute(fusion_export)

                    # Export .STEP
                    step_path = os.path.join(block_dir, f"{safe_label}.step")
                    step_export = export_mgr.createSTEPExportOptions(step_path, root_comp)
                    export_mgr.execute(step_export)

                    print(f"✅ Exported: {label} → {block_dir}")

                except Exception as row_error:
                    print(f"❌ Error processing row {row}: {str(row_error)}")

    except Exception as main_error:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox(f'❌ Script error:\n{str(main_error)}\n{traceback.format_exc()}')
