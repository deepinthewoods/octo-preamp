#!/usr/bin/env python3
"""Route digital moat-crossing traces on the MAIN board.

Noise-optimized routing strategy (v2):
  1. I2S clocks (MCLK, BCLK, LRCK) cross the moat ONCE each, then fan out
     via vertical backbones to all 4 ES8388s (was 12 crossings, now 3)
  2. I2C signals (SDA, SCL, SDA2, SCL2) routed on In2.Cu to physically
     separate from I2S clocks/data on In1.Cu
  3. DGND ground guard traces on In1.Cu between signal groups
  4. DGND stitching vias along moat boundary for low-impedance return path
  5. ADC data and MUX control use individual trunks on In1.Cu (unchanged topology)

Clock trunks enter at y=26.0-27.0 (above all data trunks) to avoid crossing
the vertical backbones of other clocks. Backbone x columns are staggered:
  LRCK at x=78.5, BCLK at x=79.5, MCLK at x=81.5
so no horizontal trunk crosses another clock's backbone.

Digital-side endpoints at x=71 connect to ESP32 socket pads (routed separately).
"""
import pcbnew

BOARD_PATH = "/media/niz/Samsung SSD/_dev/preamp/preamp-zener/boards/main/layout/layout.kicad_pcb"

TRUNK_W = 0.25   # mm, inner-layer trunk width
STUB_W = 0.2     # mm, F.Cu stub width (thinner for QFN pitch clearance)
GUARD_W = 0.25   # mm, guard trace width
VIA_SIZE = 0.6   # mm, via pad diameter
VIA_DRILL = 0.3  # mm, via drill
ENTRY_X = 71.0   # digital-side entry point


def mm(val):
    return pcbnew.FromMM(val)

def pos(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))

def add_trace(board, net, layer_id, x1, y1, x2, y2, width):
    """Add a single PCB track segment."""
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pos(x1, y1))
    t.SetEnd(pos(x2, y2))
    t.SetWidth(mm(width))
    t.SetLayer(layer_id)
    t.SetNet(net)
    board.Add(t)

def add_via(board, net, x, y):
    """Add a through via."""
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pos(x, y))
    v.SetWidth(mm(VIA_SIZE))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNet(net)
    board.Add(v)

def route_individual(board, net, layer_id, fcu_id, trunk_y, via_x, via_y, pad_x, pad_y):
    """Route a single trunk+via+stub chain (used for data and MUX signals)."""
    # Trunk: horizontal from entry to via column
    add_trace(board, net, layer_id, ENTRY_X, trunk_y, via_x, trunk_y, TRUNK_W)
    # Jog from trunk_y to via_y if needed
    if abs(trunk_y - via_y) > 0.01:
        add_trace(board, net, layer_id, via_x, trunk_y, via_x, via_y, TRUNK_W)
    # Via
    add_via(board, net, via_x, via_y)
    # F.Cu stub to pad
    add_trace(board, net, fcu_id, via_x, via_y, pad_x, pad_y, STUB_W)


