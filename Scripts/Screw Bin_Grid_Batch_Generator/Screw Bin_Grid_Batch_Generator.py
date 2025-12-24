# Gridfinity_Batch_Bins_Only v0.2
# Reads a CSV (your revised schema), opens a template .f3d, sets parameters, saves .f3d, optional .stl.
# No label text is created in this version (pure geometry test).

import adsk.core, adsk.fusion, traceback, csv, os

_app = None
_ui  = None

# Map dropdowns to integer code parameters in your template.
BIN_TYPE_MAP = {'shelled': 0, 'hollow': 1, 'solid': 2}
GRID_TYPE_MAP = {'uniform': 0}  # expand if you add more

# Columns we intentionally ignore (label-related; not used in this bins-only pass)
IGNORE_COLS = {
    'label_text', 'text_height', 'label_height_mm',
    'label_thickness_mm', 'label_align', 'label_margin_mm'
}

def to_bool01(v):
    if v is None: return None
    s = str(v).strip().lower()
    if s in ('1', 'true', 'yes', 'y', 'on'):  return 1
    if s in ('0', 'false', 'no', 'n', 'off'): return 0
    return None

def unit_expr(col, val):
    """Return a Fusion expression string with units when the column name implies mm/deg."""
    s = str(val).strip()
    # numeric?
    try:
        f = float(s)
    except:
        return s  # raw expression (e.g., equations)
    if col.endswith('_mm'):
        return f'{f} mm'
    if col.endswith('_deg'):
        return f'{f} deg'
    # unitless (counts, codes, booleans, _u, etc.)
    return s

def set_if_exists(params, name, expr):
    up = params.itemByName(name)
    if up:
        up.expression = expr
        return True
    return False

def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        # Pick template .f3d
        fd = _ui.createFileDialog()
        fd.title = 'Select Gridfinity TEMPLATE (.f3d)'
        fd.filter = 'Fusion Design (*.f3d)'
        if fd.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        template_path = fd.filename

        # Pick CSV
        cd = _ui.createFileDialog()
        cd.title = 'Select CSV'
        cd.filter = 'CSV Files (*.csv)'
        if cd.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        csv_path = cd.filename

        # Output folder
        od = _ui.createFolderDialog()
        od.title = 'Select output folder'
        if od.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        out_dir = od.folder

        # Read CSV
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))

        for i, row in enumerate(rows, 1):
            name = (row.get('name') or f'bin_{i}').strip()
            doc = _app.documents.open(template_path)
            design = adsk.fusion.Design.cast(
                doc.products.itemByProductType('DesignProductType')
            )
            if not design:
                raise RuntimeError('Design not found in opened document.')
            params = design.userParameters

            # ---- Handle dropdowns first ----
            bt = (row.get('bin_type') or '').strip().lower()
            if bt:
                code = BIN_TYPE_MAP.get(bt)
                if code is None:
                    raise RuntimeError(f'Unknown bin_type "{row.get("bin_type")}". Use Shelled | Hollow | Solid.')
                set_if_exists(params, 'bin_type_code', str(code))

            gt = (row.get('grid_type') or '').strip().lower()
            if gt:
                gcode = GRID_TYPE_MAP.get(gt, 0)
                set_if_exists(params, 'grid_type_code', str(gcode))

            # ---- Set booleans (checkboxes) ----
            bool_fields = [
                'generate_body_bool', 'generate_lip_bool', 'generate_lip_notches_bool',
                'scoop_enable_bool',
                'label_tab_enable_bool',
                'base_enable_bool', 'screw_holes_bool',
                'magnet_sockets_bool', 'magnet_tabs_bool'
            ]
            for b in bool_fields:
                if b in row and row[b] != '':
                    v = to_bool01(row[b])
                    if v is not None:
                        set_if_exists(params, b, str(v))

            # ---- Fix up a couple header quirks from your CSV ----
            # grid_cells_ (typo) -> grid_cells_x
            if row.get('grid_cells_') not in (None, ''):
                set_if_exists(params, 'grid_cells_x', unit_expr('grid_cells_x', row['grid_cells_']))
            # scoop_max_radius (no _mm) -> scoop_max_radius_mm
            if row.get('scoop_max_radius') not in (None, ''):
                set_if_exists(params, 'scoop_max_radius_mm', unit_expr('scoop_max_radius_mm', row['scoop_max_radius']))
            # bin_height_unit_mm provided; try both possible template names
            if row.get('bin_height_unit_mm') not in (None, ''):
                vexpr = unit_expr('bin_height_unit_mm', row['bin_height_unit_mm'])
                if not set_if_exists(params, 'bin_height_unit_mm', vexpr):
                    set_if_exists(params, 'base_height_unit_mm', vexpr)

            # ---- Set all other numeric/unit params that exist and are not ignored ----
            for col, val in row.items():
                if col in IGNORE_COLS:                   # skip label/unused in this pass
                    continue
                if col in ('name', 'bin_type', 'grid_type', 'grid_cells_', 'scoop_max_radius', 'bin_height_unit_mm'):
                    continue
                if val is None or str(val).strip() == '':
                    continue
                if params.itemByName(col):
                    set_if_exists(params, col, unit_expr(col, val))

            design.computeAll()

            # Save native f3d
            doc.name = name
            doc.saveAs(os.path.join(out_dir, f'{name}.f3d'), _app.data.activeProject.rootFolder)

            # Optional STL export if column present
            do_stl = row.get('export_stl', '').strip().lower() in ('1','true','yes','y','on')
            if do_stl:
                exp = _app.exportManager
                opts = exp.createSTLExportOptions(design.rootComponent, os.path.join(out_dir, f'{name}.stl'))
                opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                exp.execute(opts)

            doc.close(False)

        _ui.messageBox('Batch complete (bins only).')

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
