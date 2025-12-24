import adsk.core
import adsk.fusion
import os
import traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        
        if not design:
            ui.messageBox('No active Fusion 360 design found.')
            return
        
        # Get the configuration table from the design
        configTable = design.configurationTopTable
        
        if not configTable:
            ui.messageBox('No configuration table found in this design.')
            return
        
        # Get all configuration rows
        configRows = configTable.configurationRows
        
        if configRows.count == 0:
            ui.messageBox('No configurations found in the table.')
            return
        
        # Get the folder to save STL files
        folderDlg = ui.createFolderDialog()
        folderDlg.title = 'Select folder to save STL files'
        dlgResult = folderDlg.showDialog()
        
        if dlgResult != adsk.core.DialogResults.DialogOK:
            return
        
        outputFolder = folderDlg.folder
        
        # Store the current configuration to restore later
        originalConfigRow = configTable.activeConfigurationRow
        
        ui.messageBox(f'Found {configRows.count} configurations. Starting export...')
        
        # Get the root component for export
        rootComp = design.rootComponent
        
        # Iterate through each configuration
        successCount = 0
        failedConfigs = []
        
        for i in range(configRows.count):
            try:
                configRow = configRows.item(i)
                
                # Activate this configuration (like double-clicking it)
                configRow.activate()
                
                # Force the design to update
                adsk.doEvents()
                app.activeViewport.refresh()
                
                # Create generic filename: Configuration_1.stl, Configuration_2.stl, etc.
                fileName = f'Configuration_{i + 1}.stl'
                fullPath = os.path.join(outputFolder, fileName)
                
                # Export as STL - export the root component (everything visible)
                exportMgr = design.exportManager
                stlOptions = exportMgr.createSTLExportOptions(rootComp)
                stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
                stlOptions.filename = fullPath
                
                exportMgr.execute(stlOptions)
                successCount += 1
                
            except Exception as e:
                failedConfigs.append(f'Configuration {i + 1}: {str(e)}')
        
        # Restore original configuration
        if originalConfigRow:
            originalConfigRow.activate()
            adsk.doEvents()
            app.activeViewport.refresh()
        
        # Show results
        resultMsg = f'Export complete!\n\nSuccessfully exported {successCount} of {configRows.count} configurations to:\n{outputFolder}'
        
        if len(failedConfigs) > 0:
            resultMsg += f'\n\nFailed exports:\n' + '\n'.join(failedConfigs)
        
        ui.messageBox(resultMsg)
        
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')

def stop(context):
    pass