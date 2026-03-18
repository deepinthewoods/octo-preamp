#!/usr/bin/env python3
"""Route digital moat-crossing traces on In1.Cu for the MAIN board.

Routes I2S (MCLK, BCLK, LRCK, ADCDAT_A-D, DACDAT) and I2C (SDA, SCL, SDA2, SCL2)
from x=71 (digital zone) through the moat on In1.Cu to vias near ES8388 pads,
with short F.Cu stubs to the SMD pads.

Via strategy to avoid QFN 0.4mm pitch clearance issues:
  - MCLK vias at x=81.5 (north of QFN), F.Cu stubs go south to top-side pads
  - BCLK vias at x=79.5 (west of QFN), F.Cu stubs go east to top-side pads
  - Left-side pad vias at x=77.5 (single column, 0.8mm y spacing),
    F.Cu stubs go east/diagonal to left-side pads
  - All stubs approach from different directions, avoiding parallel runs at 0.4mm pitch

Digital-side endpoints at x=71 can be connected to ESP32 socket pads later.
"""
import pcbnew

BOARD_PATH = "/media/niz/Samsung SSD/_dev/preamp/preamp-zener/boards/main/layout/layout.kicad_pcb"

TRUNK_W = 0.25   # mm, In1.Cu trace width
STUB_W = 0.2     # mm, F.Cu stub trace width (thinner for QFN 0.4mm pitch clearance)
VIA_SIZE = 0.6   # mm, via pad (JLCPCB standard: 0.3mm drill + 0.15mm annular ring)
VIA_DRILL = 0.3  # mm, via drill (JLCPCB minimum)
ENTRY_X = 71.0   # digital-side stub endpoint (clears J16 slave socket pads at x=70.25)

# Route definitions: (net_name, trunk_y, via_x, via_y, pad_x, pad_y)
#
# Via columns:
#   x=77.5  — left-side pads (LRCK, ADCDAT, SDA/SCL, DACDAT, SDA2/SCL2)
#   x=79.5  — BCLK (east-going stubs to top-side pads)
#   x=81.5  — MCLK (south-going stubs to top-side pads)
#
# All vias in x=77.5 column spaced 0.8mm apart in y (edge clearance > 0.2mm)
# Trunk y spacing >= 0.5mm (0.25mm trace + 0.2mm clearance + margin)

ROUTES = [
    # === U1 area (ES8388 #1, center 82/30.1) ===
    ("MCLK",     27.0,  81.5,  27.0,    81.2,    28.1625),
    ("BCLK",     27.8,  79.5,  28.1625, 80.8,    28.1625),
    ("LRCK",     28.6,  77.5,  28.6,    80.0625, 28.9),
    ("ADCDAT_A", 29.4,  77.5,  29.4,    80.0625, 29.7),
    ("SDA",      30.2,  77.5,  30.2,    80.0625, 30.1),
    ("SCL",      31.0,  77.5,  31.0,    80.0625, 30.5),

    # === U2 area (ES8388 #2, center 82/35.9375) ===
    ("MCLK",     32.8,  81.5,  32.8,    81.2,    34.0),
    ("BCLK",     33.6,  79.5,  34.0,    80.8,    34.0),
    ("LRCK",     34.4,  77.5,  34.4,    80.0625, 34.7375),
    ("ADCDAT_B", 35.2,  77.5,  35.2,    80.0625, 35.5375),
    ("SDA",      36.0,  77.5,  36.0,    80.0625, 35.9375),
    ("SCL",      36.8,  77.5,  36.8,    80.0625, 36.3375),

    # === U3 area (ES8388 #3, center 82/42, has DACDAT + SDA2/SCL2) ===
    ("MCLK",     38.9,  81.5,  38.9,    81.2,    40.0625),
    ("BCLK",     39.5,  79.5,  40.0625, 80.8,    40.0625),
    ("LRCK",     40.0,  77.5,  40.0,    80.0625, 40.8),
    ("DACDAT",   40.8,  77.5,  40.8,    80.0625, 41.2),
    ("ADCDAT_C", 41.6,  77.5,  41.6,    80.0625, 41.6),
    ("SDA2",     42.4,  77.5,  42.4,    80.0625, 42.0),
    ("SCL2",     43.2,  77.5,  43.2,    80.0625, 42.4),

    # === U4 area (ES8388 #4, center 82/47.9375) ===
    ("MCLK",     44.8,  81.5,  44.8,    81.2,    46.0),
    ("BCLK",     45.5,  79.5,  46.0,    80.8,    46.0),
    ("LRCK",     46.3,  77.5,  46.3,    80.0625, 46.7375),
    ("ADCDAT_D", 47.1,  77.5,  47.1,    80.0625, 47.5375),
    ("SDA2",     47.9,  77.5,  47.9,    80.0625, 47.9375),
    ("SCL2",     48.7,  77.5,  48.7,    80.0625, 48.3375),
]


def mm(val):
    return pcbnew.FromMM(val)

def pos(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def main():
    print("Opening MAIN board...")
    board = pcbnew.LoadBoard(BOARD_PATH)
    nets = board.GetNetInfo().NetsByName()

    in1_id = board.GetLayerID("In1.Cu")
    fcu_id = board.GetLayerID("F.Cu")

    routed = 0
    for net_name, trunk_y, via_x, via_y, pad_x, pad_y in ROUTES:
        if not nets.has_key(net_name):
            print(f"  WARNING: net {net_name} not found, skipping")
            continue

        net = nets[net_name]

        # 1. In1.Cu trunk: east from ENTRY_X at trunk_y to via column
        t1 = pcbnew.PCB_TRACK(board)
        t1.SetStart(pos(ENTRY_X, trunk_y))
        t1.SetEnd(pos(via_x, trunk_y))
        t1.SetWidth(mm(TRUNK_W))
        t1.SetLayer(in1_id)
        t1.SetNet(net)
        board.Add(t1)

        # 2. In1.Cu jog from trunk_y to via_y (if different)
        if abs(trunk_y - via_y) > 0.01:
            jog = pcbnew.PCB_TRACK(board)
            jog.SetStart(pos(via_x, trunk_y))
            jog.SetEnd(pos(via_x, via_y))
            jog.SetWidth(mm(TRUNK_W))
            jog.SetLayer(in1_id)
            jog.SetNet(net)
            board.Add(jog)

        # 3. Via at (via_x, via_y)
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pos(via_x, via_y))
        via.SetWidth(mm(VIA_SIZE))
        via.SetDrill(mm(VIA_DRILL))
        via.SetNet(net)
        board.Add(via)

        # 4. F.Cu stub from via to pad
        stub = pcbnew.PCB_TRACK(board)
        stub.SetStart(pos(via_x, via_y))
        stub.SetEnd(pos(pad_x, pad_y))
        stub.SetWidth(mm(STUB_W))
        stub.SetLayer(fcu_id)
        stub.SetNet(net)
        board.Add(stub)

        routed += 1

    print(f"  Routed {routed} moat-crossing traces ({routed} vias, {routed} F.Cu stubs)")
    pcbnew.SaveBoard(BOARD_PATH, board)
    print(f"  Saved: {BOARD_PATH}")


if __name__ == "__main__":
    main()
