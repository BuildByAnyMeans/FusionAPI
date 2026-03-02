import adsk.core
import adsk.fusion
import os
import re
import traceback
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

# Command identity information
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_bulkExport'
CMD_NAME = 'Save All Items'
CMD_Description = 'Bulk export selected components and bodies to mesh files'

# Promoted to panel
IS_PROMOTED = True

# Location in the UI
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
# Fallback panel IDs in case the primary one doesn't exist
FALLBACK_PANEL_IDS = ['UtilityPanel', 'SolidMakePanel', 'InsertPanel']
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers
local_handlers = []

# Stores the actual folder path selected by the user (not from UI text which is HTML)
_selected_folder = ''


def _get_panel():
    """Get the toolbar panel, trying multiple IDs for compatibility across Fusion versions."""
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    if not workspace:
        futil.log(f'{CMD_NAME}: Workspace "{WORKSPACE_ID}" not found')
        return None

    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    if panel:
        return panel

    for fallback_id in FALLBACK_PANEL_IDS:
        panel = workspace.toolbarPanels.itemById(fallback_id)
        if panel:
            futil.log(f'{CMD_NAME}: Using fallback panel "{fallback_id}"')
            return panel

    futil.log(f'{CMD_NAME}: No suitable panel found')
    return None


def start():
    """Called when add-in is started"""
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    futil.add_handler(cmd_def.commandCreated, command_created)

    panel = _get_panel()
    if not panel:
        futil.log(f'{CMD_NAME}: Could not find a panel to add command to')
        return

    control = panel.controls.itemById(CMD_ID)
    if not control:
        control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED


def stop():
    """Called when add-in is stopped"""
    panel = _get_panel()
    if panel:
        command_control = panel.controls.itemById(CMD_ID)
        if command_control:
            command_control.deleteMe()

    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    if command_definition:
        command_definition.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    """Called when command is created"""
    futil.log(f'{CMD_NAME} Command Created Event')

    cmd = args.command
    inputs = cmd.commandInputs

    # --- Output group ---
    output_group = inputs.addGroupCommandInput('output_group', 'Output')
    output_group.isExpanded = True
    output_children = output_group.children

    # Selection input — user clicks to select bodies/components
    selection_input = output_children.addSelectionInput(
        'object_selection', 'Objects', 'Select bodies or components to export'
    )
    selection_input.addSelectionFilter('Occurrences')
    selection_input.addSelectionFilter('Bodies')
    selection_input.setSelectionLimits(1, 0)  # min 1, no max

    # Format dropdown
    format_dropdown = output_children.addDropDownCommandInput(
        'file_format', 'Format', adsk.core.DropDownStyles.TextListDropDownStyle
    )
    format_dropdown.listItems.add('3MF', True)
    format_dropdown.listItems.add('STL (Binary)', False)
    format_dropdown.listItems.add('STL (ASCII)', False)
    format_dropdown.listItems.add('OBJ', False)

    # Output folder — browse button + read-only path display
    output_children.addBoolValueInput('browse_folder', 'Output Folder...', False)
    folder_display = output_children.addTextBoxCommandInput(
        'folder_display', 'Folder', '<i>No folder selected</i>', 1, True
    )

    # --- Refinement Settings group ---
    refinement_group = inputs.addGroupCommandInput('refinement_group', 'Refinement Settings')
    refinement_group.isExpanded = False
    refinement_children = refinement_group.children

    refinement_dropdown = refinement_children.addDropDownCommandInput(
        'mesh_refinement', 'Mesh Refinement', adsk.core.DropDownStyles.TextListDropDownStyle
    )
    refinement_dropdown.listItems.add('Low', False)
    refinement_dropdown.listItems.add('Medium', True)
    refinement_dropdown.listItems.add('High', False)

    # --- Options group ---
    options_group = inputs.addGroupCommandInput('options_group', 'Options')
    options_group.isExpanded = False
    options_children = options_group.children

    options_children.addBoolValueInput('open_folder', 'Open folder when done', True, '', True)

    # Connect to events
    futil.add_handler(cmd.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(cmd.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(cmd.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(cmd.destroy, command_destroy, local_handlers=local_handlers)


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    """Called when user changes inputs"""
    changed_input = args.input
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

    if changed_input.id == 'browse_folder':
        global _selected_folder
        folder_dialog = ui.createFolderDialog()
        folder_dialog.title = 'Select Output Folder'
        result = folder_dialog.showDialog()
        if result == adsk.core.DialogResults.DialogOK:
            _selected_folder = folder_dialog.folder
            # Show just the folder name in the UI to avoid overflow
            folder_name = os.path.basename(_selected_folder)
            folder_display = args.inputs.itemById('folder_display')
            folder_display.text = folder_name
            folder_display.tooltip = _selected_folder


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    """Validate inputs before allowing OK"""
    inputs = args.inputs

    # Must have at least one object selected
    selection_input = inputs.itemById('object_selection')
    if selection_input.selectionCount == 0:
        args.areInputsValid = False
        return

    # Must have an output folder selected via browse
    if not _selected_folder:
        args.areInputsValid = False
        return

    args.areInputsValid = True


def command_execute(args: adsk.core.CommandEventArgs):
    """Execute the export"""
    try:
        futil.log(f'{CMD_NAME} Command Execute Event')

        inputs = args.command.commandInputs

        # Gather selected objects
        selection_input = inputs.itemById('object_selection')
        futil.log(f'{CMD_NAME} selection_input: {selection_input}')

        export_items = []
        if selection_input:
            futil.log(f'{CMD_NAME} selectionCount: {selection_input.selectionCount}')
            for i in range(selection_input.selectionCount):
                entity = selection_input.selection(i).entity
                futil.log(f'{CMD_NAME} entity {i}: {type(entity).__name__} - {entity.name}')
                if isinstance(entity, adsk.fusion.Occurrence):
                    export_items.append({'entity': entity, 'name': entity.name, 'type': 'Component'})
                elif isinstance(entity, adsk.fusion.BRepBody):
                    export_items.append({'entity': entity, 'name': entity.name, 'type': 'Body'})
                else:
                    # Catch anything else the selection might return
                    export_items.append({'entity': entity, 'name': entity.name, 'type': 'Unknown'})
                    futil.log(f'{CMD_NAME} WARNING: unexpected entity type: {type(entity).__name__}')

        # Gather settings
        export_folder = _selected_folder
        export_format = inputs.itemById('file_format').selectedItem.name
        mesh_refinement = inputs.itemById('mesh_refinement').selectedItem.name
        open_folder_when_done = inputs.itemById('open_folder').value

        futil.log(f'{CMD_NAME} folder: {export_folder}')
        futil.log(f'{CMD_NAME} format: {export_format}, refinement: {mesh_refinement}')
        futil.log(f'{CMD_NAME} items to export: {len(export_items)}')

        if len(export_items) == 0:
            ui.messageBox('No valid items found to export.\n\nCheck the Text Commands window for details.')
            return

        # Perform export
        perform_bulk_export(export_items, export_folder, export_format, mesh_refinement, open_folder_when_done)

    except Exception:
        ui.messageBox(f'Export command failed:\n\n{traceback.format_exc()}')


def perform_bulk_export(export_items, export_folder, export_format, mesh_refinement, open_folder_when_done):
    """Perform the actual bulk export operation"""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        ui.messageBox('No active design found.')
        return

    # Create output folder if it doesn't exist
    if not os.path.exists(export_folder):
        try:
            os.makedirs(export_folder)
        except OSError as e:
            ui.messageBox(f'Could not create output folder:\n{e}')
            return

    export_manager = design.exportManager
    success_count = 0
    failure_count = 0
    error_messages = []

    # Map refinement to mesh quality enum
    refinement_map = {
        'Low': adsk.fusion.TriangleMeshQualityOptions.LowQualityTriangleMesh,
        'Medium': adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh,
        'High': adsk.fusion.TriangleMeshQualityOptions.HighQualityTriangleMesh
    }
    mesh_quality = refinement_map.get(mesh_refinement, adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh)

    # Export each item
    for item in export_items:
        try:
            entity = item['entity']
            browser_name = item['name']
            item_type = item['type']

            # Build filename
            filename = sanitize_filename(browser_name)

            if export_format == '3MF':
                filename += '.3mf'
            elif export_format.startswith('STL'):
                filename += '.stl'
            elif export_format == 'OBJ':
                filename += '.obj'

            filepath = os.path.join(export_folder, filename)
            futil.log(f'{CMD_NAME} Exporting "{browser_name}" ({item_type}) -> {filepath}')

            # Export
            result = False
            if export_format == '3MF':
                options = export_manager.createC3MFExportOptions(entity, filepath)
                options.meshRefinement = mesh_quality
                result = export_manager.execute(options)
            elif export_format.startswith('STL'):
                options = export_manager.createSTLExportOptions(entity, filepath)
                options.meshRefinement = mesh_quality
                options.isBinaryFormat = ('Binary' in export_format)
                options.sendToPrintUtility = False
                result = export_manager.execute(options)
            elif export_format == 'OBJ':
                options = export_manager.createOBJExportOptions(entity, filepath)
                options.meshRefinement = mesh_quality
                result = export_manager.execute(options)

            if result:
                success_count += 1
                futil.log(f'{CMD_NAME} OK: {filename}')
            else:
                failure_count += 1
                error_messages.append(f'{browser_name}: export returned false')
                futil.log(f'{CMD_NAME} FAIL: {filename} - execute() returned False')

        except Exception as e:
            failure_count += 1
            error_msg = f'{item["name"]}: {str(e)}'
            error_messages.append(error_msg)
            futil.log(f'{CMD_NAME} ERROR: {item["name"]}: {traceback.format_exc()}')

    # Summary
    summary = f'Export Complete\n\nSuccessful: {success_count}\nFailed: {failure_count}'
    summary += f'\nFolder: {export_folder}'
    if error_messages:
        summary += '\n\nErrors:\n' + '\n'.join(error_messages)
    ui.messageBox(summary)

    # Open folder if requested
    if open_folder_when_done and success_count > 0:
        import subprocess
        import platform
        try:
            if platform.system() == 'Darwin':
                subprocess.Popen(['open', export_folder])
            elif platform.system() == 'Windows':
                subprocess.Popen(['explorer', export_folder])
        except Exception:
            pass


def sanitize_filename(name):
    """Sanitize filename to remove invalid characters"""
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '_', name)
    sanitized = sanitized.strip('. ')
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized if sanitized else 'unnamed'


def command_destroy(args: adsk.core.CommandEventArgs):
    """Called when command terminates"""
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers, _selected_folder
    local_handlers = []
    _selected_folder = ''
