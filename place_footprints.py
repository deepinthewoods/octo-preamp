#!/usr/bin/env python3
"""Place footprints on KiCad PCBs using pcbnew Python API directly."""

import sys
sys.path.insert(0, "/usr/lib/python3/dist-packages")

import pcbnew

BOARDS_DIR = "/media/niz/Samsung SSD/_dev/preamp/preamp-zener/boards"
FP_DIR = "/usr/share/kicad/footprints"


def load_footprint(lib_name, fp_name):
    """Load a footprint from the KiCad library."""
    lib_path = f"{FP_DIR}/{lib_name}.pretty"
    fp = pcbnew.FootprintLoad(lib_path, fp_name)
    if fp is None:
        raise RuntimeError(f"Could not load {lib_name}:{fp_name}")
    return fp


def place_fp(board, lib_name, fp_name, ref, value, x_mm, y_mm, angle_deg=0, nets=None):
    """Place a footprint on the board at the given position."""
    fp = load_footprint(lib_name, fp_name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
    if angle_deg:
        fp.SetOrientationDegrees(angle_deg)

    # Assign nets to pads
    if nets:
        netinfo = board.GetNetInfo()
        for pad_num, net_name in nets.items():
            net = netinfo.GetNetItem(net_name)
            if net is None:
                # Create net if it doesn't exist
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
                netinfo = board.GetNetInfo()
                net = netinfo.GetNetItem(net_name)
            for pad in fp.Pads():
                if pad.GetNumber() == str(pad_num):
                    pad.SetNet(net)
                    break

    board.Add(fp)
    return fp


def add_mounting_hole(board, x_mm, y_mm, ref, drill_mm=2.2, ground_net="GND"):
    """Add a mounting hole footprint."""
    fp = load_footprint("MountingHole", f"MountingHole_{drill_mm}mm_M{int(drill_mm)}_Pad")
    fp.SetReference(ref)
    fp.SetValue("MountingHole")
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))

    # Assign ground net to pad
    netinfo = board.GetNetInfo()
    net = netinfo.GetNetItem(ground_net)
    if net:
        for pad in fp.Pads():
            pad.SetNet(net)

    board.Add(fp)


def ensure_net(board, name):
    """Ensure a net exists on the board."""
    netinfo = board.GetNetInfo()
    if netinfo.GetNetItem(name) is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)


# =============================================================================
# SLAVE BOARD
# =============================================================================

def build_slave():
    pcb_path = f"{BOARDS_DIR}/slave/kicad/slave.kicad_pcb"
    board = pcbnew.LoadBoard(pcb_path)

    # Ensure all nets exist
    nets = ["VCC_3V3", "GND", "RST", "BCLK", "LRCK", "DOUT", "UART_TX", "UART_RX"]
    for n in nets:
        ensure_net(board, n)

    # J_LEFT: 1x8 pin socket (DevKit left header)
    place_fp(board, "Connector_PinSocket_2.54mm", "PinSocket_1x08_P2.54mm_Vertical",
             "J1", "J_LEFT", 5, 3.5, nets={
                 1: "VCC_3V3", 2: "VCC_3V3", 3: "RST", 4: "",
                 5: "BCLK", 6: "LRCK", 7: "DOUT", 8: ""
             })

    # J_RIGHT: 1x8 pin socket (DevKit right header)
    place_fp(board, "Connector_PinSocket_2.54mm", "PinSocket_1x08_P2.54mm_Vertical",
             "J2", "J_RIGHT", 25, 3.5, nets={
                 1: "GND", 2: "", 3: "", 4: "",
                 5: "", 6: "", 7: "UART_TX", 8: "UART_RX"
             })

    # J_MASTER: 1x8 pin header (to master board)
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical",
             "J3", "J_MASTER", 15, 22, nets={
                 1: "BCLK", 2: "LRCK", 3: "DOUT", 4: "UART_RX",
                 5: "UART_TX", 6: "RST", 7: "VCC_3V3", 8: "GND"
             })

    # Mounting holes (M2, 4 corners)
    add_mounting_hole(board, 2, 2, "H1", drill_mm=2.2, ground_net="GND")
    add_mounting_hole(board, 28, 2, "H2", drill_mm=2.2, ground_net="GND")
    add_mounting_hole(board, 2, 23, "H3", drill_mm=2.2, ground_net="GND")
    add_mounting_hole(board, 28, 23, "H4", drill_mm=2.2, ground_net="GND")

    board.Save(pcb_path)
    print(f"Slave board saved: {pcb_path}")
    print(f"  Components: {len(board.GetFootprints())}")
    print(f"  Nets: {board.GetNetCount()}")


# =============================================================================
# ADC BOARD
# =============================================================================

