# 8-Channel Per-String Guitar Pickup System — Definitive Specification

**Version 2.4 — 17 March 2026**

Consolidates: `pcb_spec_v2.0.md`, `pcb_revision_brief_v2.1.md`, `pcb_revision_brief_v2.2.md`

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

The system uses 2x ES8388 codec ICs for ADC, 5x ESP32-S3 microcontrollers (1 master + 4 slaves) for DSP, and an HT8988A codec for the final stereo DAC output with built-in headphone amplifier. Power is supplied by a single-cell LiPo battery charged via USB-C.

### Boards

| Board | Source | Components | Layers | Size | Description |
|-------|--------|------------|--------|------|-------------|
| **MAIN** | `boards/main/main.zen` | ~113 | 4 | ~160x80mm | Merged master + ADC + DAC-router + 4x slave sockets |
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
  -> HT8988A DAC -> Outputs
```

### Effects Mode

```
Pickups -> AFE -> ES8388 ADC (I2S to master)
  -> Master: routes raw 16-bit audio into forward TDM slots (no pitch detection)
  -> I2S to slaves
  -> Slaves: per-string effects (EQ, dynamics, modulation, delay)
  -> I2S return to master
  -> Master mixes -> HT8988A DAC -> Outputs
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

The system runs entirely from a single-cell LiPo battery (3.7V nominal). USB-C is for charging only. There is no 5V rail. Slave ESP32 DevKits are powered directly from the 3.3V DVDD rail, bypassing their onboard LDOs.

```
USB-C VBUS (5V)
  |
  v
MCP73831T-2ACI/OT (SOT-23-5, ~210mA charge current)
  |
  v
LiPo Cell (single cell, 3.7V nom, 4.2V full, 3.5V cutoff)
  |
  +---> LP2985-33DBVR --> 3.3V AVDD (analog, ultra-low noise, ~30uV RMS)
  +---> AP2114H-3.3   --> 3.3V DVDD (digital, 1A max)
```

### MCP73831 Charger

- Package: SOT-23-5
- RPROG = 4.7k -> ~210mA charge current
- STAT pin -> charge status LED (active-low open-drain)
- BAT54 Schottky reverse protection on VBAT line
- Decoupling: 47uF + 100nF on VBAT output

### Analog Rail — LP2985-33DBVR (AVDD)

- Package: SOT-23-5
- Output: 3.3V AVDD, ~30uV RMS noise
- Feeds: ES8388 AVDD, all AFE op-amps, virtual ground, HT8988A analog pins
- 10nF bypass cap on BYP pin (per datasheet)
- Copper pour: AGND, separate from DGND

### Digital Rail — AP2114H-3.3 (DVDD)

- Package: SOT-223, 1A max output
- Output: 3.3V DVDD
- Feeds: 5x ESP32-S3 DevKits (~80mA each), ES8388 DVDD, HT8988A digital pins
- Current budget: ~430mA typical, ~580mA peak
- Decoupling: 22uF bulk + standard 100nF/10uF
- Copper pour: DGND, separate from AGND

### Ground Planes (CRITICAL)

- AGND and DGND are separate copper pours on all boards
- Connected at exactly ONE star point via ferrite bead FB1 (220 Ohm, 0805) on the MAIN board
- No digital traces cross the AGND pour
- No analog traces cross the DGND pour
- ES8388 AGND/DGND pins connect to their respective pours
- All op-amp ground pins connect to AGND only
- Preamp board uses single `GND` net (pure analog)

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
| J_OUT | 2x5 header (2.54mm THT) | 8 signals + AVDD + GND to MAIN board |
| J_PWR | 2-pin header | AVDD + GND power input |
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
- Drive HT8988A output DAC via I2S
- Control analog routing matrix (CD4052B) via GPIOs
- Monitor LiPo battery voltage via ADC
- Handle footswitch inputs for mode switching
- Initiate OTA firmware updates to slave boards

#### Master GPIO Assignments

**I2S — ES8388 ADC Input (Peripheral 0):**

| GPIO | Signal | Notes |
|------|--------|-------|
| 5 | MCLK | 12.288MHz at 48kHz Fs |
| 6 | BCLK | Bit clock |
| 7 | LRCK | Word select |
| 15 | ADCDAT_A | ES8388 #1 data out (CH 1-4) |
| 16 | ADCDAT_B | ES8388 #2 data out (CH 5-8) |

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
| 13 | DOUT_DAC | Out | Final stereo mix to HT8988A |

**I2C — Codec Control:**

| GPIO | Signal | Notes |
|------|--------|-------|
| 21 | SDA | Shared: ES8388 #1 @0x10, ES8388 #2 @0x11, HT8988A @0x1A |
| 38 | SCL | 4.7k pull-ups to AVDD |

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
| 19 | USB_DN | USB native D- |
| 20 | USB_DP | USB native D+ |
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

