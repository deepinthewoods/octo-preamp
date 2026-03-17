#!/usr/bin/env python3
"""Generate JLCPCB BOM and CPL files for main and preamp boards."""

import csv
import io
import re

# LCSC part number mappings based on MPN/value
LCSC_MAP = {
    # ICs
    'NE5532DR': 'C7426',
    'ES8388': 'C365736',
    'LP2985-33DBVR': 'C92497',
    'MCP73831-2-OTI/OT': 'C424093',
    'AP2114H-3.3TRG1': 'C151314',
    'CD4052BM96': 'C6599',
    'HT8988A': 'C5143013',  # kept from existing - no alternative given
    'BAT54': 'C85099',
    # Capacitors by MPN
    'GCM155R71H104KE02D': 'C307331',   # 0402 100nF X7R
    'GRM1555CYA103GE01D': 'C15195',    # 0402 10nF NP0 (used as 10nF in main)
    'GCM1555C1H102FA16D': 'C1546',     # 0402 1nF NP0
    'GRM21BZ71E106KE15K': 'C15850',    # 0805 10uF
    'GRM21BZ71A226ME15K': 'C45783',    # 0805 22uF
    'GCM188R71E105KA64D': 'C15849',    # 0603 1uF
    'GRM188Z71A106KA73D': 'C19702',    # 0603 10uF X5R
    # Resistors by MPN
    'ERJ-2RKF1002X': 'C25744',   # 0402 10k
    'ERJ-2RKF5101X': 'C25905',   # 0402 5.1k
    'ERJ-2RKF1201X': 'C25764',   # 0402 1.2k
    'ERJ-2RKF1001X': 'C11702',   # 0402 1k
    'ERJ-2RKF4701X': 'C25900',   # 0402 4.7k
    'ERJ-2RKF1003X': 'C25741',   # 0402 100k
    'ERJ-2RKF7501X': 'C25890',   # 0402 7.5k
    'ERJ-2RKF1004X': 'C25731',   # 0402 1M
    'ERJ-2RKF6001X': 'C25618',   # 0402 600R (MPN pattern for 600 ohm)
    'ERJ-3EKF4701V': 'C23162',   # 0603 4.7k
    # Ferrite bead
    'BLM21PG221SN1D': 'C1015',   # 0805 ferrite 220 Ohm
    # LED
    'led': 'C72043',             # 0603 LED green
}

# Excluded prefixes (THT hand-solder parts)
EXCLUDED_PREFIXES = ('J', 'RV', 'H')

# For capacitors/resistors with generic "capacitor"/"resistor" val,
# we need to figure out what they are from context.
# Looking at the pos files:
# Main board: C5 "capacitor" 0805, C16/C17 "capacitor" 0805, C19/C20 "capacitor" 0805, C23 "capacitor" 0805
# These are 0805 caps - based on context they are 47uF (the only 0805 value not yet assigned)
MAIN_GENERIC_CAP_0805 = 'C16780'  # 0805 47uF

# Preamp board: C41 "capacitor" 0805 - also 47uF
PREAMP_GENERIC_CAP_0805 = 'C16780'  # 0805 47uF

# Preamp board: R27-R34 "resistor" 0402 - these are 600R based on user context
PREAMP_GENERIC_RES_0402 = 'C25618'  # 0402 600R


def read_pos_file(filepath):
    """Read KiCad pos CSV and return list of dicts."""
    rows = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        # Strip quotes from header
        header = [h.strip('"') for h in header]
        for row in reader:
            if not row:
                continue
            d = {}
            for i, h in enumerate(header):
                d[h] = row[i].strip('"') if i < len(row) else ''
            rows.append(d)
    return rows


