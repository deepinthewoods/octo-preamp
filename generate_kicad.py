#!/usr/bin/env python3
"""Generate KiCad 7 project files for all 5 preamp system boards."""

import json
import uuid
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def uid():
    return str(uuid.uuid4())


# =============================================================================
# KiCad project template (.kicad_pro)
# =============================================================================

def make_kicad_pro(name, layers=4):
    return json.dumps({
        "board": {
            "3dviewports": [],
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.05,
                    "copper_line_width": 0.2,
                    "copper_text_italic": False,
                    "copper_text_size_h": 1.5,
                    "copper_text_size_v": 1.5,
                    "copper_text_thickness": 0.3,
                    "copper_text_upright": False,
                    "courtyard_line_width": 0.05,
                    "dimension_precision": 4,
                    "dimension_units": 3,
                    "dimensions": {
                        "arrow_length": 1270000,
                        "extension_offset": 500000,
                        "keep_text_aligned": True,
                        "suppress_zeroes": False,
                        "text_position": 0,
                        "units_format": 1
                    },
                    "fab_line_width": 0.1,
                    "fab_text_italic": False,
                    "fab_text_size_h": 1.0,
                    "fab_text_size_v": 1.0,
                    "fab_text_thickness": 0.15,
                    "fab_text_upright": False,
                    "other_line_width": 0.1,
                    "other_text_italic": False,
                    "other_text_size_h": 1.0,
                    "other_text_size_v": 1.0,
                    "other_text_thickness": 0.15,
                    "other_text_upright": False,
                    "pads": {"drill": 0.762, "height": 1.524, "width": 1.524},
                    "silk_line_width": 0.1,
                    "silk_text_italic": False,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.1,
                    "silk_text_upright": False,
                    "zones": {"min_clearance": 0.2}
                },
                "diff_pair_dimensions": [],
                "drc_exclusions": [],
                "meta": {"version": 2},
                "rule_severities": {
                    "annular_width": "error",
                    "clearance": "error",
                    "copper_edge_clearance": "error",
                    "courtyards_overlap": "error",
                    "diff_pair_gap_out_of_range": "error",
                    "diff_pair_uncoupled_length_too_long": "error",
                    "drill_out_of_range": "error",
                    "duplicate_footprints": "warning",
                    "extra_footprint": "warning",
                    "footprint": "error",
                    "footprint_type_mismatch": "error",
                    "hole_clearance": "error",
                    "hole_near_hole": "error",
                    "invalid_outline": "error",
                    "isolated_copper": "warning",
                    "item_on_disabled_layer": "error",
                    "items_not_allowed": "error",
                    "length_out_of_range": "error",
                    "lib_footprint_issues": "warning",
                    "lib_footprint_mismatch": "warning",
                    "malformed_courtyard": "error",
                    "microvia_drill_too_small": "error",
                    "missing_courtyard": "ignore",
                    "missing_footprint": "warning",
                    "net_conflict": "warning",
                    "npth_inside_courtyard": "ignore",
                    "padstack": "error",
                    "pth_inside_courtyard": "ignore",
                    "shorting_items": "error",
                    "silk_edge_clearance": "warning",
                    "silk_over_copper": "warning",
                    "silk_overlap": "warning",
                    "skew_out_of_range": "error",
                    "through_hole_pad_without_hole": "error",
                    "too_many_vias": "error",
                    "track_dangling": "warning",
                    "track_width": "error",
                    "tracks_crossing": "error",
                    "unconnected_items": "error",
                    "unresolved_variable": "error",
                    "via_dangling": "warning",
                    "zones_intersect": "error"
                },
                "rules": {
                    "max_error": 0.005,
                    "min_clearance": 0.2,
                    "min_connection": 0.0,
                    "min_copper_edge_clearance": 0.3,
                    "min_hole_clearance": 0.25,
                    "min_hole_to_hole": 0.25,
                    "min_microvia_diameter": 0.2,
                    "min_microvia_drill": 0.1,
                    "min_resolved_spokes": 2,
                    "min_silk_clearance": 0.0,
                    "min_text_height": 0.8,
                    "min_text_thickness": 0.08,
                    "min_through_hole_diameter": 0.3,
                    "min_track_width": 0.2,
                    "min_via_annular_width": 0.13,
                    "min_via_diameter": 0.6,
                    "min_via_drill": 0.3,
                    "use_height_for_length_calcs": True
                },
                "teardrop_options": [
                    {"td_onpadsmd": True, "td_onroundshapesonly": False,
                     "td_ontrackend": False, "td_onviapad": True}
                ],
                "teardrop_parameters": [
                    {"td_allow_use_two_tracks": True, "td_curve_segcount": 0,
                     "td_height_ratio": 1.0, "td_length_ratio": 0.5,
                     "td_maxheight": 2.0, "td_maxlen": 1.0,
                     "td_on_pad_in_zone": False, "td_target_name": "td_round_shape",
                     "td_width_to_size_filter_ratio": 0.9},
                    {"td_allow_use_two_tracks": True, "td_curve_segcount": 0,
                     "td_height_ratio": 1.0, "td_length_ratio": 0.5,
                     "td_maxheight": 2.0, "td_maxlen": 1.0,
                     "td_on_pad_in_zone": False, "td_target_name": "td_rect_shape",
                     "td_width_to_size_filter_ratio": 0.9},
                    {"td_allow_use_two_tracks": True, "td_curve_segcount": 0,
                     "td_height_ratio": 1.0, "td_length_ratio": 0.5,
                     "td_maxheight": 2.0, "td_maxlen": 1.0,
                     "td_on_pad_in_zone": False, "td_target_name": "td_track_end",
                     "td_width_to_size_filter_ratio": 0.9}
                ],
                "track_widths": [0.0, 0.2, 0.3, 0.5],
                "via_dimensions": [{"diameter": 0.0, "drill": 0.0}],
                "zones_allow_external_fillets": False
            },
            "layer_presets": [],
            "viewports": []
        },
        "boards": [],
        "cvpcb": {"equivalence_files": []},
        "libraries": {
            "pinned_footprint_libs": [],
            "pinned_symbol_libs": []
        },
        "meta": {"filename": f"{name}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [{
                "bus_width": 12,
                "clearance": 0.2,
                "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25,
                "diff_pair_width": 0.2,
                "line_style": 0,
                "microvia_diameter": 0.3,
                "microvia_drill": 0.1,
                "name": "Default",
                "pcb_color": "rgba(0, 0, 0, 0.000)",
                "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": 0.25,
                "via_diameter": 0.8,
                "via_drill": 0.4,
                "wire_width": 6
            }],
            "meta": {"version": 3},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": []
        },
        "pcbnew": {
            "last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "", "step": "", "vrml": ""},
            "page_layout_descr_file": ""
        },
        "schematic": {
            "annotate_start_num": 0,
            "drawing": {
                "dashed_lines_dash_length_ratio": 12.0,
                "dashed_lines_gap_length_ratio": 3.0,
                "default_line_thickness": 6.0,
                "default_text_size": 50.0,
                "field_names": [],
                "intersheets_ref_own_page": False,
                "intersheets_ref_prefix": "",
                "intersheets_ref_short": False,
                "intersheets_ref_show": False,
                "intersheets_ref_suffix": "",
                "junction_size_choice": 3,
                "label_size_ratio": 0.375,
                "pin_symbol_size": 25.0,
                "text_offset_ratio": 0.15
            },
            "legacy_lib_dir": "",
            "legacy_lib_list": [],
            "meta": {"version": 1},
            "net_format_name": "",
            "ngspice": {"fix_include_paths": True, "fix_passive_vals": False,
                        "meta": {"version": 1}, "model_mode": 0,
                        "workbook_filename": ""},
            "page_layout_descr_file": ""
        },
        "sheets": [[uid(), ""]],
        "text_variables": {}
    }, indent=2)


