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
kicad-cli pcb export gerbers --output ./gerbers/ boards/<board>/layout/layout.kicad_pcb
kicad-cli pcb export drill --output ./gerbers/ boards/<board>/layout/layout.kicad_pcb
kicad-cli pcb export pdf --layers "F.Cu,Edge.Cuts,F.SilkS" --output board.pdf boards/<board>/layout/layout.kicad_pcb
```

## Boards

| Board | .zen source | Components | Layers | Size | Notes |
|-------|------------|------------|--------|------|-------|
| **MAIN** | `boards/main/main.zen` | ~120 | 4 | 200x100mm | Merged master+ADC+DAC-router+slaves |
| **Preamp/AFE** | `boards/preamp/preamp.zen` | 165 | 4 | 160x80mm | Pure analog, unchanged |

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
