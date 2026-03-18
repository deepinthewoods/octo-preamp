# 8-Channel Per-String Guitar Pickup System — Definitive Specification

**Version 2.10 — 18 March 2026**

Consolidates: `pcb_spec_v2.0.md`, `pcb_revision_brief_v2.1.md`, `pcb_revision_brief_v2.2.md`

**v2.10 changes (noise-optimized moat crossing):**
- I2S clocks (MCLK, BCLK, LRCK) now cross moat once each via fan-out topology (was 12 individual crossings, now 3 trunks + vertical backbones)
- Added 33R series termination resistors (R_MCLK_TERM, R_BCLK_TERM, R_LRCK_TERM) on I2S clocks near ESP32 source to reduce edge rate and EMI
- I2C signals (SDA, SCL, SDA2, SCL2) moved to In2.Cu — physically separated from I2S clocks/data on In1.Cu
- Added 13 DGND stitching vias at x=74.5 (moat boundary) for low-impedance return path
- Added 6 DGND ground guard traces on In1.Cu between signal groups
- DGND corridor on In1.Cu extended north to y=25 to cover clock fan-out trunks
- Total moat crossings reduced from 35 to 22 (12 clock→3, I2C remains 8 but on separate layer)

**v2.9 changes (remove board USB-C):**
- Removed separate USB-C connector (J_USB) from MAIN board — DevKit's built-in USB-C handles both data and power
- DevKit P_5V pin now feeds VBUS net (MCP73831 LiPo charger)
- GPIO19/GPIO20 no longer routed to board — used internally by DevKit USB-C
- Removed R_CC1, R_CC2 (CC pull-downs), UsbC module import
- Saves ~5 components and board space

**v2.8 changes (mixed-signal routing strategy):**
- Added DGND copper pour on In1.Cu covering digital zone (x=10–75mm)
- Added DGND corridor strip on In1.Cu (x=75–86, y=27–51) extending through moat into analog zone under ES8388 codecs
- Digital traces to ES8388s (I2S, I2C) must be routed on In1.Cu so return currents stay on DGND, not AGND
- Updated 4-layer stackup: F.Cu/B.Cu = signal + ground pours, In1.Cu = DGND plane + corridor, In2.Cu = AGND plane
- ESP32-S3 antenna clearance is inherently met (devkit on pin headers elevates antenna >3mm above PCB copper)

**v2.7 changes (preamp board local LDO):**
- Added LP2985-33DBVR to preamp board for local AVDD generation (from VBAT)
- Removes ~104mA NE5532 load from MAIN board LP2985 (was exceeding 150mA limit)
- MAIN LP2985 now supplies only ~78mA (ES8388 AVDD + MAIN analog ICs — well within limit)
- J_OUT/J_AFE cable pin 9 changed from AVDD to VBAT
- Fixed VBAT_MON/VBAT_DIV net split bug (GPIO36 now connects to voltage divider midpoint)

