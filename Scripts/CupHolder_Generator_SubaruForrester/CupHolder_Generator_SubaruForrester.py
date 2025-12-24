import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        rootComp = design.rootComponent
        userParams = design.userParameters

        # Create new blank component
        occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = 'Cupholder Insert Workspace'

        # Define all parameters
        paramList = [
            ('top_length', 7.625, 'in', 'Top slot length'),
            ('top_width', 3.375, 'in', 'Top slot width'),
            ('bottom_length', 7.25, 'in', 'Bottom slot length'),
            ('bottom_width', 3.0, 'in', 'Bottom slot width'),
            ('insert_height', 5.5, 'in', 'Overall insert height'),
            ('standard_diam', 2.90, 'in', 'Standard can diameter'),
            ('skinny_diam', 2.25, 'in', 'Skinny can diameter'),
            ('cup_center_offset', 1.875, 'in', 'Offset from centerline to cup center'),
            ('cut_depth_standard', 3.0, 'in', 'Cut depth for standard can'),
            ('cut_depth_skinny', 5.5, 'in', 'Cut depth for skinny can')
        ]

        # Add parameters only if they don't already exist
        existing_names = [userParams.item(i).name for i in range(userParams.count)]
        for name, val, units, comment in paramList:
            if name not in existing_names:
                userParams.add(name, adsk.core.ValueInput.createByString(f'{val} {units}'), units, comment)

        ui.messageBox('✅ Parameter workspace created. Safe to sketch using names.')

    except:
        if ui:
            ui.messageBox('❌ Script failed:\n{}'.format(traceback.format_exc()))
