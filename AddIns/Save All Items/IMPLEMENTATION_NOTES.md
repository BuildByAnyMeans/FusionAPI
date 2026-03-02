# Implementation Notes

## What Was Built

This is a complete Fusion 360 Add-In that enables bulk export of selected components and bodies to mesh files while preserving browser names.

### Core Features Implemented

1. **Selection Handling**
   - Supports Occurrence (component instances) selection
   - Supports BRepBody (individual body) selection
   - Supports Component selection (converted to Occurrence)
   - Handles mixed selections (components + bodies together)

2. **Export Formats**
   - **3MF**: Full support with internal part name preservation
   - **STL (Binary)**: Optimized file size
   - **STL (ASCII)**: Text format for compatibility
   - **OBJ**: Industry standard mesh format

3. **UI Components**
   - Interactive table showing selection preview
   - Folder browser for output directory selection
   - Format dropdown with 4 export options
   - Mesh refinement selector (Low/Medium/High)
   - "Open folder when done" checkbox

4. **File Naming**
   - Pattern: `[BrowserName]_[ProjectName].[ext]`
   - Handles unsaved documents (omits project name)
   - Sanitizes filenames for Windows/macOS compatibility
   - Removes invalid characters: `< > : " / \ | ? *`
   - Limits filename length to 200 characters

5. **Error Handling**
   - Try-catch around each export operation
   - Continues processing if one item fails
   - Shows detailed summary with success/failure counts
   - Logs specific error messages for debugging

## File Structure

```
Save All Items/
├── Save All Items.py              # Main entry point
├── Save All Items.manifest         # Add-in metadata
├── config.py                       # Configuration settings
├── README.md                       # User documentation
├── QUICKSTART.md                   # Testing guide
├── IMPLEMENTATION_NOTES.md         # This file
├── AddInIcon.svg                   # Add-in icon
├── lib/
│   └── fusionAddInUtils/          # Utility library
│       ├── __init__.py
│       ├── event_utils.py
│       └── general_utils.py
├── commands/
│   ├── __init__.py                # Command registration
│   └── bulkExport/                # Main export command
│       ├── __init__.py
│       ├── entry.py               # Command implementation
│       └── resources/             # Command icons
│           ├── 16x16.png
│           ├── 32x32.png
│           └── 64x64.png
└── resources/
    ├── 16x16.png                  # Add-in icons
    └── 32x32.png
```

## Technical Implementation Details

### 3MF Export
The 3MF format is the recommended export format because it:
- Preserves multiple part names within a single file
- Supports complex assemblies with nested components
- Maintains the browser tree structure internally
- Opens in slicers/CAM software with named parts

Implementation uses `createC3MFExportOptions()` which accepts:
- Occurrence objects (for components)
- BRepBody objects (for individual bodies)

### STL Export
STL format limitations:
- Single mesh per file (no internal part names)
- Components export as flattened single mesh
- Bodies export individually

Implementation uses `createSTLExportOptions()` with:
- Binary/ASCII format selection
- Mesh refinement quality
- `sendToPrintUtility = False` to prevent auto-opening

### OBJ Export
OBJ format characteristics:
- Supports material/texture definitions
- Good for rendering applications
- Limited part name preservation

Implementation uses `createOBJExportOptions()` with mesh refinement settings.

### Mesh Refinement Mapping
```python
'Low'    -> TriangleMeshQualityOptions.LowQualityTriangleMesh
'Medium' -> TriangleMeshQualityOptions.MediumQualityTriangleMesh
'High'   -> TriangleMeshQualityOptions.HighQualityTriangleMesh
```

## Known Limitations

1. **Units**: Exported meshes use the document's current unit settings. There is no runtime unit conversion during export.

2. **Component Selection**: When a Component is selected (not an Occurrence), the code finds the corresponding Occurrence in the design. This works for root components but may have edge cases with deeply nested structures.

3. **Hidden Bodies**: Only visible bodies are exported. Hidden bodies in components are skipped.

4. **Platform Differences**: Folder opening after export uses different commands on macOS vs Windows. Linux is not currently supported for the folder opening feature.

5. **Format Limitations**:
   - STL and OBJ don't preserve multiple part names like 3MF does
   - For components with multiple bodies, these formats flatten to a single mesh

## Future Enhancement Opportunities

1. **Progress Feedback**: Add progress bar for large export operations
2. **Batch Processing**: Allow saving/loading selection sets
3. **Advanced Naming**: Template-based filename patterns
4. **Unit Conversion**: Runtime mesh scaling for unit conversion
5. **Export Presets**: Save commonly used export configurations
6. **Incremental Export**: Only export changed items
7. **Material Export**: Include material assignments in formats that support it (OBJ/MTL)
8. **Validation**: Pre-export mesh validation and repair
9. **Export Queue**: Background export with notification on completion
10. **Cloud Upload**: Direct export to cloud storage services

## Debugging

Enable debug mode in [config.py](config.py#L11):
```python
DEBUG = True
```

This provides verbose logging in Fusion 360's Text Commands window, including:
- Command lifecycle events
- Input validation results
- Export operation details
- Error stack traces

## API References

Key Fusion 360 API objects used:
- `adsk.fusion.Design` - Main design object
- `adsk.fusion.ExportManager` - Export operations
- `adsk.fusion.Occurrence` - Component instances
- `adsk.fusion.BRepBody` - Solid/surface bodies
- `adsk.core.CommandInput` - Dialog UI elements
- `adsk.core.TableCommandInput` - Selection preview table

## Version History

### 1.0.0 (Initial Release)
- Basic export functionality for 3MF, STL, OBJ formats
- Selection preview table
- File naming with project name
- Error handling and summary reporting
- Mesh refinement options
- Open folder on completion
