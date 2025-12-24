================================================================================
FACE CENTER POINTS (BODY) - Fusion 360 Add-In
================================================================================

Version:    1.0.0
Author:     Parker
Company:    East Mountain DesignWorks

--------------------------------------------------------------------------------
DESCRIPTION
--------------------------------------------------------------------------------

Face Center Points adds sketch points at the center of selected body faces. 
Useful for creating reference geometry, positioning holes, or establishing 
construction points for downstream features.

--------------------------------------------------------------------------------
FEATURES
--------------------------------------------------------------------------------

- Multi-face selection: Select one or many faces in a single operation
- Three center calculation methods:
    * Parametric center - Fast, works well for regular shapes
    * Bounding box center - Simple geometric center of face bounds
    * Area centroid - Most accurate for irregular/complex shapes
- Sketch organization options:
    * One sketch per face - Clean timeline, easy to edit individually
    * Single consolidated sketch - All points in one sketch
- Construction point toggle - Create as construction geometry if desired

--------------------------------------------------------------------------------
INSTALLATION
--------------------------------------------------------------------------------

1. Download and extract the FaceCenterPoints_Body folder

2. Move the folder to your Fusion 360 Add-Ins directory:

   Mac:
   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns
   
   Windows:
   %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns

3. In Fusion 360:
   - Go to Utilities tab > Add-Ins (or press Shift+S)
   - Click the "Add-Ins" tab
   - Find "Face Center Points (Body)" under My Add-Ins
   - Click "Run"
   - Optionally check "Run on Startup" for automatic loading

--------------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------------

1. Open a design with solid bodies
2. Go to Solid tab > Create panel
3. Click "Face Center Points"
4. Select one or more faces
5. Choose your preferred options:
   - Sketch Organization
   - Center Calculation method
   - Construction points toggle
6. Click OK

--------------------------------------------------------------------------------
TIPS
--------------------------------------------------------------------------------

- For rectangular faces, all three calculation methods give the same result
- For L-shaped or irregular faces, "Area centroid" is most accurate
- Use "One sketch per face" if you need to edit/delete points individually
- Use "Single consolidated sketch" for cleaner timeline with many faces
- Construction points won't interfere with profile detection in sketches

--------------------------------------------------------------------------------
TROUBLESHOOTING
--------------------------------------------------------------------------------

Add-in not appearing in menu:
- Verify folder is in correct Add-Ins location
- Check that .addin and .py filenames match folder name exactly
- Restart Fusion 360

Error on run:
- Ensure you have an active design open
- Make sure you're selecting body faces (not sketch geometry)

Icon not displaying:
- Verify 16x16.png and 32x32.png exist in resources/icons/
- File names must be exactly "16x16.png" and "32x32.png"

--------------------------------------------------------------------------------
VERSION HISTORY
--------------------------------------------------------------------------------

1.0.0 - Initial release
       - Multi-face selection
       - Three center calculation methods
       - Sketch organization options
       - Construction point toggle

--------------------------------------------------------------------------------
LICENSE
--------------------------------------------------------------------------------

See LICENSE.txt for full license terms.

--------------------------------------------------------------------------------
SUPPORT
--------------------------------------------------------------------------------

For bugs, feature requests, or questions:
[your email or contact method]

================================================================================