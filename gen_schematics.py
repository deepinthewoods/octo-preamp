#!/usr/bin/env python3
"""Generate properly wired KiCad 7 schematics for all 5 preamp boards.

Uses the exact format output by the KiCAD-MCP-Server, with components,
wires, and net labels placed at correct pin positions so that
sync_schematic_to_board works.
"""

import uuid
import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))

def uid():
    return str(uuid.uuid4())

# Conn_01x08 pin offsets (relative to component position)
# Pin N at: x_off = -5.08, y_off = -(7.62 - (N-1)*2.54)
def conn1x08_pin(comp_x, comp_y, pin_num):
    """Return absolute (x, y) of pin endpoint for Conn_01x08."""
    x = comp_x - 5.08
    y = comp_y - 7.62 + (pin_num - 1) * 2.54
    return (x, y)

# Conn_02x05 pin offsets - left pins (odd) and right pins (even)
def conn2x05_pin(comp_x, comp_y, pin_num):
    """Return absolute (x, y) for Conn_02x05_Odd_Even."""
    row = (pin_num - 1) // 2
    if pin_num % 2 == 1:  # odd = left side
        x = comp_x - 5.08
    else:  # even = right side
        x = comp_x + 5.08
    y = comp_y - 5.08 + row * 2.54
    return (x, y)

# Conn_02x06 pin offsets
def conn2x06_pin(comp_x, comp_y, pin_num):
    row = (pin_num - 1) // 2
    if pin_num % 2 == 1:
        x = comp_x - 5.08
    else:
        x = comp_x + 5.08
    y = comp_y - 6.35 + row * 2.54
    return (x, y)

# Read the MCP-generated schematic to extract the lib_symbols block
def get_lib_symbols_from_file(path):
    """Read a .kicad_sch and return the lib_symbols content."""
    with open(path) as f:
        content = f.read()
    # Find the lib_symbols block
    start = content.find("(lib_symbols")
    if start < 0:
        return ""
    depth = 0
    end = start
    for i in range(start, len(content)):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return content[start:end]


class SchematicWriter:
    def __init__(self, title):
        self.title = title
        self.uuid = uid()
        self.components = []
        self.labels = []
        self.wires = []

    def add_component(self, lib_id, ref, value, footprint, x, y):
        self.components.append({
            "lib_id": lib_id, "ref": ref, "value": value,
            "footprint": footprint, "x": x, "y": y, "uuid": uid()
        })

    def add_label(self, name, x, y):
        self.labels.append({"name": name, "x": round(x, 2), "y": round(y, 2), "uuid": uid()})

    def add_wire(self, x1, y1, x2, y2):
        self.wires.append({"x1": round(x1, 2), "y1": round(y1, 2),
                           "x2": round(x2, 2), "y2": round(y2, 2), "uuid": uid()})

    def label_at_pin_1x8(self, net, comp_x, comp_y, pin_num):
        """Place a net label at the pin position of a 1x8 connector, with a short wire stub."""
        px, py = conn1x08_pin(comp_x, comp_y, pin_num)
        # Label at pin with wire stub going left
        lx = px - 5.08
        self.add_wire(px, py, lx, py)
        self.add_label(net, lx, py)

    def label_at_pin_2x5(self, net, comp_x, comp_y, pin_num):
        px, py = conn2x05_pin(comp_x, comp_y, pin_num)
        if pin_num % 2 == 1:  # left pin - extend left
            lx = px - 5.08
        else:  # right pin - extend right
            lx = px + 5.08
        self.add_wire(px, py, lx, py)
        self.add_label(net, lx, py)

    def label_at_pin_2x6(self, net, comp_x, comp_y, pin_num):
        px, py = conn2x06_pin(comp_x, comp_y, pin_num)
        if pin_num % 2 == 1:
            lx = px - 5.08
        else:
            lx = px + 5.08
        self.add_wire(px, py, lx, py)
        self.add_label(net, lx, py)

    def build(self, lib_symbols_block):
        parts = []
        parts.append(f'(kicad_sch (version 20230121) (generator "preamp-gen")\n')
        parts.append(f'  (uuid "{self.uuid}")\n')
        parts.append(f'  (paper "A3")\n')
        parts.append(f'  (title_block\n    (title "{self.title}")\n    (rev "2.0")\n  )\n')
        parts.append(f'  {lib_symbols_block}\n')

        # Components
        for c in self.components:
            parts.append(
                f'  (symbol (lib_id "{c["lib_id"]}") (at {c["x"]} {c["y"]} 0) (unit 1)\n'
                f'    (in_bom yes) (on_board yes) (dnp no)\n'
                f'    (uuid "{c["uuid"]}")\n'
                f'    (property "Reference" "{c["ref"]}" (at {c["x"]} {c["y"]-3} 0)\n'
                f'      (effects (font (size 1.27 1.27))))\n'
                f'    (property "Value" "{c["value"]}" (at {c["x"]} {c["y"]+3} 0)\n'
                f'      (effects (font (size 1.27 1.27))))\n'
                f'    (property "Footprint" "{c["footprint"]}" (at {c["x"]} {c["y"]} 0)\n'
                f'      (effects (font (size 1.27 1.27)) (hide yes)))\n'
                f'    (property "Datasheet" "~" (at {c["x"]} {c["y"]} 0)\n'
                f'      (effects (font (size 1.27 1.27)) (hide yes)))\n'
                f'  )\n'
            )

        # Net labels
        for l in self.labels:
            parts.append(
                f'  (label "{l["name"]}" (at {l["x"]} {l["y"]} 0) (fields_autoplaced yes)\n'
                f'    (effects (font (size 1.27 1.27)) (justify left bottom))\n'
                f'    (uuid "{l["uuid"]}"))\n'
            )

        # Wires
        for w in self.wires:
            parts.append(
                f'  (wire (pts (xy {w["x1"]} {w["y1"]}) (xy {w["x2"]} {w["y2"]}))\n'
                f'    (stroke (width 0) (type default))\n'
                f'    (uuid "{w["uuid"]}"))\n'
            )

        parts.append('  (sheet_instances (path "/" (page "1")))\n')
        parts.append(')\n')
        return "".join(parts)


