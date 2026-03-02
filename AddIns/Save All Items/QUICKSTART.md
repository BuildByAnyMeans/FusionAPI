# Quick Start Guide

## Testing the Add-In

### 1. Load the Add-In in Fusion 360

1. Open Fusion 360
2. Go to **Utilities > Add-Ins**
3. Click the **Add-Ins** tab
4. Click the green **+** button next to "My Add-Ins"
5. Navigate to and select this folder: `Save All Items`
6. Click **Select Folder**
7. The add-in should now appear in the list
8. Click **Run** to start the add-in

### 2. Test Basic Functionality

#### Test 1: Export a Single Component
1. In your design, select a component in the browser tree
2. Go to the **Utilities** tab in the toolbar
3. Click **Save All Items**
4. The dialog should show:
   - The component name in the preview table
   - Type: Component
   - Format: 3MF
5. Click the folder icon to select an output folder
6. Click **OK** to export
7. Check the output folder for the exported file

#### Test 2: Export Multiple Bodies
1. In your design, hold Ctrl/Cmd and select multiple bodies in the browser
2. Click **Save All Items**
3. The preview table should list all selected bodies
4. Change the file format to "STL (Binary)" if desired
5. Select output folder and click **OK**
6. Verify all bodies were exported as separate files

#### Test 3: Mixed Selection
1. Select both components and individual bodies
2. Click **Save All Items**
3. Verify the preview shows both types correctly
4. Export and verify files are created properly

### 3. Test Different Formats

Try exporting the same selection in different formats:
- **3MF**: Best for preserving part names (recommended)
- **STL (Binary)**: Compact, good for 3D printing
- **STL (ASCII)**: Text format, larger files
- **OBJ**: Supports texture coordinates

### 4. Test Mesh Refinement

Export the same item with different refinement settings:
- **Low**: Faster export, lower quality mesh
- **Medium**: Balanced (default)
- **High**: Slower export, higher quality mesh

### 5. Verify File Naming

Check that exported files follow the naming convention:
- Saved project: `[ComponentName]_[ProjectName].3mf`
- Unsaved project: `[ComponentName].3mf`
- Invalid characters should be replaced with underscores

## Troubleshooting

### Add-In Won't Load
- Check that all files are in the correct directory structure
- Look for Python syntax errors in the Text Commands window (Fusion 360)
- Verify that the manifest file is valid JSON

### Button Doesn't Appear in Utilities Tab
- Check that `PANEL_ID = 'UtilitiesPanel'` is correct in entry.py
- Try restarting Fusion 360
- Check the Text Commands window for errors

### Export Fails
- Ensure components/bodies are visible (not hidden)
- Check that you have write permissions to the output folder
- Try a different export format
- Check the summary dialog for specific error messages

### Nothing Selected Error
- Make sure you select items in the browser BEFORE clicking the command
- Components and bodies must be selected (not sketches, construction planes, etc.)

## Debug Mode

To enable debug logging:
1. Open `config.py`
2. Ensure `DEBUG = True`
3. Restart the add-in
4. Check **Utilities > Text Commands** window for detailed logs

## Stopping the Add-In

1. Go to **Utilities > Add-Ins**
2. Find "Save All Items" in the list
3. Click **Stop**

To permanently remove:
1. Stop the add-in first
2. Delete the "Save All Items" folder from the Add-Ins directory