def get_lcsc(ref, val, package, board):
    """Get LCSC part number for a component."""
    # Direct MPN match
    if val in LCSC_MAP:
        return val, LCSC_MAP[val]

    # Generic capacitor
    if val == 'capacitor':
        if '0805' in package:
            if board == 'main':
                return '47uF 0805', MAIN_GENERIC_CAP_0805
            else:
                return '47uF 0805', PREAMP_GENERIC_CAP_0805
        return None, None

    # Generic resistor
    if val == 'resistor':
        if '0402' in package:
            return '600R 0402', PREAMP_GENERIC_RES_0402
        return None, None

    # LED
    if val == 'led' or val == 'LED':
        return 'LED GREEN 0603', LCSC_MAP.get('led', None)

    return None, None


def is_excluded(ref):
    """Check if component should be excluded (THT parts)."""
    # Extract prefix letters
    prefix = re.match(r'^([A-Z]+)', ref)
    if prefix:
        return prefix.group(1) in EXCLUDED_PREFIXES
    return False


def generate_bom_cpl(board_name, pos_filepath, bom_outpath, cpl_outpath):
    """Generate BOM and CPL CSV files for a board."""
    rows = read_pos_file(pos_filepath)

    bom_rows = []
    cpl_rows = []

    for r in rows:
        ref = r['Ref']
        val = r['Val']
        package = r['Package']
        posx = r['PosX']
        posy = r['PosY']
        rot = r['Rot']
        side = r['Side']

        # Skip excluded parts
        if is_excluded(ref):
            continue

        # Get LCSC part number
        comment, lcsc = get_lcsc(ref, val, package, board_name)
        if lcsc is None:
            print(f"WARNING: No LCSC match for {ref} val={val} pkg={package}")
            continue

        # Use val as comment if we got a direct match, otherwise use the mapped comment
        if comment is None:
            comment = val

        bom_rows.append({
            'Comment': comment,
            'Designator': ref,
            'Footprint': package,
            'LCSC': lcsc,
        })

        # CPL row
        layer = 'Top' if side.lower() == 'top' else 'Bottom'
        cpl_rows.append({
            'Designator': ref,
            'Mid X': f"{float(posx):.6f}mm",
            'Mid Y': f"{float(posy):.6f}mm",
            'Rotation': rot,
            'Layer': layer,
        })

    # Sort by designator (natural sort)
    def sort_key(row):
        ref = row['Designator']
        prefix = re.match(r'^([A-Z]+)', ref).group(1)
        num = int(re.search(r'(\d+)', ref).group(1))
        return (prefix, num)

    bom_rows.sort(key=sort_key)
    cpl_rows.sort(key=sort_key)

    # Write BOM
    with open(bom_outpath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Comment', 'Designator', 'Footprint', 'LCSC'])
        for row in bom_rows:
            writer.writerow([row['Comment'], row['Designator'], row['Footprint'], row['LCSC']])

    # Write CPL
    with open(cpl_outpath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Designator', 'Mid X', 'Mid Y', 'Rotation', 'Layer'])
        for row in cpl_rows:
            writer.writerow([row['Designator'], row['Mid X'], row['Mid Y'], row['Rotation'], row['Layer']])

    print(f"{board_name}: {len(bom_rows)} BOM entries, {len(cpl_rows)} CPL entries")
    print(f"  -> {bom_outpath}")
    print(f"  -> {cpl_outpath}")


if __name__ == '__main__':
    import os
    base = os.path.dirname(os.path.abspath(__file__))

    generate_bom_cpl(
        'main',
        os.path.join(base, 'boards/main/layout/main-pos.csv'),
        os.path.join(base, 'boards/main/layout/main-bom.csv'),
        os.path.join(base, 'boards/main/layout/main-cpl.csv'),
    )

    generate_bom_cpl(
        'preamp',
        os.path.join(base, 'boards/preamp/layout/preamp-pos.csv'),
        os.path.join(base, 'boards/preamp/layout/preamp-bom.csv'),
        os.path.join(base, 'boards/preamp/layout/preamp-cpl.csv'),
    )