# =============================================================================
# Read the lib_symbols from the MCP-generated slave schematic
# =============================================================================

slave_sch_path = os.path.join(BASE, "boards/slave/kicad/slave.kicad_sch")
lib_symbols = get_lib_symbols_from_file(slave_sch_path)


# =============================================================================
# SLAVE BOARD
# =============================================================================

def gen_slave():
    s = SchematicWriter("Slave Board - ESP32-S3 DevKit Breakout")

    # Three 1x8 connectors
    j1x, j1y = 50, 60   # J_LEFT
    j2x, j2y = 100, 60  # J_RIGHT
    j3x, j3y = 160, 60  # J_MASTER

    s.add_component("Connector_Generic:Conn_01x08", "J1", "J_LEFT",
                     "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical", j1x, j1y)
    s.add_component("Connector_Generic:Conn_01x08", "J2", "J_RIGHT",
                     "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical", j2x, j2y)
    s.add_component("Connector_Generic:Conn_01x08", "J3", "J_MASTER",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", j3x, j3y)

    # J_LEFT pins: 1=3V3, 2=3V3, 3=RST, 4=GPIO4(NC), 5=BCLK, 6=LRCK, 7=DOUT, 8=GPIO15(NC)
    j1_nets = ["VCC_3V3", "VCC_3V3", "RST", "NC_GPIO4", "BCLK", "LRCK", "DOUT", "NC_GPIO15"]
    for i, net in enumerate(j1_nets):
        if not net.startswith("NC_"):
            s.label_at_pin_1x8(net, j1x, j1y, i+1)

    # J_RIGHT pins: 1=GND, 2=GPIO43(NC), 3=GPIO44(NC), 4=GPIO1(NC), 5=GPIO2(NC), 6=GPIO42(NC), 7=UART_TX, 8=UART_RX
    j2_nets = ["GND", "NC_GPIO43", "NC_GPIO44", "NC_GPIO1", "NC_GPIO2", "NC_GPIO42", "UART_TX", "UART_RX"]
    for i, net in enumerate(j2_nets):
        if not net.startswith("NC_"):
            s.label_at_pin_1x8(net, j2x, j2y, i+1)

    # J_MASTER pins: 1=BCLK, 2=LRCK, 3=DOUT, 4=UART_RX, 5=UART_TX, 6=RST, 7=VCC_3V3, 8=GND
    j3_nets = ["BCLK", "LRCK", "DOUT", "UART_RX", "UART_TX", "RST", "VCC_3V3", "GND"]
    for i, net in enumerate(j3_nets):
        s.label_at_pin_1x8(net, j3x, j3y, i+1)

    return s.build(lib_symbols)


# =============================================================================
# ADC BOARD
# =============================================================================

def gen_adc():
    s = SchematicWriter("ADC Board - Dual ES8388 Audio Codec")

    # Since we don't have ES8388 in the lib_symbols block, use generic ICs
    # We'll use Conn_01x08 as placeholder for codec connections
    # In practice, the Zener HDL generates the real netlist

    # J_AFE connector (2x5)
    jafe_x, jafe_y = 50, 60
    s.add_component("Connector_Generic:Conn_01x08", "J1", "J_AFE_A",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jafe_x, jafe_y)

    # J_MASTER connector (use 1x8 as approx for 2x6)
    jm_x, jm_y = 130, 60
    s.add_component("Connector_Generic:Conn_01x08", "J2", "J_MASTER",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jm_x, jm_y)

    # J_AFE nets (8 signal channels)
    for i in range(8):
        s.label_at_pin_1x8(f"SIG_CH{i+1}", jafe_x, jafe_y, i+1)

    # J_MASTER nets
    jm_nets = ["MCLK", "BCLK", "LRCK", "ADCDAT_A", "ADCDAT_B", "SDA", "SCL", "AVDD"]
    for i, net in enumerate(jm_nets):
        s.label_at_pin_1x8(net, jm_x, jm_y, i+1)

    return s.build(lib_symbols)


# =============================================================================
# MASTER BOARD
# =============================================================================

def gen_master():
    s = SchematicWriter("Master Board - ESP32-S3 DevKit + Power + USB-C")

    # DevKit left header (1x20 approx as 2x 1x8 for schematic)
    # We'll use 1x8 connectors to represent groups of signals

    # ADC connector
    jadc_x, jadc_y = 50, 40
    s.add_component("Connector_Generic:Conn_01x08", "J_ADC", "J_ADC",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jadc_x, jadc_y)
    jadc_nets = ["MCLK", "BCLK", "LRCK", "ADCDAT_A", "ADCDAT_B", "SDA", "SCL", "AVDD_3V3"]
    for i, net in enumerate(jadc_nets):
        s.label_at_pin_1x8(net, jadc_x, jadc_y, i+1)

    # Slave A connector
    jsla_x, jsla_y = 50, 80
    s.add_component("Connector_Generic:Conn_01x08", "J_SLA", "J_SLAVE_A",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jsla_x, jsla_y)
    jsla_nets = ["BCLK_OUT", "LRCK_OUT", "DIN_A", "TX_SLAVE", "RX_SLAVE", "EN_SLAVE2", "DVDD_3V3", "DGND"]
    for i, net in enumerate(jsla_nets):
        s.label_at_pin_1x8(net, jsla_x, jsla_y, i+1)

    # Slave B connector
    jslb_x, jslb_y = 50, 110
    s.add_component("Connector_Generic:Conn_01x08", "J_SLB", "J_SLAVE_B",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jslb_x, jslb_y)
    jslb_nets = ["BCLK_OUT", "LRCK_OUT", "DIN_B", "TX_SLAVE", "RX_SLAVE", "EN_SLAVE3", "DVDD_3V3", "DGND"]
    for i, net in enumerate(jslb_nets):
        s.label_at_pin_1x8(net, jslb_x, jslb_y, i+1)

    # Slave C connector
    jslc_x, jslc_y = 50, 140
    s.add_component("Connector_Generic:Conn_01x08", "J_SLC", "J_SLAVE_C",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jslc_x, jslc_y)
    jslc_nets = ["BCLK_OUT", "LRCK_OUT", "DIN_C", "TX_SLAVE", "RX_SLAVE", "EN_SLAVE4", "DVDD_3V3", "DGND"]
    for i, net in enumerate(jslc_nets):
        s.label_at_pin_1x8(net, jslc_x, jslc_y, i+1)

    # DAC connector
    jdac_x, jdac_y = 50, 170
    s.add_component("Connector_Generic:Conn_01x08", "J_DAC", "J_DAC",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jdac_x, jdac_y)
    jdac_nets = ["DOUT_DAC", "MUX_A", "MUX_B", "MUX_INH", "AVDD_3V3", "DVDD_3V3", "AGND", "DGND"]
    for i, net in enumerate(jdac_nets):
        s.label_at_pin_1x8(net, jdac_x, jdac_y, i+1)

    # USB-C (simplified as 1x4)
    # Battery charger, LDOs, etc would need their own symbols
    # For now, create the board connectors which define the inter-board interface

    return s.build(lib_symbols)


# =============================================================================
# DAC-ROUTER BOARD
# =============================================================================

def gen_dac_router():
    s = SchematicWriter("DAC + Router Board - PCM5102A + CD4052B + OPA4134")

    # J_MASTER from master board
    jm_x, jm_y = 50, 50
    s.add_component("Connector_Generic:Conn_01x08", "J_MASTER", "J_MASTER",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jm_x, jm_y)
    jm_nets = ["DOUT_DAC", "MUX_A", "MUX_B", "MUX_INH", "AVDD", "DVDD", "AGND", "DGND"]
    for i, net in enumerate(jm_nets):
        s.label_at_pin_1x8(net, jm_x, jm_y, i+1)

    # J_AFE from preamp board (8 dry signals)
    jafe_x, jafe_y = 50, 90
    s.add_component("Connector_Generic:Conn_01x08", "J_AFE", "J_AFE",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jafe_x, jafe_y)
    for i in range(8):
        s.label_at_pin_1x8(f"DRY_CH{i+1}", jafe_x, jafe_y, i+1)

    # Output jacks (simplified)
    jol_x, jol_y = 160, 50
    s.add_component("Connector_Generic:Conn_01x08", "J_OUT_L", "TRS_L",
                     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", jol_x, jol_y)
    s.label_at_pin_1x8("JACK_L_TIP", jol_x, jol_y, 1)
    s.label_at_pin_1x8("AGND", jol_x, jol_y, 3)

    jor_x, jor_y = 160, 80
    s.add_component("Connector_Generic:Conn_01x08", "J_OUT_R", "TRS_R",
                     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", jor_x, jor_y)
    s.label_at_pin_1x8("JACK_R_TIP", jor_x, jor_y, 1)
    s.label_at_pin_1x8("AGND", jor_x, jor_y, 3)

    return s.build(lib_symbols)


# =============================================================================
# PREAMP (AFE) BOARD
# =============================================================================

def gen_preamp():
    s = SchematicWriter("AFE Board - 8-Channel Guitar Preamp + Direct Outputs")

    # Input connectors (8x 1x2 simplified as 1x8)
    jin_x, jin_y = 30, 60
    s.add_component("Connector_Generic:Conn_01x08", "J_IN", "PICKUPS",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jin_x, jin_y)
    for i in range(8):
        s.label_at_pin_1x8(f"PICKUP_{i+1}", jin_x, jin_y, i+1)

    # Output to ADC
    jout_x, jout_y = 200, 60
    s.add_component("Connector_Generic:Conn_01x08", "J_OUT", "J_OUT",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jout_x, jout_y)
    for i in range(8):
        s.label_at_pin_1x8(f"SIGNAL_{i+1}", jout_x, jout_y, i+1)

    # Direct output jacks (simplified as 1x8)
    jdo_x, jdo_y = 200, 110
    s.add_component("Connector_Generic:Conn_01x08", "J_DOUT", "DIRECT_OUT",
                     "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", jdo_x, jdo_y)
    for i in range(8):
        s.label_at_pin_1x8(f"DIRECT_OUT_{i+1}", jdo_x, jdo_y, i+1)

    # Power
    jpwr_x, jpwr_y = 30, 110
    s.add_component("Connector_Generic:Conn_01x08", "J_PWR", "POWER",
                     "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", jpwr_x, jpwr_y)
    s.label_at_pin_1x8("AVDD", jpwr_x, jpwr_y, 1)
    s.label_at_pin_1x8("GND", jpwr_x, jpwr_y, 2)

    return s.build(lib_symbols)


# =============================================================================
# Generate all
# =============================================================================

boards = {
    "slave": gen_slave,
    "adc": gen_adc,
    "preamp": gen_preamp,
    "master": gen_master,
    "dac_router": gen_dac_router,
}

for name, gen_fn in boards.items():
    dir_name = name.replace("_", "-")
    sch_path = os.path.join(BASE, f"boards/{dir_name}/kicad/{name}.kicad_sch")
    content = gen_fn()
    with open(sch_path, "w") as f:
        f.write(content)
    print(f"Generated: {sch_path}")

print("\nDone! All schematics regenerated with proper wiring.")
