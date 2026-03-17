# Preamp-Zener Project

8-channel per-string guitar pickup system with real-time DSP synthesis. 2 unique PCB boards (2 physical) defined in Zener HDL.

## .zen to KiCad Workflow

### 1. Compile .zen files

```bash
pcb build
```

Validates all board definitions, resolves component references, checks electrical rules. Warnings about missing "house" parts (BOM matching) are non-blocking.

### 2. Generate KiCad layout files

```bash
pcb layout --no-open boards/<board>/<board>.zen
```

For each board, this:
- Compiles the .zen source
- Generates a KiCad netlist (`default.net`) in `boards/<board>/layout/`
- Creates `fp-lib-table` mapping footprint library names to `.pretty` directories
- Creates a `layout.kicad_pcb` skeleton and `layout.kicad_pro` project file
- Attempts footprint import via internal lens-based sync

**Known issue:** The internal footprint import fails because the Zener cache stores KiCad 9 format footprints (`version 20241229`) but the system has KiCad 7 (`version 20211014`). The netlist is generated correctly but the PCB file ends up empty.

### 3. Import footprints and auto-place (auto_layout.py)

```bash
python3 auto_layout.py
```

This script bridges the gap left by step 2:
- Parses the `default.net` netlist from each board's `layout/` directory
- Loads footprints from **system** KiCad 7 libraries (`/usr/share/kicad/footprints/`) — NOT the Zener cache which is KiCad 9 format
- Creates a fresh `.kicad_pcb` with all components placed, nets assigned, board outline, and ground copper pours
- Saves to `boards/<board>/layout/layout.kicad_pcb`

### 4. Open in KiCad for routing

```bash
pcb open boards/<board>/<board>.zen
# or directly:
pcbnew boards/<board>/layout/layout.kicad_pcb
```

At this point the board has:
- All footprints placed with initial positions
- Net assignments on pads (ratsnest visible)
- Board outline on Edge.Cuts
- Ground copper pours on F.Cu and B.Cu

Manual or assisted routing is needed for traces.

### 5. Export for manufacturing

```bash
# Gerbers (use kicad-cli, not the MCP tool which fails to write layer files)
kicad-cli pcb export gerbers \
  -l "F.Cu,B.Cu,In1.Cu,In2.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts" \
  -o boards/<board>/layout/gerber/ \
  boards/<board>/layout/layout.kicad_pcb

# Drill files
kicad-cli pcb export drill --format excellon \
  -o boards/<board>/layout/gerber/ \
  boards/<board>/layout/layout.kicad_pcb

# Position/CPL file (for JLCPCB assembly)
kicad-cli pcb export pos --format csv --units mm \
  -o boards/<board>/layout/<board>-cpl.csv \
  boards/<board>/layout/layout.kicad_pcb

# PDF (optional)
kicad-cli pcb export pdf --layers "F.Cu,Edge.Cuts,F.SilkS" \
  --output board.pdf boards/<board>/layout/layout.kicad_pcb
```

### 6. JLCPCB assembly files (BOM + CPL)

JLCPCB requires a **BOM** and **CPL** uploaded separately from the gerber zip. Both files must have matching designators (one row per component, not grouped).

**BOM format** (`<board>-bom.csv`):
```csv
Comment,Designator,Footprint,LCSC
NE5532DR,U1,SOIC-8_3.9x4.9mm_P1.27mm,C7426
```
- `Comment`: MPN or description
- `Designator`: single reference (e.g. `U1`, not `U1,U2,U3`)
- `Footprint`: KiCad footprint name
- `LCSC`: JLCPCB/LCSC part number (e.g. `C7426`)

**CPL format** (`<board>-cpl.csv`):
```csv
Designator,Mid X,Mid Y,Rotation,Layer
U1,30.000000mm,-30.000000mm,0.000000,Top
```
- Coordinates must include `mm` suffix
- Layer must be `Top` or `Bottom` (not `T`/`B` or `top`/`bottom`)
- KiCad's `pos` export uses `Ref,Val,Package,PosX,PosY,Rot,Side` — must be reformatted

**Critical**: BOM and CPL designators must match exactly. Only include SMD parts that JLCPCB can assemble — exclude through-hole connectors, trimpots, jacks, mounting holes. Filter the CPL to only contain designators present in the BOM.

**LCSC part lookup**: Use `https://jlcsearch.tscircuit.com/components/list.json?search=<MPN>&limit=3` (public API, no auth). The `search=` param matches by MPN. For generic passives not stocked by exact MPN, use common JLCPCB basic parts (e.g. UniOhm `0603WAF` resistors, Samsung `CL` capacitors).

## Boards

| Board | .zen source | Components | Layers | Size | Notes |
|-------|------------|------------|--------|------|-------|
| **MAIN** | `boards/main/main.zen` | ~113 | 4 | ~160x80mm | Merged master+ADC+DAC-router+slaves |
| **Preamp/AFE** | `boards/preamp/preamp.zen` | ~151 | 4 | ~100x60mm | Pure analog, 13x NE5532 |

Single cable between boards: Preamp J_OUT -> MAIN J_AFE (2x5, 8 signals + AVDD + AGND).

Previous board sources archived to `archive/` (master, adc, dac-router, slave).

## Ground net names

- **Preamp:** `GND` (single clean analog ground)
- **MAIN:** `AGND` (analog), `DGND` (digital), bridged by ferrite bead FB1

## Project structure

```
boards/
  main/
    main.zen             # MAIN board (merged master+ADC+DAC-router+slaves)
    layout/              # Generated KiCad files
  preamp/
    preamp.zen           # Preamp/AFE board (unchanged)
    layout/              # Generated KiCad files
archive/                 # Previous board sources (master, adc, dac-router, slave)
components/              # Component .zen modules (20 files)
modules/                 # Reusable circuit .zen modules
.pcb/                    # Zener cache and stdlib
auto_layout.py           # Footprint import + auto-placement script
```

## Key tools

- `pcb` CLI (Zener/Diode) — compile, layout, BOM, format
- `pcbnew` Python API (KiCad 7) — footprint loading, board manipulation
- `kicad-cli` — export gerbers, PDFs, SVGs
- KiCad MCP server (`KiCAD-MCP-Server/`) — MCP integration (SWIG backend has known issues with `get_component_list` returning empty)

## Important notes

- Always edit `.zen` files for schematic changes, not KiCad files directly
- The `kicad/` directories under each board are from legacy Python scripts — use `layout/` instead
- System KiCad 7 footprint libraries work; Zener cache footprints (KiCad 9 format) do not load with pcbnew 7
- The KiCad MCP SWIG backend can open boards and run some operations (design rules, copper pours, save) but `get_component_list` returns empty — use pcbnew Python API directly for component queries