**v2.6 changes (4x ES8388, remove HT8988A):**
- ES8388 is stereo (2-ch ADC per IC), not 4-ch as previously assumed
- Replaced 2x ES8388 + HT8988A with 4x ES8388 (2-ch stereo each = 8 ADC channels total)
- ES8388 #3 DAC section active: headphone output (LOUT1/ROUT1) + line output (LOUT2/ROUT2)
- Added second I2C bus (GPIO43=SDA2, GPIO44=SCL2) for ES8388 #3+#4 (address conflict resolution)
- New ADC data lines: GPIO4 (ADCDAT_C, ES8388 #3), GPIO48 (ADCDAT_D, ES8388 #4; shares DevKit RGB LED pin)
- GPIO13 DACDAT now routes to ES8388 #3 DSDIN (same GPIO, replaces HT8988A)
- Single JLCPCB part for all ADC+DAC (C365736, $0.95, 9,686 in stock); open items #1 and #2 closed

**v2.5 changes (gain trimpot SMD):**
- Gain trimpots changed from Bourns 3296W (THT) to Bourns 3314J-1-103E (SMD, top-adjust)
- Trimpots now JLCPCB-assemblable — no longer require hand soldering

**v2.4 changes (slave socket placement):**
- Slave ESP32 sockets repositioned to board edges so DevKit boards hang over the edge
- Slaves C+D (strings 5-8): bottom edge, boards hang below
- Slaves A+B (strings 1-4): top edge, boards hang above (sockets rotated 180°)

**v2.3 changes (size optimization):**
- All 0603 passives downsized to 0402 across both boards
- Decoupling module: bulk 0805→0603, bypass 0603→0402
- Bulk coupling caps: 100uF 1210→47uF 0805 (VBUS, battery, headphone, main output)
- DVDD bulk: 22uF 1206→0805, VGND bulk: 100uF 1206→47uF 0805
- Preamp: 8x 6.35mm mono jacks replaced with 2-pin solder pad headers
- Preamp: removed 4x dedicated direct output buffer NE5532s (input buffer drives both paths via 600R series protection)
- Mounting holes reduced from 4→2 per board
- Preamp op-amp count: 17→13 NE5532 dual ICs
- Preamp component count: 165→151

---

## 1. Project Overview

An electronic system for an 8-string guitar with independent per-string pickup processing. Each string's signal is captured, buffered, and made available simultaneously on three paths:

1. **Direct output** — unbuffered tap from input buffer, per-string solder pads for wire soldering
2. **8-channel ADC path** — feeding the digital DSP system (pitch detection, oscillator synthesis, filtering, or per-string effects)
3. **Analog summing path** — stereo summed dry signal for traditional amplifier use

The system uses 4x ES8388 codec ICs (stereo ADC+DAC, 2 channels each = 8 ADC channels total) and 5x ESP32-S3 microcontrollers (1 master + 4 slaves) for DSP. ES8388 #3 provides the final stereo DAC output with headphone and line outputs. Power is supplied by a single-cell LiPo battery charged via USB-C.

### Boards

| Board | Source | Components | Layers | Size | Description |
|-------|--------|------------|--------|------|-------------|
| **MAIN** | `boards/main/main.zen` | ~124 | 4 | ~160x80mm | Merged master + ADC + DAC-router + 4x slave sockets |
| **Preamp/AFE** | `boards/preamp/preamp.zen` | ~151 | 4 | ~100x60mm | Pure analog front-end, 13x NE5532 dual op-amps |

Single cable between boards: Preamp `J_OUT` -> MAIN `J_AFE` (2x5 header: 8 signals + AVDD + AGND).

Previous board sources (master, adc, dac-router, slave) archived to `archive/`.

### HDL Toolchain

- **Zener** (Starlark-based PCB HDL by Diode) — `.zen` files are the source of truth
- `pcb build` to validate, `pcb layout` to generate KiCad files, `pcb bom` for BOM, `pcb fmt` to format
- Custom components in `components/*/`, stdlib generics in `.pcb/stdlib/`

---

## 2. System Signal Flow

### Synth Mode (Default)

```
Pickups -> AFE (buffer, gain, AA filter)
  -> ES8388 ADC (I2S to master)
  -> Master: pitch detection + amplitude tracking
  -> Packs control data into forward I2S TDM slots
  -> I2S to slaves
  -> Slaves: oscillator synthesis + filter DSP
  -> I2S return to master
  -> Master mixes all returns
  -> ES8388 #3 DAC -> Outputs
```

### Effects Mode

```
Pickups -> AFE -> ES8388 ADC (I2S to master)
  -> Master: routes raw 16-bit audio into forward TDM slots (no pitch detection)
  -> I2S to slaves
  -> Slaves: per-string effects (EQ, dynamics, modulation, delay)
  -> I2S return to master
  -> Master mixes -> ES8388 #3 DAC -> Outputs
```

### Analog Dry Path (Parallel)

```
AFE SIGNAL lines -> summing amp (strings 1-4 left, 5-8 right)
  -> CD4052B routing mux -> main output jacks
```

Mode is selectable at runtime via footswitch. UART command switches slaves between synth/effects mode.

---

## 3. Power Supply

### Architecture

The system runs entirely from a single-cell LiPo battery (3.7V nominal). USB-C on the DevKit provides both programming/debug and 5V charging power. There is no separate USB-C connector on the MAIN board. There is no 5V rail. Slave ESP32 DevKits are powered directly from the 3.3V DVDD rail, bypassing their onboard LDOs.

```
DevKit USB-C (5V via P_5V pin)
  |
  v
MCP73831T-2ACI/OT (SOT-23-5, ~210mA charge current)
  |
  v
LiPo Cell (single cell, 3.7V nom, 4.2V full, 3.5V cutoff)
  |
  +---> LP2985-33DBVR (MAIN) --> 3.3V AVDD (analog, ~30uV RMS)
  |       Feeds: 4x ES8388 AVDD + MAIN analog ICs (~78mA)
  |
  +---> LP2985-33DBVR (Preamp, via J_AFE pin 9 VBAT) --> 3.3V AVDD (preamp local)
  |       Feeds: 13x NE5532 + virtual ground (~104mA)
  |
  +---> AP2114H-3.3 --> 3.3V DVDD (digital, 1A max)
```

### MCP73831 Charger

- Package: SOT-23-5
- RPROG = 4.7k -> ~210mA charge current
- STAT pin -> charge status LED (active-low open-drain)
- BAT54 Schottky reverse protection on VBAT line
- Decoupling: 47uF + 100nF on VBAT output

### Analog Rail — LP2985-33DBVR × 2 (AVDD)

Two instances of LP2985-33DBVR, one per board:

**MAIN board LP2985:**
- Package: SOT-23-5
- Output: 3.3V AVDD, ~30uV RMS noise
- Feeds: 4x ES8388 AVDD, 2x NE5532 summing amp, 2x CD4052B (~78mA)
- 10nF NP0 bypass cap on BYP pin
- VBAT routed to preamp via J_AFE pin 9

**Preamp board LP2985:**
- Package: SOT-23-5
- Output: 3.3V AVDD (local), ~30uV RMS noise
- Feeds: 13x NE5532 op-amps, virtual ground buffer (~104mA)
- 10nF NP0 bypass cap on BYP pin
- Powered from VBAT via J_OUT pin 9 (from MAIN board)
- Copper pour: GND (single analog ground on preamp)

### Digital Rail — AP2114H-3.3 (DVDD)

- Package: SOT-223, 1A max output
- Output: 3.3V DVDD
- Feeds: 5x ESP32-S3 DevKits (~80mA each), ES8388 DVDD
- Current budget: ~430mA typical, ~580mA peak
- Decoupling: 22uF bulk + standard 100nF/10uF
- Copper pour: DGND, separate from AGND

### Ground Planes (CRITICAL)

- AGND and DGND are separate copper pours on the MAIN board
- Connected at exactly ONE star point via ferrite bead FB1 (220 Ohm, 0805) at the moat boundary
- 4mm moat (no copper) separates digital (left) and analog (right) zones on F.Cu/B.Cu
- ES8388 AGND/DGND pins connect to their respective pours
- All op-amp ground pins connect to AGND only
- Preamp board uses single `GND` net (pure analog)

**MAIN board 4-layer ground pour assignment:**

| Layer | Digital zone (x=10–75) | Moat (x=75–79) | Analog zone (x=79–110) |
|-------|----------------------|-----------------|----------------------|
| F.Cu | DGND pour | No copper | AGND pour |
| In1.Cu | DGND pour | DGND corridor (y=25–77) | DGND corridor (to x=89, y=25–77) |
| In2.Cu | — | — | AGND pour |
| B.Cu | DGND pour | No copper | AGND pour |

**Digital corridor on In1.Cu:** A DGND pour strip extends from the digital zone through the moat into the analog zone (x=75–89, y=25–77), covering the ES8388 codecs and CD4052B muxes. Provides a continuous DGND return path for I2S clock/data traces on In1.Cu. Extended north to y=25 to cover clock fan-out trunks entering at y=26–27.

**DGND stitching vias:** A column of 13 DGND through vias at x=74.5 (just inside the digital zone boundary) connects F.Cu, In1.Cu, and B.Cu DGND pours. Creates a low-impedance ground wall at the moat entry for digital return currents.

**Ground guard traces:** Six DGND traces on In1.Cu run horizontally between signal groups (at y=25, 28, 33, 38.5, 44.5, 49.5), ensuring continuous ground reference between adjacent signal trunks even where the DGND corridor pour is slotted.

**Routing rules:**
- I2S clocks (MCLK, BCLK, LRCK): routed on In1.Cu as single fan-out trunks. One horizontal trunk crosses the moat, then a vertical backbone distributes to all 4 ES8388 vias. Backbone columns: LRCK at x=78.5, BCLK at x=79.5, MCLK at x=81.5.
- I2S data (ADCDAT_A-D, DACDAT): routed on In1.Cu as individual trunks to each ES8388.
- I2C (SDA, SCL, SDA2, SCL2): routed on **In2.Cu** (separate layer from I2S) to prevent coupling from I2S clock edges. Individual trunks, vias at x=76.5 (SDA) and x=75.5 (SCL).
- MUX control (MUX_A, MUX_B, MUX_INH): routed on In1.Cu as individual trunks.
- F.Cu in the analog zone reserved for short via-to-pad stubs only (1–3mm). No long digital runs on surface layers in the analog zone.

### Battery

- Recommended: 103450 LiPo, ~2000mAh, 10x34x50mm
- Connector: JST-PH 2.0mm 2-pin
- Runtime: ~4.5-5 hours at ~430mA average
- VBAT monitoring: 100k/100k voltage divider -> master GPIO36
- Firmware undervoltage cutoff: 3.5V

---

## 4. Analog Front End (Preamp/AFE Board)

The AFE board handles all 8 pickup inputs. Each channel is identical. The board runs entirely on 3.3V AVDD with a virtual ground at 1.65V.

### Virtual Ground Generation

- 10k/10k divider from AVDD to GND -> 1.65V mid-rail
- Buffered by NE5532 voltage follower (U_VGND)
- Decoupled with 47uF + 100nF to GND
- AC reference for all audio coupling on the AFE board

### Per-Channel Signal Chain (x8)

```
Pickup input
  |
  v
10nF input coupling cap (C0G/film)
  |
  v
1M bias resistor to VGND (sets input impedance)
  |
  v
NE5532 voltage follower (input buffer)
  |
  +---> Direct output tap: 10uF coupling -> 600R series -> 2-pin solder pads
  |
  v
Non-inverting gain stage: NE5532, gain = 1 + Rf/Rg
  Rg = 1k fixed, Rf = 0-10k trimpot (0 to 21dB)
  |
  v
Sallen-Key 2nd-order Butterworth anti-alias filter
  fc ~ 21.2kHz, Q = 0.707, 12dB/octave rolloff
  R1 = R2 = 7.5k, C1 = C2 = 1nF (C0G/NP0)
  NE5532 voltage follower as unity-gain buffer
  |
  v
10uF output coupling cap -> SIGNAL net
```

### Op-Amp Count (AFE Board)

| Stage | Qty (NE5532 dual ICs) | Sections Used |
|-------|----------------------|---------------|
| Input buffers | 4 | 8 (paired 1+2, 3+4, 5+6, 7+8) |
| Variable gain preamp | 4 | 8 |
| Anti-alias filter (Sallen-Key) | 4 | 8 |
| Virtual ground buffer | 1 | 1 (1 spare) |
| **Total** | **13x NE5532** | **25 used, 1 spare** |

Direct outputs tap directly from the input buffer output (no dedicated buffer ICs). The NE5532 input buffer drives both the gain stage (high-Z input) and the direct output path (600R series protection). This is safe because the combined load is well within the NE5532's drive capability.

### Connectors (AFE Board)

| Ref | Type | Function |
|-----|------|----------|
| J_IN1-J_IN8 | 2-pin headers (2.54mm THT) | Pickup inputs |
| J_DOUT1-J_DOUT8 | 2-pin solder pad headers (2.54mm THT) | Direct outputs (wire soldering) |
| J_OUT | 2x5 header (2.54mm THT) | 8 signals + VBAT + GND to MAIN board |
| J_PWR | 2-pin header | VBAT + GND power input (feeds local LP2985) |
| H1-H2 | M3 mounting holes | Board mounting |

---

## 5. MAIN Board — Zone A: Digital

### Master ESP32-S3-DevKitC-1

Board: ESP32-S3 DevKit N16R8 (16MB flash, 8MB PSRAM), mounted in 2x 20-pin machined header sockets.

#### Responsibilities

- Generate I2S master clocks (MCLK, BCLK, LRCK) for both ES8388 ICs
- Receive 8-channel ADC data from both ES8388s over I2S
- Run pitch detection (bitstream autocorrelation) and amplitude tracking on all 8 channels (synth mode)
- Pack control data or route raw audio into forward I2S TDM slots
- Receive I2S audio returns from all 4 slaves
- Software mix all streams into final stereo output
- Drive ES8388 #3 DAC section via I2S (DACDAT → GPIO13)
- Control analog routing matrix (CD4052B) via GPIOs
- Monitor LiPo battery voltage via ADC
- Handle footswitch inputs for mode switching
- Initiate OTA firmware updates to slave boards

#### Master GPIO Assignments

**I2S — ES8388 ADC Input (Peripheral 0):**

| GPIO | Signal | Notes |
|------|--------|-------|
| 5 | MCLK | 12.288MHz at 48kHz Fs (via 33R series termination) |
| 6 | BCLK | Bit clock (via 33R series termination) |
| 7 | LRCK | Word select (via 33R series termination) |
| 15 | ADCDAT_A | ES8388 #1 data out (CH 1-2) |
| 16 | ADCDAT_B | ES8388 #2 data out (CH 3-4) |
| 4 | ADCDAT_C | ES8388 #3 data out (CH 5-6) |
| 48 | ADCDAT_D | ES8388 #4 data out (CH 7-8); shares DevKit onboard RGB LED pin |

**I2S — Slave Bus (Peripheral 1, TDM):**

| GPIO | Signal | Direction | Notes |
|------|--------|-----------|-------|
| 8 | BCLK_OUT | Out | Shared bit clock to all slaves |
| 9 | LRCK_OUT | Out | Shared word select to all slaves |
| 10 | DIN_A | In | Return audio from slave 1 (strings 1+2) |
| 11 | DIN_B | In | Return audio from slave 2 (strings 3+4) |
| 12 | DIN_C | In | Return audio from slave 3 (strings 5+6) |
| 14 | DIN_D | In | Return audio from slave 4 (strings 7+8) |
| 17 | SD_FWD_AB | Out | Forward data to slaves 1+2 (pin-muxed UART TX for OTA) |
| 18 | SD_FWD_CD | Out | Forward data to slaves 3+4 (pin-muxed UART RX for OTA) |
| 13 | DACDAT | Out | Final stereo mix to ES8388 #3 DSDIN |

**I2C — Codec Control:**

| GPIO | Signal | Notes |
|------|--------|-------|
| 21 | SDA | I2C bus 0: ES8388 #1 @0x10, ES8388 #2 @0x11 |
| 38 | SCL | I2C bus 0: 4.7k pull-ups to AVDD |
| 43 | SDA2 | I2C bus 1: ES8388 #3 @0x10, ES8388 #4 @0x11 |
| 44 | SCL2 | I2C bus 1: 4.7k pull-ups to AVDD |

**Analog Routing Matrix (CD4052B):**

| GPIO | Signal | Notes |
|------|--------|-------|
| 45 | MUX_A | Address bit 0 |
| 46 | MUX_B | Address bit 1 |
| 35 | MUX_INH | Inhibit (mute during switching) |

**OTA Flash Control:**

| GPIO | Signal | Target |
|------|--------|--------|
| 2 | BOOT_SLAVE2 | Slave 1 GPIO0 |
| 1 | BOOT_SLAVE3 | Slave 2 GPIO0 |
| 42 | BOOT_SLAVE4 | Slave 3 GPIO0 |
| 47 | BOOT_SLAVE5 | Slave 4 GPIO0 |
| 41 | EN_SLAVE2 | Slave 1 RST |
| 40 | EN_SLAVE3 | Slave 2 RST |
| 39 | EN_SLAVE4 | Slave 3 RST |
| 37 | EN_SLAVE5 | Slave 4 RST |

**Miscellaneous:**

| GPIO | Signal | Notes |
|------|--------|-------|
| 36 | VBAT_MON | Battery voltage divider (100k/100k, VBAT * 0.5) |
| 19 | NC | USB D- — used internally by DevKit USB-C |
| 20 | NC | USB D+ — used internally by DevKit USB-C |
| 48 | RGB LED | Onboard status LED |
| 43 | U0TXD | Reserved for USB debug |
| 44 | U0RXD | Reserved for USB debug |
| 3 | LOG | Boot log output, do not connect |
| 0 | BOOT | Reserved |

### Slave ESP32 Sockets (x4)

Four ESP32-S3 DevKitC-1 modules (N16R8), each mounted in 2x 1x8 machined pin header sockets positioned at the board edges so the DevKit boards hang over the edge. Direct on-board traces — no cables.

- **Slaves A+B** (strings 1-4): sockets at top edge, DevKits hang over the top (headers rotated 180°)
- **Slaves C+D** (strings 5-8): sockets at bottom edge, DevKits hang over the bottom

#### String Assignment

| Board | Core 0 | Core 1 | Forward Line | Return Line |
|-------|--------|--------|-------------|-------------|
| ESP32 #2 (Slave A) | String 1 | String 2 | SD_FWD_AB (slots 0,1) | DIN_A (GPIO10) |
| ESP32 #3 (Slave B) | String 3 | String 4 | SD_FWD_AB (slots 2,3) | DIN_B (GPIO11) |
| ESP32 #4 (Slave C) | String 5 | String 6 | SD_FWD_CD (slots 4,5) | DIN_C (GPIO12) |
| ESP32 #5 (Slave D) | String 7 | String 8 | SD_FWD_CD (slots 6,7) | DIN_D (GPIO14) |

#### Slave Header Pinout

**Left header (1x8):**

| Pin | DevKit Pin | Signal | Notes |
|-----|-----------|--------|-------|
| 1 | 3V3 | DVDD | Power |
| 2 | 3V3 | DVDD | Second power pin |
| 3 | RST | EN_SLAVEn | Master-controlled reset |
| 4 | GPIO4 | NC | Spare |
| 5 | GPIO5 | BCLK_OUT | I2S bit clock |
| 6 | GPIO6 | LRCK_OUT | I2S word select |
| 7 | GPIO7 | DIN_x | I2S DOUT (slave -> master) |
| 8 | GPIO15 | NC | Spare |

**Right header (1x8):**

| Pin | DevKit Pin | Signal | Notes |
|-----|-----------|--------|-------|
| 1 | GND | DGND | Ground |
| 2 | GPIO43 | NC | Debug only |
| 3 | GPIO44 | NC | Debug only |
| 4 | GPIO1 | NC | Spare |
| 5 | GPIO2 | NC | Spare |
| 6 | GPIO42 | NC | Spare |
| 7 | GPIO41 | UART_SLAVE_TX | OTA/debug only (wired-OR, 10k pull-up) |
| 8 | GPIO40 | SD_FWD_xx | I2S DIN (forward audio/control from master) |

#### WiFi Policy

WiFi and Bluetooth are disabled on all slave boards at firmware level to eliminate ~200mA transmit current spikes and DVDD voltage droop.

---

## 6. MAIN Board — Zone B: ADC Analog

### ES8388 Codec Configuration

Four ES8388 ICs provide 8 ADC channels total (2 per IC — ES8388 is a stereo codec). ES8388 #3 also provides the stereo DAC output. All four share the same I2S clock bus (MCLK, BCLK, LRCK). Two I2C buses handle the address conflict (only two I2C addresses available per IC: 0x10 and 0x11).

| Parameter | Value |
|-----------|-------|
| ADC resolution | 24-bit (truncated to 16-bit on I2S TDM bus) |
| ADC SNR | 93 dBFS typical |
| DAC SNR | 90 dBFS typical (ES8388 #3 only) |
| Sample rate | 48kHz |
| MCLK | 12.288MHz (256x Fs) |
| I2S format | Standard I2S, 16-bit word length |

**I2C Bus 0 (SDA GPIO21, SCL GPIO38):**

| IC | I2C Address | AD0 | Channels | ADC Data Out |
|----|-------------|-----|----------|--------------|
| ES8388 #1 (U_ADC1) | 0x10 | AGND | CH1+2 (LIN1/RIN1) | ADCDAT_A → GPIO15 |
| ES8388 #2 (U_ADC2) | 0x11 | AVDD via 10k | CH3+4 (LIN1/RIN1) | ADCDAT_B → GPIO16 |

**I2C Bus 1 (SDA2 GPIO43, SCL2 GPIO44):**

| IC | I2C Address | AD0 | Channels | ADC Data Out | DAC |
|----|-------------|-----|----------|--------------|-----|
| ES8388 #3 (U_ADC3) | 0x10 | AGND | CH5+6 (LIN1/RIN1) | ADCDAT_C → GPIO4 | Active: LOUT1/2 + ROUT1/2 |
| ES8388 #4 (U_ADC4) | 0x11 | AVDD via 10k | CH7+8 (LIN1/RIN1) | ADCDAT_D → GPIO48 | Powered down |

LIN2/RIN2 inputs are unused on all four ICs (left floating). DAC sections on ES8388 #1, #2, and #4 are powered down via register.

### J_AFE Connector

2x5 pin header (2.54mm THT): receives single cable from Preamp J_OUT.

| Pin | Signal |
|-----|--------|
| 1-8 | SIG_CH1 through SIG_CH8 |
| 9 | VBAT (powers preamp local LP2985) |
| 10 | AGND |

SIGNAL lines route to **both** ES8388 ADC inputs **and** Zone C summing amp inputs — this is the key benefit of board unification.

---

## 7. MAIN Board — Zone C: DAC / Output Analog

### ES8388 #3 DAC Output

ES8388 #3 (U_ADC3) provides the stereo DAC output. Its DAC section is enabled via I2C register; the other three ES8388s have DAC sections powered down.

| Parameter | Value |
|-----------|-------|
| DAC SNR | 90 dBFS typical |
| DAC THD | -85dB typical |
| Line output | ~1Vrms |
| Interface | I2S (shared BCLK/LRCK with ADC section) + I2C bus 1 |
| I2C address | 0x10 on bus 1 |
| Package | QFN-28 (same as ADC ICs) |

**Connections:**
- I2S DAC input: DACDAT from master GPIO13 → ES8388 #3 DSDIN
- BCLK/LRCK: shared with ADC I2S bus
- LOUT1/ROUT1 → headphone output (via 47uF coupling caps + volume pot + 3.5mm TRS jack)
- LOUT2/ROUT2 → line output (via 10uF coupling caps + 3.5mm TRS jack)

### Headphone Output

- ES8388 #3 LOUT1/ROUT1 -> 47uF AC coupling caps -> 10k audio taper dual pot -> 3.5mm TRS stereo jack (J_HP)

### Line Output

- ES8388 #3 LOUT2/ROUT2 -> 10uF AC coupling caps -> 3.5mm TRS stereo jack (J_LINE)

### Virtual Ground Generation (MAIN Board)

- 10k/10k divider from AVDD to AGND -> 1.65V mid-rail (VGND)
- No buffer needed — only load is 2 op-amp non-inverting inputs (negligible current)
- Decoupled with 47uF + 100nF to AGND (low impedance at audio frequencies)
- AC reference for summing amplifier inverting stages (single-supply NE5532 requires mid-rail bias)

### Analog Summing Amplifier (Dry Path)

Two NE5532 dual op-amps sum 8 channels to two mono outputs. Summing amp non-inverting inputs reference VGND (1.65V mid-rail) for correct bipolar signal swing with single-supply AVDD/AGND.

- **Output A:** SIG_CH1-CH4 through 10k input resistors -> inverting summing node (virtual ground at VGND) -> 1.2k feedback (unity gain of 4-input sum)
- **Output B:** SIG_CH5-CH8 through 10k input resistors -> inverting summing node (virtual ground at VGND) -> 1.2k feedback

Output buffers: NE5532 voltage followers (U_OUTBUF)

### Analog Routing Matrix (2x CD4052B)

Two CD4052B dual 4:1 analog muxes with shared control lines. MUX1 selects the primary signal; MUX2 provides the synth signal for passive summing in Hybrid mode. Both mux outputs are summed through matched 1k resistors at a common filter node before the output stage.

**MUX1 Input Wiring:**

| MUX_A | MUX_B | MUX1 X (→ Output A) | MUX1 Y (→ Output B) |
|-------|-------|---------------------|---------------------|
| 0 | 0 | Dry sum A | Dry sum B |
| 1 | 0 | DAC synth L | DAC synth R |
| 0 | 1 | Dry sum A | Dry sum B |
| 1 | 1 | Dry sum A | DAC synth R |

**MUX2 Input Wiring:**

| MUX_A | MUX_B | MUX2 X | MUX2 Y | Purpose |
|-------|-------|--------|--------|---------|
| 0 | 0 | AGND | AGND | Silent — no contribution |
| 1 | 0 | AGND | AGND | Silent — MUX1 handles synth |
| 0 | 1 | DAC synth L | DAC synth R | Summed with MUX1 dry signal |
| 1 | 1 | AGND | AGND | Silent — MUX1 handles split |

**Combined Output (after passive summing):**

| MUX_A | MUX_B | Mode | J_OUT_A | J_OUT_B |
|-------|-------|------|---------|---------|
| 0 | 0 | Dry only | Summed dry A | Summed dry B |
| 1 | 0 | Synth only | DAC synth L | DAC synth R |
| 0 | 1 | Hybrid | Dry A + synth L | Dry B + synth R |
| 1 | 1 | Wet/dry split | Dry A | Synth (DAC R) |

**Passive summing topology:** MUX1 and MUX2 outputs each pass through a 1k resistor to a common summing node. In non-hybrid modes, MUX2 outputs AGND (0V AC), contributing nothing. In hybrid mode, both dry (MUX1) and synth (MUX2) signals are summed at equal levels. A 100nF shunt cap on the summing node provides RC click suppression.

**Hybrid mix ratio control:** The synth level in the mix is digitally controllable via ES8388 #3 LOUT2/ROUT2 output volume registers (I2C, 0 to -46.5dB in 1.5dB steps). The dry signal level is fixed. This also affects J_LINE level since LOUT2/ROUT2 feed both paths, but J_LINE is not typically used in hybrid mode.

MUX_INH asserted briefly during switching to prevent clicks.

### Main Output Stage

- Summing node -> 47uF coupling cap -> 1k series resistor -> 6.35mm TS jack
- Two outputs: J_OUT_A and J_OUT_B (2-pin headers: Tip + GND)
- Two footswitch connectors: J_FS1, J_FS2 (2-pin headers)

---

## 8. I2S TDM Bus Architecture (v2.2)

All master<->slave communication runs on I2S Peripheral 1 with 8 TDM slots of 16 bits each.

- BCLK = 48000 x 16 x 8 = 6.144 MHz
- I2S Peripheral 0: ADC input (2 SD lines from ES8388s, shared BCLK/LRCK)
- I2S Peripheral 1: slave returns (4 SD inputs) + forward data (2 SD outputs) + DAC output (1 SD output)

### TDM Slot Mapping

| Slot | String | Forward Line | Return Line | Slave |
|------|--------|-------------|-------------|-------|
| 0 | 1 | SD_FWD_AB | SD_RET1 (DIN_A) | Slave A, Core 0 |
| 1 | 2 | SD_FWD_AB | SD_RET1 (DIN_A) | Slave A, Core 1 |
| 2 | 3 | SD_FWD_AB | SD_RET2 (DIN_B) | Slave B, Core 0 |
| 3 | 4 | SD_FWD_AB | SD_RET2 (DIN_B) | Slave B, Core 1 |
| 4 | 5 | SD_FWD_CD | SD_RET3 (DIN_C) | Slave C, Core 0 |
| 5 | 6 | SD_FWD_CD | SD_RET3 (DIN_C) | Slave C, Core 1 |
| 6 | 7 | SD_FWD_CD | SD_RET4 (DIN_D) | Slave D, Core 0 |
| 7 | 8 | SD_FWD_CD | SD_RET4 (DIN_D) | Slave D, Core 1 |

### 16-Bit Slot Width

ESP32-S3 I2S TDM supports max 4 slots at 32-bit or 8 slots at 16-bit. 16-bit selected to accommodate all 8 channels. The ES8388 24-bit ADC output is truncated to 16 bits (96dB dynamic range), which exceeds guitar pickup SNR (60-80dB) and is CD quality for effects processing.

### Synth Mode Control Word Packing

Interleaved frames on consecutive I2S samples:

| Frame | Bits | Content |
|-------|------|---------|
| Even (N) | [15:0] | Pitch — unsigned 16-bit, units of 0.01 Hz (44000 = 440.00 Hz) |
| Odd (N+1) | [15:2] | Amplitude — unsigned 14-bit peak (0x0000-0x3FFF) |
| | [1:0] | Gate — 00=OFF, 01=SUSTAIN, 10=ONSET, 11=reserved |

Effective update rate: 24kHz (one complete tuple every 2 frames). Far exceeds pitch detector output rate (~40-750Hz).

### UART Retention

UART is no longer used for real-time data. Retained for:
- **OTA firmware updates** (master pin-muxes GPIO17 to UART TX, ~5 sec per update)
- **Debug logging** (slave GPIO41 UART TX, does not conflict with I2S)
- **Mode switching** (single-byte command, <1ms interruption)

Pin muxing via ESP32-S3 GPIO matrix — purely firmware register writes, no hardware change.

---

## 9. Firmware

### Master DSP Pipeline (per block, all 8 channels)

| Step | Operation | CPU Cost |
|------|-----------|----------|
| 1 | DMA delivers 16-bit samples from ES8388s | Zero (hardware) |
| 2 | Peak amplitude detection (8 channels) | <1% |
| 3 | Convert to 1-bit bitstream (sign extraction) | ~1-2% |
| 4 | Bitstream autocorrelation (8 channels) | ~15-25% |
| 5 | Peak picking and pitch estimation | ~2-5% |
| 6 | Pack I2S TDM forward frames | <1% |

Total Core 0 load: ~20-35% at 48kHz. Substantial headroom for future additions.

### Pitch Detection

Bitstream autocorrelation (not YIN). Converts ADC samples to 1-bit sign, computes autocorrelation using XNOR and popcount on packed 32-bit words. Low CPU and memory footprint, suitable for all 8 channels on a single core.

### Gate States

| Value | State | Meaning |
|-------|-------|---------|
| 0x00 | OFF | String silent, slaves enter release phase |
| 0x01 | SUSTAIN | String sounding, pitch stable |
| 0x02 | ONSET | New note detected, slaves trigger attack phase (one frame only) |

### Slave DSP — Synth Mode (per core)

```
I2S DIN (control data) -> latch pitch/amplitude/gate
  |
  v
Oscillator Engine (DDS, 32-bit phase accumulator)
  - Waveforms: sine / sawtooth / square / triangle / wavetable
  - Portamento filtering on pitch
  - ADSR envelope triggered by gate signal
  - Optional sub-oscillator (octave-down)
  |
  v
Filter Stage (biquad IIR, state-variable)
  - Types: LPF, HPF, BPF, notch
  - Optional cutoff ADSR envelope
  - Optional keyboard tracking
  - Q: 0.5 to 10
  |
  v
I2S DMA buffer -> DOUT to master
```

### Slave DSP — Effects Mode (per core)

~5,000 cycles per sample per channel (240MHz / 48kHz). Enough for:
- 10-band parametric EQ + HP/LP filter
- Dynamics processing (compressor/gate)
- Modulation effects
- Short delay/reverb (using 8MB PSRAM for buffers)

### OTA Firmware Update

Slaves ship with custom OTA bootloader. All subsequent updates delivered by master over UART (GPIO17, pin-muxed at runtime).

**Partition table (16MB flash):**
- nvs (16kB) — config, string ID, tuning
- otadata (8kB) — active OTA partition tracking
- app0/OTA_0 (4MB) — running firmware
- app1/OTA_1 (4MB) — master writes new firmware here

**UART protocol (GPIO40 RX):**
- Normal: 0xAA [data] [checksum] 0x55
- OTA trigger: 0xBE 0xEF [firmware size 4B]
- OTA data: raw binary blocks with CRC per block
- OTA complete: 0xDE 0xAD -> slave reboots

Uses esp-serial-flasher library (Espressif). Update takes ~5 seconds.

---

## 10. Output Connector Inventory

| Output | Qty | Type | Board | Signal |
|--------|-----|------|-------|--------|
| Direct outs | 8 | 2-pin solder pads | Preamp | Per-string pickup tap |
| Main A | 1 | 6.35mm TS | MAIN | Routing matrix output A (ch 1-4 dry sum) |
| Main B | 1 | 6.35mm TS | MAIN | Routing matrix output B (ch 5-8 dry sum) |
| Line out | 1 | 3.5mm TRS stereo | MAIN | ES8388 #3 DAC line output |
| Headphone | 1 | 3.5mm TRS stereo | MAIN | ES8388 #3 DAC HP output (with pot) |
| Footswitches | 2 | 2-pin headers | MAIN | Mode selection |

---

## 11. Bill of Materials (Key Components)

| Qty | Component | Part | Function |
|-----|-----------|------|----------|
| 5 | Microcontroller | ESP32-S3 DevKit N16R8 | 1x master, 4x slave |
| 4 | Audio ADC/DAC codec | ES8388 (JLCPCB C365736, $0.95) | Stereo 2-ch ADC; #3 also active as DAC out |
| 1 | LiPo charger | MCP73831T-2ACI/OT | USB-C to LiPo charging |
| 2 | Analog LDO | LP2985-33DBVR (SOT-23-5) | 3.3V AVDD, ultra-low noise (1x MAIN, 1x Preamp) |
| 1 | Digital LDO | AP2114H-3.3 (SOT-223) | 3.3V DVDD, 1A max |
| 1 | Reverse protection | BAT54 Schottky | VBAT protection |
| 2 | Analog mux | CD4052B | Output routing matrix |
| 13 | Dual op-amp (AFE) | NE5532 (SOIC-8) | Buffers, gain, filters, VGND |
| 2 | Dual op-amp (MAIN) | NE5532 | Summing amp + output buffer |
| 8 | Gain trimpot | Bourns 3314J-1-103E (SMD, 10k) | Per-channel gain trim |
| 1 | Ferrite bead | 220 Ohm, 0805 | AGND/DGND bridge |
| 2 | Audio pot | 10k audio taper | Headphone volume (dual ganged) |
| — | ~~USB-C connector~~ | — | Removed — DevKit USB-C provides charging + data |
| 1 | Battery connector | JST-PH 2.0mm 2-pin | LiPo connection |
| 8 | Solder pad header | 2-pin 2.54mm THT | Direct outputs (Preamp) |
| 2 | Stereo jack | 3.5mm TRS | Line + headphone out (MAIN) |
| 1 | LiPo cell | 103450, ~2000mAh | Main power |

---

## 12. PCB Layout Rules

- 4-layer stackup: F.Cu (signal+ground pours) / In1.Cu (DGND plane+corridor) / In2.Cu (AGND plane) / B.Cu (signal+ground pours)
- Separate AGND and DGND pours, star connection via ferrite bead FB1
- 4mm moat between digital and analog zones on F.Cu/B.Cu
- I2S clocks cross moat via fan-out: 1 trunk + vertical backbone per clock on In1.Cu (3 crossings total, not 12)
- I2S data (ADCDAT, DACDAT) routed on In1.Cu as individual trunks with DGND corridor return path
- I2C (SDA, SCL, SDA2, SCL2) routed on In2.Cu — separate layer from I2S to prevent clock coupling
- 33R series termination resistors on MCLK, BCLK, LRCK near ESP32 source (reduces edge rate and EMI)
- DGND stitching vias (13x) at moat boundary (x=74.5) for low-impedance return path
- DGND guard traces on In1.Cu between signal groups
- No long digital traces on F.Cu/B.Cu in the analog zone (x>79mm) — stubs only
- ESP32-S3 antenna clearance: met by devkit-on-headers elevation (>3mm above PCB copper)
- Slave ESP32 sockets placed at board edges — DevKits overhang top (slaves A+B) and bottom (slaves C+D)
- ESP32-S3 USB-C ports must remain accessible after assembly (initial flash)
- ES8388 power pins: 100nF ceramic + 10uF as close as possible
- ES8388 DVDD/DGND decoupling routed back through DGND corridor, not tied to AGND locally
- I2S forward data lines (GPIO17/18): keep short, avoid adjacent noisy lines

### JLCPCB Assembly Notes

- Assembly type: Economic PCBA where possible
- ESP32-S3 DevKits: NOT assembled by JLCPCB — hand insert into headers after delivery
- Mark all ESP32 header footprints DNF in BOM
- Extended components (ES8388 C365736): $1.50 setup fee per unique part type
- THT items for hand soldering: headers, TRS jacks, JST connector, USB-C
- Gain trimpots (Bourns 3314J) are SMD — include in JLCPCB BOM/CPL

---

## 13. Open Items

| # | Item | Status |
|---|------|--------|
| 1 | Review AFE board dimensions with 13x NE5532 + passives — target ~100x60mm | OPEN |
| 2 | Determine latency impact of pin-muxing GPIO17/18 between I2S and UART for mode switch | LOW RISK |
| 3 | GPIO48 shares DevKit onboard RGB LED — verify ES8388 #4 ADCDAT_D signal integrity with LED load | LOW RISK |

### Resolved Items

- I2S return from 4 slaves via TDM mode (4 SD lines on Peripheral 1) — **RESOLVED**
- 16-bit TDM slot width selected (hardware constraint, 8 slots per peripheral) — **RESOLVED**
- I2S full-duplex TDM on slave (TX + RX share BCLK/LRCK, confirmed by ESP-IDF) — **RESOLVED**
- HT8988A availability (not in JLCPCB stock) — **RESOLVED** (replaced by ES8388 #3 DAC section)
- HT8988A I2C address conflict with ES8388s — **RESOLVED** (HT8988A removed; two I2C buses handle 4x ES8388)
- ES8388 assumed 4-ch ADC — **CORRECTED** (stereo 2-ch per IC; 4x ICs for 8 channels)
- Synth mode control word packing (interleaved frames, 24kHz update rate) — **RESOLVED**
- RC click suppression on mux outputs — **IMPLEMENTED** (1k + 100nF per output)
- Footswitch pinouts — **DECIDED** (one per mode, user wires as appropriate)
- AP2112K 600mA limit — **RESOLVED** (upgraded to AP2114H-3.3, 1A max)
- Op-amp consolidation — **RESOLVED** (all NE5532 on AFE board)
- Output connector type — **RESOLVED** (2-pin solder pads for direct outs, 6.35mm TS for main, 3.5mm TRS for line/HP)
- UART replaced by I2S TDM for real-time data — **RESOLVED** (v2.2)

---

*End of Definitive Specification — Version 2.10*