# =============================================================================
# KiCad schematic helpers
# =============================================================================

class SchematicBuilder:
    def __init__(self, title=""):
        self.uuid = uid()
        self.title = title
        self.lib_symbols = []
        self.symbols = []  # placed component instances
        self.wires = []
        self.labels = []
        self.power_symbols = []
        self._y = 25.4  # current Y placement cursor (mm)
        self._lib_cache = set()

    def _add_lib_symbol(self, lib, name, pins):
        """Add a library symbol definition if not already added."""
        key = f"{lib}:{name}"
        if key in self._lib_cache:
            return
        self._lib_cache.add(key)

        pin_strs = []
        for pnum, pname, px, py, direction in pins:
            pin_strs.append(
                f'        (pin passive line (at {px} {py} {direction}) (length 2.54)\n'
                f'          (name "{pname}" (effects (font (size 1.27 1.27))))\n'
                f'          (number "{pnum}" (effects (font (size 1.27 1.27))))\n'
                f'        )'
            )

        self.lib_symbols.append(
            f'    (symbol "{lib}:{name}"\n'
            f'      (in_bom yes) (on_board yes)\n'
            f'      (property "Reference" "U" (at 0 1.27 0) (effects (font (size 1.27 1.27))))\n'
            f'      (property "Value" "{name}" (at 0 -1.27 0) (effects (font (size 1.27 1.27))))\n'
            f'      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'      (symbol "{name}_0_1"\n'
            f'        (rectangle (start -7.62 {len(pins)*1.27+2.54}) (end 7.62 {-len(pins)*1.27-2.54})\n'
            f'          (stroke (width 0.254) (type default))\n'
            f'          (fill (type background))\n'
            f'        )\n'
            f'      )\n'
            f'      (symbol "{name}_1_1"\n'
            + "\n".join(pin_strs) + "\n"
            f'      )\n'
            f'    )'
        )

    def add_component(self, ref, lib, symbol, value, footprint, x, y, pins_nets,
                      properties=None):
        """Place a component instance with net labels on each pin."""
        comp_uuid = uid()
        prop_strs = ""
        if properties:
            for pk, pv in properties.items():
                prop_strs += (
                    f'    (property "{pk}" "{pv}" (at {x} {y} 0)\n'
                    f'      (effects (font (size 1.27 1.27)) hide)\n'
                    f'    )\n'
                )

        self.symbols.append(
            f'  (symbol (lib_id "{lib}:{symbol}") (at {x} {y} 0) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid "{comp_uuid}")\n'
            f'    (property "Reference" "{ref}" (at {x} {y-2.54} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Value" "{value}" (at {x} {y+2.54} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Footprint" "{footprint}" (at {x} {y+5.08} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            + prop_strs +
            f'  )\n'
        )

        # Add net labels for each pin connection
        for pnum, net_name, px_off, py_off in pins_nets:
            if net_name and not net_name.startswith("NC_"):
                lx = x + px_off
                ly = y + py_off
                self.labels.append(
                    f'  (net_label "{net_name}" (at {lx} {ly} 0)\n'
                    f'    (effects (font (size 1.27 1.27)))\n'
                    f'    (uuid "{uid()}")\n'
                    f'  )\n'
                )

    def add_label(self, name, x, y):
        self.labels.append(
            f'  (net_label "{name}" (at {x} {y} 0)\n'
            f'    (effects (font (size 1.27 1.27)))\n'
            f'    (uuid "{uid()}")\n'
            f'  )\n'
        )

    def add_power(self, name, x, y, lib_name="power"):
        self.power_symbols.append(
            f'  (symbol (lib_id "{lib_name}:{name}") (at {x} {y} 0) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "#{name}" (at {x} {y+2.54} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'    (property "Value" "{name}" (at {x} {y-2.54} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'  )\n'
        )

    def build(self):
        lib_block = "\n".join(self.lib_symbols)
        sym_block = "\n".join(self.symbols)
        label_block = "\n".join(self.labels)
        pwr_block = "\n".join(self.power_symbols)

        return (
            f'(kicad_sch (version 20230121) (generator eeschema)\n'
            f'  (uuid "{self.uuid}")\n'
            f'  (paper "A3")\n'
            f'  (title_block\n'
            f'    (title "{self.title}")\n'
            f'    (rev "2.0")\n'
            f'  )\n'
            f'  (lib_symbols\n'
            f'{lib_block}\n'
            f'  )\n'
            f'{sym_block}\n'
            f'{label_block}\n'
            f'{pwr_block}\n'
            f')\n'
        )


# =============================================================================
# KiCad PCB helpers
# =============================================================================

def make_pcb(name, width, height, layers=4, nets=None, mounting_holes=None,
             mounting_dia=3.2, ground_net="GND"):
    """Generate a .kicad_pcb file with board outline and design rules (KiCad 7 format)."""
    if nets is None:
        nets = ["", "GND"]

    # KiCad 7 layer numbering (matches existing preamp layout)
    layer_defs = [
        '\t\t(0 "F.Cu" mixed)',
        '\t\t(2 "B.Cu" mixed)',
        '\t\t(9 "F.Adhes" user "F.Adhesive")',
        '\t\t(11 "B.Adhes" user "B.Adhesive")',
        '\t\t(13 "F.Paste" user)',
        '\t\t(15 "B.Paste" user)',
        '\t\t(5 "F.SilkS" user "F.Silkscreen")',
        '\t\t(7 "B.SilkS" user "B.Silkscreen")',
        '\t\t(1 "F.Mask" user)',
        '\t\t(3 "B.Mask" user)',
        '\t\t(17 "Dwgs.User" user "User.Drawings")',
        '\t\t(19 "Cmts.User" user "User.Comments")',
        '\t\t(21 "Eco1.User" user "User.Eco1")',
        '\t\t(23 "Eco2.User" user "User.Eco2")',
        '\t\t(25 "Edge.Cuts" user)',
        '\t\t(27 "Margin" user)',
        '\t\t(31 "F.CrtYd" user "F.Courtyard")',
        '\t\t(29 "B.CrtYd" user "B.Courtyard")',
        '\t\t(35 "F.Fab" user)',
        '\t\t(33 "B.Fab" user)',
    ]

    if layers >= 4:
        layer_defs.insert(1, '\t\t(4 "In1.Cu" power)')
        layer_defs.insert(2, '\t\t(6 "In2.Cu" power)')

    net_strs = "\n".join(f'\t(net {i} "{n}")' for i, n in enumerate(nets))

    # Board outline — KiCad 7 gr_line syntax: (width ...) not (stroke ...)
    outline = (
        f'\t(gr_line (start 0 0) (end {width} 0) (layer "Edge.Cuts") (width 0.05) (tstamp {uid()}))\n'
        f'\t(gr_line (start {width} 0) (end {width} {height}) (layer "Edge.Cuts") (width 0.05) (tstamp {uid()}))\n'
        f'\t(gr_line (start {width} {height}) (end 0 {height}) (layer "Edge.Cuts") (width 0.05) (tstamp {uid()}))\n'
        f'\t(gr_line (start 0 {height}) (end 0 0) (layer "Edge.Cuts") (width 0.05) (tstamp {uid()}))\n'
    )

    return (
        f'(kicad_pcb\n'
        f'\t(version 20221018)\n'
        f'\t(generator pcbnew)\n'
        f'\t(general\n'
        f'\t\t(thickness 1.6)\n'
        f'\t)\n'
        f'\t(paper "A4")\n'
        f'\t(title_block\n'
        f'\t\t(title "{name}")\n'
        f'\t\t(rev "2.0")\n'
        f'\t)\n'
        f'\t(layers\n'
        + "\n".join(layer_defs) + "\n"
        f'\t)\n'
        f'\t(setup\n'
        f'\t\t(pad_to_mask_clearance 0)\n'
        f'\t\t(pcbplotparams\n'
        f'\t\t\t(layerselection 0x00010fc_ffffffff)\n'
        f'\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)\n'
        f'\t\t\t(disableapertmacros false)\n'
        f'\t\t\t(usegerberextensions false)\n'
        f'\t\t\t(usegerberattributes true)\n'
        f'\t\t\t(usegerberadvancedattributes true)\n'
        f'\t\t\t(creategerberjobfile true)\n'
        f'\t\t\t(dashed_line_dash_ratio 12.000000)\n'
        f'\t\t\t(dashed_line_gap_ratio 3.000000)\n'
        f'\t\t\t(svgprecision 4)\n'
        f'\t\t\t(plotframeref false)\n'
        f'\t\t\t(viasonmask false)\n'
        f'\t\t\t(mode 1)\n'
        f'\t\t\t(useauxorigin false)\n'
        f'\t\t\t(hpglpennumber 1)\n'
        f'\t\t\t(hpglpenspeed 20)\n'
        f'\t\t\t(hpglpendiameter 15.000000)\n'
        f'\t\t\t(dxfpolygonmode true)\n'
        f'\t\t\t(dxfimperialunits true)\n'
        f'\t\t\t(dxfusepcbnewfont true)\n'
        f'\t\t\t(psnegative false)\n'
        f'\t\t\t(psa4output false)\n'
        f'\t\t\t(plotreference true)\n'
        f'\t\t\t(plotvalue true)\n'
        f'\t\t\t(plotinvisibletext false)\n'
        f'\t\t\t(sketchpadsonfab false)\n'
        f'\t\t\t(subtractmaskfromsilk false)\n'
        f'\t\t\t(outputformat 1)\n'
        f'\t\t\t(mirror false)\n'
        f'\t\t\t(drillshape 1)\n'
        f'\t\t\t(scaleselection 1)\n'
        f'\t\t\t(outputdirectory "")\n'
        f'\t\t)\n'
        f'\t)\n'
        f'{net_strs}\n'
        f'{outline}'
        f')\n'
    )


# =============================================================================
# Minimal schematic builder — components with net labels
# =============================================================================

def make_minimal_sch(title, components, net_labels):
    """
    Create a minimal schematic with components and net labels.
    components: list of (ref, symbol_lib, value, footprint, x, y)
    net_labels: list of (name, x, y)
    """
    comps = []
    labels = []

    for ref, sym, val, fp, x, y in components:
        comps.append(
            f'  (symbol (lib_id "{sym}") (at {x} {y} 0) (unit 1)\n'
            f'    (in_bom yes) (on_board yes) (dnp no)\n'
            f'    (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {x+2} {y-3} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Value" "{val}" (at {x+2} {y+3} 0)\n'
            f'      (effects (font (size 1.27 1.27)))\n'
            f'    )\n'
            f'    (property "Footprint" "{fp}" (at {x} {y+6} 0)\n'
            f'      (effects (font (size 1.27 1.27)) hide)\n'
            f'    )\n'
            f'  )\n'
        )

    for name, x, y in net_labels:
        labels.append(
            f'  (label "{name}" (at {x} {y} 0) (fields_autoplaced)\n'
            f'    (effects (font (size 1.27 1.27)))\n'
            f'    (uuid "{uid()}")\n'
            f'  )\n'
        )

    return (
        f'(kicad_sch (version 20230121) (generator "eeschema")\n'
        f'  (uuid "{uid()}")\n'
        f'  (paper "A3")\n'
        f'  (title_block\n'
        f'    (title "{title}")\n'
        f'    (rev "2.0")\n'
        f'  )\n'
        f'  (lib_symbols\n'
        f'  )\n'
        + "".join(comps)
        + "".join(labels)
        + f')\n'
    )


# =============================================================================
# Board definitions
# =============================================================================

BOARDS = {
    "slave": {
        "title": "Slave Board - ESP32-S3 DevKit Breakout",
        "width": 30, "height": 25, "layers": 2,
        "mounting_dia": 2.2,
        "nets": ["", "GND", "VCC_3V3", "RST", "BCLK", "LRCK", "DOUT",
                 "UART_TX", "UART_RX"],
        "ground_net": "GND",
        "components": [
            # ref, symbol_lib, value, footprint, x, y
            ("J1", "Connector_Generic:Conn_01x08_Socket", "J_LEFT",
             "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical", 30, 30),
            ("J2", "Connector_Generic:Conn_01x08_Socket", "J_RIGHT",
             "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical", 60, 30),
            ("J3", "Connector_Generic:Conn_01x08_Pin", "J_MASTER",
             "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 100, 30),
        ],
        "net_labels": [
            ("VCC_3V3", 20, 30), ("VCC_3V3", 20, 32.54),
            ("RST", 20, 35.08), ("BCLK", 20, 40.16),
            ("LRCK", 20, 42.7), ("DOUT", 20, 45.24),
            ("GND", 50, 30),
            ("UART_TX", 50, 45.24), ("UART_RX", 50, 47.78),
            ("BCLK", 90, 30), ("LRCK", 90, 32.54), ("DOUT", 90, 35.08),
            ("UART_RX", 90, 37.62), ("UART_TX", 90, 40.16),
            ("RST", 90, 42.7), ("VCC_3V3", 90, 45.24), ("GND", 90, 47.78),
        ],
    },
    "adc": {
        "title": "ADC Board - Dual ES8388 Audio Codec",
        "width": 50, "height": 40, "layers": 4,
        "mounting_dia": 3.2,
        "nets": ["", "AGND", "DGND", "AVDD", "DVDD", "SDA", "SCL",
                 "MCLK", "BCLK", "LRCK", "ADCDAT_A", "ADCDAT_B",
                 "SIG_CH1", "SIG_CH2", "SIG_CH3", "SIG_CH4",
                 "SIG_CH5", "SIG_CH6", "SIG_CH7", "SIG_CH8",
                 "VREF_A1", "VRP_A1", "DVREF_A1", "DVRP_A1",
                 "VREF_A2", "VRP_A2", "DVREF_A2", "DVRP_A2",
                 "AD0_HIGH"],
        "ground_net": "AGND",
        "components": [
            ("U1", "Audio:ES8388", "ES8388",
             "Package_QFP:LQFP-28_4x4mm_P0.4mm", 40, 40),
            ("U2", "Audio:ES8388", "ES8388",
             "Package_QFP:LQFP-28_4x4mm_P0.4mm", 40, 80),
            ("J1", "Connector_Generic:Conn_02x05_Odd_Even", "J_AFE",
             "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", 120, 40),
            ("J2", "Connector_Generic:Conn_02x06_Odd_Even", "J_MASTER",
             "Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical", 120, 80),
            # Decoupling caps
            ("C1", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 55, 35),
            ("C2", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 55, 40),
            ("C3", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 55, 75),
            ("C4", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 55, 80),
            # Reference caps
            ("C5", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 60, 45),
            ("C6", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 65, 45),
            ("C7", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 70, 45),
            ("C8", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 75, 45),
            # I2C pullups
            ("R1", "Device:R", "4.7k", "Resistor_SMD:R_0603_1608Metric", 80, 40),
            ("R2", "Device:R", "4.7k", "Resistor_SMD:R_0603_1608Metric", 85, 40),
            # AD0 pullup
            ("R3", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 30, 80),
        ],
        "net_labels": [
            ("MCLK", 110, 80), ("BCLK", 110, 82.54), ("LRCK", 110, 85.08),
            ("ADCDAT_A", 110, 87.62), ("ADCDAT_B", 110, 90.16),
            ("SDA", 110, 92.7), ("SCL", 110, 95.24),
            ("AVDD", 110, 97.78), ("DVDD", 110, 100.32),
            ("AGND", 110, 102.86), ("DGND", 110, 105.4),
        ],
    },
    "preamp": {
        "title": "AFE Board - 8-Channel Guitar Preamp + Direct Outputs",
        "width": 95, "height": 95, "layers": 4,
        "mounting_dia": 3.2,
        "nets": ["", "GND", "AVDD", "VGND", "VGND_MID"] +
                [f"PICKUP_{i}" for i in range(1, 9)] +
                [f"SIGNAL_{i}" for i in range(1, 9)] +
                [f"COUPLED_{i}" for i in range(1, 9)] +
                [f"BUFFERED_{i}" for i in range(1, 9)] +
                [f"DIRECT_OUT_{i}" for i in range(1, 9)] +
                [f"FB_{i}" for i in range(1, 9)] +
                [f"AMPLIFIED_{i}" for i in range(1, 9)] +
                [f"FILTERED_{i}" for i in range(1, 9)],
        "ground_net": "GND",
        "components": (
            # Virtual ground
            [("U_VGND", "Amplifier_Operational:TL072", "TL072",
              "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 30, 20),
             ("R_DIV_TOP", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 20, 15),
             ("R_DIV_BOT", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 20, 25),
             ("C_VGND_BULK", "Device:C", "100uF", "Capacitor_SMD:C_1206_3216Metric", 40, 20),
             ("C_VGND_BYP", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 45, 20)]
            # Input buffers (4x NE5532)
            + [("U_BUF" + str(i+1), "Amplifier_Operational:NE5532", "NE5532",
                "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 25, 45 + i*18)
               for i in range(4)]
            # Direct output buffers (4x NE5532)
            + [("U_DOUT" + str(i+1), "Amplifier_Operational:NE5532", "NE5532",
                "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 55, 45 + i*18)
               for i in range(4)]
            # Gain stage (4x NE5532)
            + [("U_GAIN" + str(i+1), "Amplifier_Operational:NE5532", "NE5532",
                "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 85, 45 + i*18)
               for i in range(4)]
            # Trimpots (8x)
            + [("RV_F" + str(i+1), "Device:R_Potentiometer_Trim", "10k",
                "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical", 110, 38 + i*9)
               for i in range(8)]
            # Mono jacks (8x direct out)
            + [("J_DOUT" + str(i+1), "Connector_Audio:AudioJack2", "6.5mm Mono",
                "Connector_Audio:Jack_6.35mm_Neutrik_NMJ6HF2_Horizontal", 140, 38 + i*9)
               for i in range(8)]
            # Input headers (8x)
            + [("J_IN" + str(i+1), "Connector_Generic:Conn_01x02_Pin", "PICKUP",
                "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 10, 40 + i*9)
               for i in range(8)]
            # Connectors
            + [("J_OUT", "Connector_Generic:Conn_02x05_Odd_Even", "J_OUT",
                "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", 140, 120),
               ("J_PWR", "Connector_Generic:Conn_01x02_Pin", "J_PWR",
                "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 10, 120)]
        ),
        "net_labels": [
            ("AVDD", 10, 120), ("GND", 10, 122.54),
            ("VGND", 30, 15), ("VGND_MID", 20, 20),
        ],
    },
    "master": {
        "title": "Master Board - ESP32-S3 DevKit + Power + USB-C",
        "width": 80, "height": 60, "layers": 4,
        "mounting_dia": 3.2,
        "nets": ["", "DGND", "AGND", "VBUS", "VBAT_RAW", "VBAT",
                 "AVDD_3V3", "DVDD_3V3", "USB_DP", "USB_DN", "CC1", "CC2",
                 "CHARGE_STAT", "PROG_PIN", "LED_STAT", "LP2985_BYP",
                 "VBAT_DIV", "VBAT_MON",
                 "MCLK", "BCLK", "LRCK", "ADCDAT_A", "ADCDAT_B",
                 "SDA", "SCL", "TX_SLAVE", "RX_SLAVE",
                 "BCLK_OUT", "LRCK_OUT", "DIN_A", "DIN_B", "DIN_C",
                 "DOUT_DAC", "MUX_A", "MUX_B", "MUX_INH",
                 "BOOT_SLAVE2", "BOOT_SLAVE3", "BOOT_SLAVE4",
                 "EN_SLAVE2", "EN_SLAVE3", "EN_SLAVE4", "ESP_RST"],
        "ground_net": "DGND",
        "components": [
            # DevKit headers
            ("J_L", "Connector_Generic:Conn_01x20_Socket", "ESP32-DevKit-L",
             "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", 40, 15),
            ("J_R", "Connector_Generic:Conn_01x20_Socket", "ESP32-DevKit-R",
             "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", 55, 15),
            # USB-C
            ("J_USB", "Connector:USB_C_Receptacle_USB2.0", "USB-C",
             "Connector_USB:USB_C_Receptacle_GCT_USB4085", 10, 15),
            # Charger
            ("U_CHG", "Battery_Management:MCP73831-2-OT", "MCP73831",
             "Package_TO_SOT_SMD:SOT-23-5", 20, 35),
            # BAT54
            ("D_BAT", "Diode:BAT54", "BAT54",
             "Package_TO_SOT_SMD:SOT-23", 30, 35),
            # LDOs
            ("U_AVDD", "Regulator_Linear:LP2985-33", "LP2985-3.3",
             "Package_TO_SOT_SMD:SOT-23-5", 25, 50),
            ("U_DVDD", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3",
             "Package_TO_SOT_SMD:SOT-223-3_TabPin2", 45, 50),
            # Ferrite bead
            ("FB1", "Device:FerriteBead", "220R",
             "Inductor_SMD:L_0805_2012Metric", 35, 55),
            # Battery connector
            ("J_BAT", "Connector_Generic:Conn_01x02_Pin", "J_BAT",
             "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", 10, 50),
            # Board connectors
            ("J_ADC", "Connector_Generic:Conn_02x06_Odd_Even", "J_ADC",
             "Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical", 70, 20),
            ("J_SLA", "Connector_Generic:Conn_01x08_Pin", "J_SLAVE_A",
             "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 70, 40),
            ("J_SLB", "Connector_Generic:Conn_01x08_Pin", "J_SLAVE_B",
             "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 70, 55),
            ("J_SLC", "Connector_Generic:Conn_01x08_Pin", "J_SLAVE_C",
             "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical", 70, 70),
            ("J_DAC", "Connector_Generic:Conn_02x05_Odd_Even", "J_DAC",
             "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", 70, 85),
            # Passives
            ("R_CC1", "Device:R", "5.1k", "Resistor_SMD:R_0402_1005Metric", 15, 25),
            ("R_CC2", "Device:R", "5.1k", "Resistor_SMD:R_0402_1005Metric", 15, 30),
            ("R_PROG", "Device:R", "4.7k", "Resistor_SMD:R_0603_1608Metric", 25, 40),
            ("R_LED", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", 20, 30),
            ("R_UART", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 60, 45),
            ("R_VMON_T", "Device:R", "100k", "Resistor_SMD:R_0603_1608Metric", 55, 55),
            ("R_VMON_B", "Device:R", "100k", "Resistor_SMD:R_0603_1608Metric", 55, 60),
            ("C_VBUS1", "Device:C", "100uF", "Capacitor_SMD:C_1210_3225Metric", 12, 20),
            ("C_VBUS2", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 12, 25),
            ("C_BAT1", "Device:C", "100uF", "Capacitor_SMD:C_1210_3225Metric", 35, 40),
            ("C_BAT2", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 35, 45),
            ("C_VMON", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 60, 60),
            ("D_STAT", "Device:LED", "Green",
             "LED_SMD:LED_0603_1608Metric", 20, 35),
        ],
        "net_labels": [
            ("VBUS", 10, 15), ("DGND", 10, 20), ("USB_DP", 10, 25), ("USB_DN", 10, 30),
            ("VBAT_RAW", 25, 35), ("VBAT", 35, 35),
            ("AVDD_3V3", 25, 50), ("DVDD_3V3", 45, 50),
            ("MCLK", 30, 15), ("BCLK", 32, 15), ("LRCK", 34, 15),
            ("TX_SLAVE", 50, 15), ("RX_SLAVE", 52, 15),
        ],
    },
    "dac_router": {
        "title": "DAC + Router Board - PCM5102A + CD4052B + OPA4134",
        "width": 70, "height": 50, "layers": 4,
        "mounting_dia": 3.2,
        "nets": ["", "AGND", "DGND", "AVDD", "DVDD",
                 "DOUT_DAC", "MUX_A", "MUX_B", "MUX_INH",
                 "DAC_OUTL", "DAC_OUTR", "DAC_CAPP", "DAC_CAPM",
                 "DAC_VNEG", "DAC_CPVDD", "DAC_L_AC", "DAC_R_AC",
                 "SUM_L", "SUM_R", "SUM_FB_L", "SUM_FB_R",
                 "OUT_L", "OUT_R",
                 "MUX1_X_OUT", "MUX1_Y_OUT", "MUX2_X_OUT", "MUX2_Y_OUT",
                 "MUX1_X_FILT", "MUX1_Y_FILT",
                 "OUT_L_AC", "OUT_R_AC", "JACK_L_TIP", "JACK_R_TIP",
                 "JACK_L_RING", "JACK_R_RING"] +
                [f"DRY_CH{i}" for i in range(1, 9)],
        "ground_net": "AGND",
        "components": [
            # PCM5102A
            ("U_DAC", "Audio:PCM5102A", "PCM5102A",
             "Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm", 20, 20),
            # CD4052B muxes
            ("U_MUX1", "Analog_Switch:CD4052B", "CD4052B",
             "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 45, 20),
            ("U_MUX2", "Analog_Switch:CD4052B", "CD4052B",
             "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", 45, 45),
            # OPA4134 summing amp
            ("U_SUM", "Amplifier_Operational:OPA4134", "OPA4134",
             "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", 20, 45),
            # Input/output resistors
            ("R_SUM_L1", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 40),
            ("R_SUM_L2", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 43),
            ("R_SUM_L3", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 46),
            ("R_SUM_L4", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 49),
            ("R_SUM_R5", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 55),
            ("R_SUM_R6", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 58),
            ("R_SUM_R7", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 61),
            ("R_SUM_R8", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", 10, 64),
            ("R_FB_L", "Device:R", "1.2k", "Resistor_SMD:R_0603_1608Metric", 25, 40),
            ("R_FB_R", "Device:R", "1.2k", "Resistor_SMD:R_0603_1608Metric", 25, 55),
            # RC click suppression
            ("R_RC_LX", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", 55, 20),
            ("C_RC_LX", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 58, 20),
            ("R_RC_LY", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", 55, 25),
            ("C_RC_LY", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 58, 25),
            # Output coupling
            ("C_OUTL", "Device:C_Polarized", "100uF", "Capacitor_SMD:C_1210_3225Metric", 60, 30),
            ("C_OUTR", "Device:C_Polarized", "100uF", "Capacitor_SMD:C_1210_3225Metric", 60, 35),
            ("R_OUTL", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", 63, 30),
            ("R_OUTR", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", 63, 35),
            # TRS jacks
            ("J_OUT_L", "Connector_Generic:Conn_01x03_Pin", "TRS_L",
             "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", 70, 30),
            ("J_OUT_R", "Connector_Generic:Conn_01x03_Pin", "TRS_R",
             "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", 70, 38),
            # Board connectors
            ("J_MASTER", "Connector_Generic:Conn_02x05_Odd_Even", "J_MASTER",
             "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", 10, 15),
            ("J_AFE", "Connector_Generic:Conn_02x05_Odd_Even", "J_AFE",
             "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", 10, 35),
            # Footswitch
            ("J_FS1", "Connector_Generic:Conn_01x02_Pin", "FS1",
             "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 70, 45),
            ("J_FS2", "Connector_Generic:Conn_01x02_Pin", "FS2",
             "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 70, 50),
            # DAC decoupling
            ("C_CP", "Device:C", "2.2uF", "Capacitor_SMD:C_0603_1608Metric", 30, 20),
            ("C_VNEG", "Device:C", "2.2uF", "Capacitor_SMD:C_0603_1608Metric", 30, 25),
            ("C_CPVDD", "Device:C", "100nF", "Capacitor_SMD:C_0603_1608Metric", 30, 15),
            ("C_DACL", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 35, 20),
            ("C_DACR", "Device:C", "10uF", "Capacitor_SMD:C_0805_2012Metric", 35, 25),
        ],
        "net_labels": [
            ("DOUT_DAC", 10, 15), ("MUX_A", 10, 17), ("MUX_B", 10, 19),
            ("MUX_INH", 10, 21), ("AVDD", 10, 23), ("DVDD", 10, 25),
            ("AGND", 10, 27), ("DGND", 10, 29),
            ("DAC_OUTL", 25, 20), ("DAC_OUTR", 25, 25),
        ],
    },
}


# =============================================================================
# Generate all projects
# =============================================================================

def generate_board(name, cfg):
    board_dir = os.path.join(BASE, "boards", name.replace("_", "-"), "kicad")
    os.makedirs(board_dir, exist_ok=True)

    fname = name

    # Write .kicad_pro
    pro_path = os.path.join(board_dir, f"{fname}.kicad_pro")
    with open(pro_path, "w") as f:
        f.write(make_kicad_pro(fname, cfg.get("layers", 4)))

    # Write .kicad_sch
    sch_path = os.path.join(board_dir, f"{fname}.kicad_sch")
    sch_content = make_minimal_sch(
        cfg["title"],
        cfg.get("components", []),
        cfg.get("net_labels", []),
    )
    with open(sch_path, "w") as f:
        f.write(sch_content)

    # Write .kicad_pcb
    pcb_path = os.path.join(board_dir, f"{fname}.kicad_pcb")
    pcb_content = make_pcb(
        fname,
        cfg["width"],
        cfg["height"],
        layers=cfg.get("layers", 4),
        nets=cfg.get("nets", ["", "GND"]),
        mounting_dia=cfg.get("mounting_dia", 3.2),
        ground_net=cfg.get("ground_net", "GND"),
    )
    with open(pcb_path, "w") as f:
        f.write(pcb_content)

    print(f"  Created: {pro_path}")
    print(f"  Created: {sch_path}")
    print(f"  Created: {pcb_path}")


if __name__ == "__main__":
    print("Generating KiCad projects for 5 boards...")
    for name, cfg in BOARDS.items():
        print(f"\n--- {name} ---")
        generate_board(name, cfg)
    print("\nDone! All 5 KiCad projects generated.")