def main():
    print("Opening MAIN board...")
    board = pcbnew.LoadBoard(BOARD_PATH)
    nets = board.GetNetInfo().NetsByName()

    in1 = board.GetLayerID("In1.Cu")
    in2 = board.GetLayerID("In2.Cu")
    fcu = board.GetLayerID("F.Cu")

    count = 0

    # =====================================================================
    # 1. I2S CLOCK FAN-OUT (In1.Cu)
    #
    # Single trunk per clock crosses moat at y<28 (above data trunks),
    # then a vertical backbone distributes to 4 ES8388 vias.
    # Backbone x columns: MCLK=81.5, BCLK=79.5, LRCK=78.5
    # =====================================================================

    CLOCK_FANOUTS = [
        # (net, trunk_y, backbone_x, [(via_y, pad_x, pad_y), ...])
        ("MCLK", 26.0, 81.5, [
            (27.0,  81.2,  28.1625),  # U1
            (32.8,  81.2,  34.0),     # U2
            (38.9,  81.2,  40.0625),  # U3
            (44.8,  81.2,  46.0),     # U4
        ]),
        ("BCLK", 26.5, 79.5, [
            (28.1625, 80.8, 28.1625), # U1
            (34.0,    80.8, 34.0),    # U2
            (40.0625, 80.8, 40.0625), # U3
            (46.0,    80.8, 46.0),    # U4
        ]),
        ("LRCK", 27.0, 78.5, [
            (28.6,  80.0625, 28.9),    # U1
            (34.4,  80.0625, 34.7375), # U2
            (40.0,  80.0625, 40.8),    # U3
            (46.3,  80.0625, 46.7375), # U4
        ]),
    ]

    for net_name, trunk_y, backbone_x, branches in CLOCK_FANOUTS:
        if not nets.has_key(net_name):
            print(f"  WARNING: net {net_name} not found, skipping")
            continue
        net = nets[net_name]

        # Horizontal trunk from digital zone to backbone column
        add_trace(board, net, in1, ENTRY_X, trunk_y, backbone_x, trunk_y, TRUNK_W)

        # Vertical backbone spanning all branch via positions
        via_ys = sorted([vy for vy, _, _ in branches])
        backbone_top = min(trunk_y, via_ys[0])
        backbone_bot = max(trunk_y, via_ys[-1])
        add_trace(board, net, in1, backbone_x, backbone_top, backbone_x, backbone_bot, TRUNK_W)

        # Vias + F.Cu stubs at each ES8388
        for via_y, pad_x, pad_y in branches:
            add_via(board, net, backbone_x, via_y)
            add_trace(board, net, fcu, backbone_x, via_y, pad_x, pad_y, STUB_W)
            count += 1

    print(f"  Clock fan-out: 3 trunks, {count} vias+stubs")

    # =====================================================================
    # 2. ADC DATA TRUNKS (In1.Cu, individual)
    #
    # Each ADCDAT line goes to one ES8388 — no fan-out needed.
    # DACDAT goes to ES8388 #3 only.
    # =====================================================================

    DATA_ROUTES = [
        # (net, trunk_y, via_x, via_y, pad_x, pad_y)
        ("ADCDAT_A", 29.4,  77.5, 29.4,  80.0625, 29.7),      # U1
        ("ADCDAT_B", 35.2,  77.5, 35.2,  80.0625, 35.5375),   # U2
        ("DACDAT",   40.8,  77.5, 40.8,  80.0625, 41.2),      # U3
        ("ADCDAT_C", 41.6,  77.5, 41.6,  80.0625, 41.6),      # U3
        ("ADCDAT_D", 47.1,  77.5, 47.1,  80.0625, 47.5375),   # U4
    ]

    data_count = 0
    for net_name, trunk_y, via_x, via_y, pad_x, pad_y in DATA_ROUTES:
        if not nets.has_key(net_name):
            print(f"  WARNING: net {net_name} not found, skipping")
            continue
        route_individual(board, nets[net_name], in1, fcu, trunk_y, via_x, via_y, pad_x, pad_y)
        data_count += 1
        count += 1

    print(f"  Data trunks: {data_count} individual routes on In1.Cu")

    # =====================================================================
    # 3. I2C ROUTES (In2.Cu — separate layer from I2S)
    #
    # Routed on In2.Cu to physically isolate from I2S clocks/data on In1.Cu.
    # Each line gets an individual trunk (no fan-out — cleaner routing).
    # Via columns: SDA at x=76.5, SCL at x=75.5 (staggered for clearance).
    # =====================================================================

    I2C_ROUTES = [
        # (net, trunk_y, via_x, via_y, pad_x, pad_y)
        # Bus 0 — U1 (ES8388 #1)
        ("SDA",  30.2,  76.5, 30.2,  80.0625, 30.1),
        ("SCL",  31.0,  75.5, 31.0,  80.0625, 30.5),
        # Bus 0 — U2 (ES8388 #2)
        ("SDA",  36.0,  76.5, 36.0,  80.0625, 35.9375),
        ("SCL",  36.8,  75.5, 36.8,  80.0625, 36.3375),
        # Bus 1 — U3 (ES8388 #3)
        ("SDA2", 42.4,  76.5, 42.4,  80.0625, 42.0),
        ("SCL2", 43.2,  75.5, 43.2,  80.0625, 42.4),
        # Bus 1 — U4 (ES8388 #4)
        ("SDA2", 47.9,  76.5, 47.9,  80.0625, 47.9375),
        ("SCL2", 48.7,  75.5, 48.7,  80.0625, 48.3375),
    ]

    i2c_count = 0
    for net_name, trunk_y, via_x, via_y, pad_x, pad_y in I2C_ROUTES:
        if not nets.has_key(net_name):
            print(f"  WARNING: net {net_name} not found, skipping")
            continue
        route_individual(board, nets[net_name], in2, fcu, trunk_y, via_x, via_y, pad_x, pad_y)
        i2c_count += 1
        count += 1

    print(f"  I2C routes: {i2c_count} individual routes on In2.Cu")

    # =====================================================================
    # 4. MUX CONTROL ROUTES (In1.Cu, individual)
    #
    # MUX signals are slow GPIO — kept as individual trunks.
    # =====================================================================

    MUX_ROUTES = [
        # (net, trunk_y, via_x, via_y, pad_x, pad_y)
        # U9 (CD4052B mux #1, center ~83/58.6)
        ("MUX_INH", 60.5,  77.5, 60.5,  80.5,  60.5),
        ("MUX_A",   61.77, 87.0, 61.77, 85.45, 61.77),
        ("MUX_B",   63.04, 88.0, 63.04, 85.45, 63.04),
        # U10 (CD4052B mux #2, center ~83/70.6)
        ("MUX_INH", 72.5,  77.5, 72.5,  80.5,  72.5),
        ("MUX_A",   73.77, 87.0, 73.77, 85.45, 73.77),
        ("MUX_B",   75.04, 88.0, 75.04, 85.45, 75.04),
    ]

    mux_count = 0
    for net_name, trunk_y, via_x, via_y, pad_x, pad_y in MUX_ROUTES:
        if not nets.has_key(net_name):
            print(f"  WARNING: net {net_name} not found, skipping")
            continue
        route_individual(board, nets[net_name], in1, fcu, trunk_y, via_x, via_y, pad_x, pad_y)
        mux_count += 1
        count += 1

    print(f"  MUX routes: {mux_count} individual routes on In1.Cu")

    # =====================================================================
    # 5. GROUND GUARD TRACES (In1.Cu, DGND)
    #
    # Explicit DGND traces between signal groups ensure continuous ground
    # reference even where the DGND corridor pour is slotted by signal traces.
    # =====================================================================

    if not nets.has_key("DGND"):
        print("  WARNING: DGND net not found, skipping guard traces and stitching")
    else:
        dgnd = nets["DGND"]

        GUARD_TRACES = [
            # (y, x_start, x_end) — horizontal DGND guard traces
            (25.0, ENTRY_X, 77.5),   # above clock trunks (top boundary)
            (28.0, ENTRY_X, 77.5),   # between clocks (y≤27) and data (y≥29.4)
            (33.0, ENTRY_X, 77.5),   # between U1 data group and U2 data group
            (38.5, ENTRY_X, 77.5),   # between U2 group and U3 group
            (44.5, ENTRY_X, 77.5),   # between U3 group and U4 group
            (49.5, ENTRY_X, 77.5),   # below U4 data group
        ]

        guard_count = 0
        for y, x1, x2 in GUARD_TRACES:
            add_trace(board, dgnd, in1, x1, y, x2, y, GUARD_W)
            guard_count += 1

        print(f"  Guard traces: {guard_count} DGND traces on In1.Cu")

        # =================================================================
        # 6. DGND STITCHING VIAS (moat boundary)
        #
        # Row of through vias at x=74.5 (just inside digital zone where
        # F.Cu, In1.Cu, and B.Cu all have DGND pours). Creates a low-
        # impedance ground wall at the moat entry for digital return currents.
        #
        # Y positions chosen to maintain ≥0.625mm clearance from all signal
        # trunks on In1.Cu and In2.Cu.
        # =================================================================

        STITCH_VIA_YS = [
            25.0,   # above clock trunks
            32.0,   # between U1 and U2 I2C groups
            38.0,   # gap between bus 0 and bus 1 regions
            39.5,   # still in the large gap
            44.2,   # between U3 I2C and U4 I2C
            50.0,   # below all ES8388 routes
            53.0,   # open zone
            56.0,   # open zone
            59.0,   # just above MUX region
            65.0,   # between MUX #1 and MUX #2
            68.0,   # open zone
            71.0,   # just above MUX #2
            76.5,   # below all MUX routes
        ]

        stitch_count = 0
        for y in STITCH_VIA_YS:
            add_via(board, dgnd, 74.5, y)
            stitch_count += 1

        print(f"  Stitching vias: {stitch_count} DGND vias at x=74.5")

    total = count + guard_count + stitch_count if nets.has_key("DGND") else count
    print(f"  Total: {total} elements routed")
    pcbnew.SaveBoard(BOARD_PATH, board)
    print(f"  Saved: {BOARD_PATH}")


if __name__ == "__main__":
    main()