def build_adc():
    pcb_path = f"{BOARDS_DIR}/adc/kicad/adc.kicad_pcb"
    board = pcbnew.LoadBoard(pcb_path)

    adc_nets = ["AGND", "DGND", "AVDD", "DVDD", "SDA", "SCL",
                "MCLK", "BCLK", "LRCK", "ADCDAT_A", "ADCDAT_B",
                "AD0_HIGH"] + [f"SIG_CH{i}" for i in range(1, 9)]
    for n in adc_nets:
        ensure_net(board, n)

    # J_AFE: 2x5 header from AFE board
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x05_P2.54mm_Vertical",
             "J1", "J_AFE", 10, 15, nets={
                 1: "SIG_CH1", 2: "SIG_CH2", 3: "SIG_CH3", 4: "SIG_CH4",
                 5: "SIG_CH5", 6: "SIG_CH6", 7: "SIG_CH7", 8: "SIG_CH8",
                 9: "AVDD", 10: "AGND"
             })

    # J_MASTER: 2x6 header to master
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x06_P2.54mm_Vertical",
             "J2", "J_MASTER", 40, 15, nets={
                 1: "MCLK", 2: "BCLK", 3: "LRCK", 4: "ADCDAT_A",
                 5: "ADCDAT_B", 6: "SDA", 7: "SCL", 8: "AVDD",
                 9: "DVDD", 10: "AGND", 11: "DGND", 12: ""
             })

    # Mounting holes
    for i, (x, y) in enumerate([(3, 3), (47, 3), (3, 37), (47, 37)]):
        add_mounting_hole(board, x, y, f"H{i+1}", drill_mm=3.2, ground_net="AGND")

    board.Save(pcb_path)
    print(f"ADC board saved: {pcb_path}")
    print(f"  Components: {len(board.GetFootprints())}")


# =============================================================================
# PREAMP (AFE) BOARD
# =============================================================================

def build_preamp():
    pcb_path = f"{BOARDS_DIR}/preamp/kicad/preamp.kicad_pcb"
    board = pcbnew.LoadBoard(pcb_path)

    preamp_nets = ["GND", "AVDD", "VGND"] + \
        [f"PICKUP_{i}" for i in range(1, 9)] + \
        [f"SIGNAL_{i}" for i in range(1, 9)] + \
        [f"DIRECT_OUT_{i}" for i in range(1, 9)]
    for n in preamp_nets:
        ensure_net(board, n)

    # 8x pickup input headers (2-pin each, placed along left edge)
    for i in range(8):
        place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical",
                 f"J_IN{i+1}", f"PICKUP_{i+1}", 5, 10 + i * 10, nets={
                     1: f"PICKUP_{i+1}", 2: "GND"
                 })

    # J_OUT: 2x5 header to ADC board
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x05_P2.54mm_Vertical",
             "J_OUT", "J_OUT", 90, 15, nets={
                 1: "SIGNAL_1", 2: "SIGNAL_2", 3: "SIGNAL_3", 4: "SIGNAL_4",
                 5: "SIGNAL_5", 6: "SIGNAL_6", 7: "SIGNAL_7", 8: "SIGNAL_8",
                 9: "AVDD", 10: "GND"
             })

    # 8x direct output mono jacks (right edge)
    for i in range(8):
        place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical",
                 f"J_DOUT{i+1}", f"DOUT_{i+1}", 90, 30 + i * 8, nets={
                     1: f"DIRECT_OUT_{i+1}", 2: "GND"
                 })

    # J_PWR
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical",
             "J_PWR", "J_PWR", 5, 90, nets={1: "AVDD", 2: "GND"})

    # Mounting holes
    for i, (x, y) in enumerate([(3, 3), (92, 3), (3, 92), (92, 92)]):
        add_mounting_hole(board, x, y, f"H{i+1}", drill_mm=3.2, ground_net="GND")

    board.Save(pcb_path)
    print(f"Preamp board saved: {pcb_path}")
    print(f"  Components: {len(board.GetFootprints())}")


# =============================================================================
# MASTER BOARD
# =============================================================================

