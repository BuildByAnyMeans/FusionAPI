# Save All Items - Fusion 360 Add-In

## Overview
Bulk export selected components and/or bodies from the Fusion 360 design browser to mesh files, preserving their names — something Fusion's native bulk export doesn't do.

## Features

### Export Logic
- **Components**: Export as a single file containing all bodies/sub-components with internal part names retained
- **Bodies**: Export individual bodies as separate files
- **Mixed Selections**: Supports exporting both components and bodies in the same operation
- **Nested Components**: Flattens everything under the selected component into one export file while preserving all sub-component and sub-body names internally

### Supported Formats
- **3MF** (recommended - preserves internal part names)
- **STL (Binary)**
- **STL (ASCII)**
- **OBJ**

### File Naming Convention
Files are named using the pattern: `[BrowserName]_[ProjectName].[ext]`

- **BrowserName**: The name exactly as shown in the Fusion browser tree
- **ProjectName**: The Fusion project/document name (if saved)
- For unsaved files, only the BrowserName is used (no underscore or project suffix)
- Invalid filename characters are automatically sanitized

### UI Features
- **Selection Preview Table**: Shows all items to be exported with name, type (component/body), and format
- **Output Folder Picker**: Browse and select destination folder
- **File Format Dropdown**: Choose export format (default: 3MF)
- **Mesh Refinement**: Choose quality - Low, Medium, High (default: Medium)
- **Open Folder When Done**: Automatically open the export folder after completion (default: checked)

**Note**: Exported meshes use the document's current unit settings. You can change the document units in Fusion 360 before exporting if needed.

## Usage

1. Select components and/or bodies in the Fusion 360 browser
2. Click the "Save All Items" button in the Utilities tab
3. Review the selection preview table
4. Choose output folder and export settings
5. Click OK to export

## Error Handling
- If one item fails to export, the add-in logs the error and continues with remaining items
- A summary is shown at completion with success/failure counts and error details

## Installation

1. Copy this folder to your Fusion 360 Add-Ins directory:
   - **Windows**: `%AppData%\Autodesk\Autodesk Fusion 360\API\AddIns`
   - **macOS**: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`

2. In Fusion 360, go to **Utilities > Add-Ins**
3. Select the "Save All Items" add-in and click "Run"

## Technical Details

- Uses Fusion 360 native mesh export APIs
- No external Python dependencies required
- Compatible with Windows and macOS
- Toolbar button placed in Utilities tab

## Version
1.0.0