Two ES8388 ICs provide 8 ADC channels total (4 per IC). Both share the same I2S clock bus and I2C control bus.

| Parameter | Value |
|-----------|-------|
| ADC resolution | 24-bit (truncated to 16-bit on I2S TDM bus) |
| ADC SNR | 93 dBFS typical |
| Sample rate | 48kHz |
| MCLK | 12.288MHz (256x Fs) |
| I2S format | Standard I2S, 16-bit word length |

**ES8388 #1 (U_ADC1):**
- Channels 1-4 (strings 1-4)
- I2C address: 0x10 (AD0 -> AGND)
- Inputs: LIN1=SIG_CH1, RIN1=SIG_CH2, LIN2=SIG_CH3, RIN2=SIG_CH4
- Data output: ADCDAT_A -> master GPIO15

**ES8388 #2 (U_ADC2):**
- Channels 5-8 (strings 5-8)
- I2C address: 0x11 (AD0 -> AVDD via 10k)
- Inputs: LIN1=SIG_CH5, RIN1=SIG_CH6, LIN2=SIG_CH7, RIN2=SIG_CH8
- Data output: ADCDAT_B -> master GPIO16

DAC sections powered down via register — not used.

### J_AFE Connector

2x5 pin header (2.54mm THT): receives single cable from Preamp J_OUT.

| Pin | Signal |
|-----|--------|
| 1-8 | SIG_CH1 through SIG_CH8 |
| 9 | AVDD |
| 10 | AGND |

SIGNAL lines route to **both** ES8388 ADC inputs **and** Zone C summing amp inputs — this is the key benefit of board unification.

---

## 7. MAIN Board — Zone C: DAC / Output Analog

### HT8988A Codec (WM8988 Compatible)

Replaces PCM5102A from v2.0. Provides DAC output with built-in Class G headphone amplifier.

| Parameter | Value |
|-----------|-------|
| DAC SNR | 100dB (A-weighted) |
| DAC THD | -90dB |
| HP output | >40mW @ 16 Ohm, 90dB SNR |
| Line output | ~1Vrms |
| Interface | I2S + I2C control |
| I2C address | 0x1A (CSB=low, MODE=low) |
| Package | QFN-28 |

**Connections:**
- I2S: DACDAT from master GPIO13, BCLK/LRC from slave bus
- I2C: shared SDA/SCL bus
- LOUT1/ROUT1 -> headphone output (via volume pot + 3.5mm TRS jack)
- LOUT2/ROUT2 -> line output (via coupling caps + 3.5mm TRS jack)
- Analog inputs: tied to AGND (not used)

### Headphone Output

- HT8988A HP outputs -> 47uF AC coupling caps -> 10k audio taper dual pot -> 3.5mm TRS stereo jack (J_HP)

### Line Output

- HT8988A line outputs -> 10uF AC coupling caps -> 3.5mm TRS stereo jack (J_LINE)

### Analog Summing Amplifier (Dry Path)

Two NE5532 dual op-amps sum 8 channels to stereo:

- **Left channel:** SIG_CH1-CH4 through 10k input resistors -> inverting summing node -> 1.2k feedback (unity gain of 4-input sum)
- **Right channel:** SIG_CH5-CH8 through 10k input resistors -> inverting summing node -> 1.2k feedback

Output buffers: NE5532 voltage followers (U_OUTBUF)

### Analog Routing Matrix (2x CD4052B)

Two CD4052B dual 4:1 analog muxes with shared control lines.

**Output Mode Truth Table:**

| MUX_A | MUX_B | Mode | Main L Output | Main R Output |
|-------|-------|------|---------------|---------------|
| 0 | 0 | Dry only | Summed dry L | Summed dry R |
| 1 | 0 | Synth only | DAC synth L | DAC synth R |
| 0 | 1 | Hybrid | Dry + synth L | Dry + synth R |
| 1 | 1 | Wet/dry split | Dry L | Synth R |

MUX_INH asserted briefly during switching to prevent clicks. RC click suppression (1k + 100nF) on mux outputs.

### Main Output Stage

- Mux output -> 1k RC filter -> 47uF coupling cap -> 1k series resistor -> 6.35mm TRS jack
- Two outputs: J_OUT_L and J_OUT_R (3-pin headers as TRS placeholders)
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
| Main L | 1 | 6.35mm TRS | MAIN | Routing matrix output L |
| Main R | 1 | 6.35mm TRS | MAIN | Routing matrix output R |
| Line out | 1 | 3.5mm TRS stereo | MAIN | HT8988A line output |
| Headphone | 1 | 3.5mm TRS stereo | MAIN | HT8988A HP output (with pot) |
| Footswitches | 2 | 2-pin headers | MAIN | Mode selection |