def build_master():
    pcb_path = f"{BOARDS_DIR}/master/kicad/master.kicad_pcb"
    board = pcbnew.LoadBoard(pcb_path)

    master_nets = ["DGND", "AGND", "VBUS", "VBAT", "AVDD_3V3", "DVDD_3V3",
                   "MCLK", "BCLK", "LRCK", "ADCDAT_A", "ADCDAT_B",
                   "SDA", "SCL", "TX_SLAVE", "RX_SLAVE",
                   "BCLK_OUT", "LRCK_OUT", "DIN_A", "DIN_B", "DIN_C",
                   "DOUT_DAC", "MUX_A", "MUX_B", "MUX_INH",
                   "EN_SLAVE2", "EN_SLAVE3", "EN_SLAVE4"]
    for n in master_nets:
        ensure_net(board, n)

    # DevKit headers (2x 1x20 pin sockets) along top edge
    place_fp(board, "Connector_PinSocket_2.54mm", "PinSocket_1x20_P2.54mm_Vertical",
             "J_L", "DevKit_Left", 15, 5)
    place_fp(board, "Connector_PinSocket_2.54mm", "PinSocket_1x20_P2.54mm_Vertical",
             "J_R", "DevKit_Right", 35, 5)

    # J_ADC: 2x6 header
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x06_P2.54mm_Vertical",
             "J_ADC", "J_ADC", 65, 10, nets={
                 1: "MCLK", 2: "BCLK", 3: "LRCK", 4: "ADCDAT_A",
                 5: "ADCDAT_B", 6: "SDA", 7: "SCL", 8: "AVDD_3V3",
                 9: "DVDD_3V3", 10: "AGND", 11: "DGND", 12: ""
             })

    # Slave connectors (1x8 each)
    for idx, (name, din, en, y) in enumerate([
        ("J_SLA", "DIN_A", "EN_SLAVE2", 30),
        ("J_SLB", "DIN_B", "EN_SLAVE3", 40),
        ("J_SLC", "DIN_C", "EN_SLAVE4", 50),
    ]):
        place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x08_P2.54mm_Vertical",
                 name, f"J_SLAVE_{chr(65+idx)}", 65, y, nets={
                     1: "BCLK_OUT", 2: "LRCK_OUT", 3: din, 4: "TX_SLAVE",
                     5: "RX_SLAVE", 6: en, 7: "DVDD_3V3", 8: "DGND"
                 })

    # J_DAC: 2x5 header
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x05_P2.54mm_Vertical",
             "J_DAC", "J_DAC", 65, 55, nets={
                 1: "DOUT_DAC", 2: "MUX_A", 3: "MUX_B", 4: "MUX_INH",
                 5: "AVDD_3V3", 6: "DVDD_3V3", 7: "AGND", 8: "DGND",
                 9: "", 10: ""
             })

    # Mounting holes
    for i, (x, y) in enumerate([(3, 3), (77, 3), (3, 57), (77, 57)]):
        add_mounting_hole(board, x, y, f"H{i+1}", drill_mm=3.2, ground_net="DGND")

    board.Save(pcb_path)
    print(f"Master board saved: {pcb_path}")
    print(f"  Components: {len(board.GetFootprints())}")


# =============================================================================
# DAC-ROUTER BOARD
# =============================================================================

def build_dac_router():
    pcb_path = f"{BOARDS_DIR}/dac-router/kicad/dac_router.kicad_pcb"
    board = pcbnew.LoadBoard(pcb_path)

    dr_nets = ["AGND", "DGND", "AVDD", "DVDD", "DOUT_DAC",
               "MUX_A", "MUX_B", "MUX_INH",
               "JACK_L_TIP", "JACK_R_TIP"] + \
              [f"DRY_CH{i}" for i in range(1, 9)]
    for n in dr_nets:
        ensure_net(board, n)

    # J_MASTER: 2x5 header
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x05_P2.54mm_Vertical",
             "J_MASTER", "J_MASTER", 10, 15, nets={
                 1: "DOUT_DAC", 2: "MUX_A", 3: "MUX_B", 4: "MUX_INH",
                 5: "AVDD", 6: "DVDD", 7: "AGND", 8: "DGND",
                 9: "", 10: ""
             })

    # J_AFE: 2x5 header for dry signals
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_2x05_P2.54mm_Vertical",
             "J_AFE", "J_AFE", 10, 35, nets={
                 1: "DRY_CH1", 2: "DRY_CH2", 3: "DRY_CH3", 4: "DRY_CH4",
                 5: "DRY_CH5", 6: "DRY_CH6", 7: "DRY_CH7", 8: "DRY_CH8",
                 9: "AVDD", 10: "AGND"
             })

    # TRS output jacks (placeholder 1x3 headers)
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical",
             "J_OUT_L", "TRS_L", 60, 15, nets={
                 1: "JACK_L_TIP", 2: "", 3: "AGND"
             })
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x03_P2.54mm_Vertical",
             "J_OUT_R", "TRS_R", 60, 30, nets={
                 1: "JACK_R_TIP", 2: "", 3: "AGND"
             })

    # Footswitch connectors
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical",
             "J_FS1", "FS1", 60, 40)
    place_fp(board, "Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical",
             "J_FS2", "FS2", 60, 45)

    # Mounting holes
    for i, (x, y) in enumerate([(3, 3), (67, 3), (3, 47), (67, 47)]):
        add_mounting_hole(board, x, y, f"H{i+1}", drill_mm=3.2, ground_net="AGND")

    board.Save(pcb_path)
    print(f"DAC-Router board saved: {pcb_path}")
    print(f"  Components: {len(board.GetFootprints())}")


# =============================================================================
# Build all
# =============================================================================

if __name__ == "__main__":
    print("Placing footprints on all 5 boards...\n")
    build_slave()
    print()
    build_adc()
    print()
    build_preamp()
    print()
    build_master()
    print()
    build_dac_router()
    print("\nDone!")