---

## 11. Bill of Materials (Key Components)

| Qty | Component | Part | Function |
|-----|-----------|------|----------|
| 5 | Microcontroller | ESP32-S3 DevKit N16R8 | 1x master, 4x slave |
| 2 | Audio ADC codec | ES8388 (JLCPCB C365736) | 4ch ADC each, I2S out |
| 1 | Output DAC/codec | HT8988A (QFN-28) | Stereo DAC + headphone amp |
| 1 | LiPo charger | MCP73831T-2ACI/OT | USB-C to LiPo charging |
| 1 | Analog LDO | LP2985-33DBVR (SOT-23-5) | 3.3V AVDD, ultra-low noise |
| 1 | Digital LDO | AP2114H-3.3 (SOT-223) | 3.3V DVDD, 1A max |
| 1 | Reverse protection | BAT54 Schottky | VBAT protection |
| 2 | Analog mux | CD4052B | Output routing matrix |
| 13 | Dual op-amp (AFE) | NE5532 (SOIC-8) | Buffers, gain, filters, VGND |
| 2 | Dual op-amp (MAIN) | NE5532 | Summing amp + output buffer |
| 8 | Gain trimpot | 10k cermet | Per-channel gain trim |
| 1 | Ferrite bead | 220 Ohm, 0805 | AGND/DGND bridge |
| 2 | Audio pot | 10k audio taper | Headphone volume (dual ganged) |
| 1 | USB-C connector | — | Charging only |
| 1 | Battery connector | JST-PH 2.0mm 2-pin | LiPo connection |
| 8 | Solder pad header | 2-pin 2.54mm THT | Direct outputs (Preamp) |
| 2 | Stereo jack | 3.5mm TRS | Line + headphone out (MAIN) |
| 1 | LiPo cell | 103450, ~2000mAh | Main power |

---

## 12. PCB Layout Rules

- 4-layer stackup: Signal / GND / PWR / Signal
- Separate AGND and DGND pours, star connection via ferrite bead
- No digital traces cross AGND pour
- No copper pour under ESP32-S3 antenna clearance zone (3mm min)
- Slave ESP32 sockets placed at board edges — DevKits overhang top (slaves A+B) and bottom (slaves C+D)
- ESP32-S3 USB-C ports must remain accessible after assembly (initial flash)
- I2S clock lines (BCLK, LRCK, MCLK) routed short, matched length
- ES8388 power pins: 100nF ceramic + 10uF as close as possible
- I2S forward data lines (GPIO17/18): keep short, avoid adjacent noisy lines

### JLCPCB Assembly Notes

- Assembly type: Economic PCBA where possible
- ESP32-S3 DevKits: NOT assembled by JLCPCB — hand insert into headers after delivery
- Mark all ESP32 header footprints DNF in BOM
- Extended components (ES8388 C365736): $1.50 setup fee per unique part type
- THT items for hand soldering: headers, TRS jacks, JST connector, USB-C

---

## 13. Open Items

| # | Item | Status |
|---|------|--------|
| 1 | Confirm HT8988A JLCPCB/LCSC part number and assembly availability | OPEN |
| 2 | Confirm HT8988A I2C address (0x1A) does not conflict with ES8388s (0x10, 0x11) | OPEN |
| 3 | Review AFE board dimensions with 13x NE5532 + passives — target ~100x60mm | OPEN |
| 4 | Determine latency impact of pin-muxing GPIO17/18 between I2S and UART for mode switch | LOW RISK |

### Resolved Items

- I2S return from 4 slaves via TDM mode (4 SD lines on Peripheral 1) — **RESOLVED**
- 16-bit TDM slot width selected (hardware constraint, 8 slots per peripheral) — **RESOLVED**
- I2S full-duplex TDM on slave (TX + RX share BCLK/LRCK, confirmed by ESP-IDF) — **RESOLVED**
- Synth mode control word packing (interleaved frames, 24kHz update rate) — **RESOLVED**
- RC click suppression on mux outputs — **IMPLEMENTED** (1k + 100nF per output)
- Footswitch pinouts — **DECIDED** (one per mode, user wires as appropriate)
- AP2112K 600mA limit — **RESOLVED** (upgraded to AP2114H-3.3, 1A max)
- Op-amp consolidation — **RESOLVED** (all NE5532 on AFE board)
- Output connector type — **RESOLVED** (2-pin solder pads for direct outs, 6.35mm TRS for main, 3.5mm TRS for line/HP)
- UART replaced by I2S TDM for real-time data — **RESOLVED** (v2.2)

---

*End of Definitive Specification — Version 2.4*
