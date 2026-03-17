**PCB REVISION BRIEF**

8-Channel Per-String Guitar Pickup System

Specification Version 2.0 → 2.1

Date: 17 March 2026

Status: For Review

Supersedes: pcb_revision_brief.docx (v1.0)

# Revision Summary

This document details all changes required to move from Specification Version 2.0 to Version 2.1. Each revision is categorised by severity and the affected board(s).

| **REV \#** | **Board(s) Affected** | **Summary**                                                                                                                      |
|------------|-----------------------|----------------------------------------------------------------------------------------------------------------------------------|
| **R01**    | Master Board          | Replace AMS1117-3.3 DVDD LDO with AP2112K-3.3                                                                                    |
| **R02**    | AFE Board             | Upgrade anti-aliasing filters from single-pole RC to 2nd-order Sallen-Key                                                        |
| **R03**    | DAC + Router Board    | Replace PCM5102A with HT8988A; add headphone and line output jacks                                                               |
| **R04**    | DAC + Router Board    | All audio output connectors changed to 6.35mm (1/4") mono sockets                                                                |
| **R05**    | Master + Slave Boards | Add 4th slave ESP32 socket and pinout for strings 7+8 DSP                                                                        |
| **R06**    | Spec Cleanup          | Resolve op-amp contradictions; confirm NE5532 throughout; correct BOM                                                            |
| **R07**    | Firmware Spec         | Define UART frame format with amplitude tracking; clarify bitstream autocorrelation pitch detection; specify master DSP pipeline |

# R01 — Digital Rail LDO Replacement (CRITICAL)

## Problem

The AMS1117-3.3 specified for the DVDD rail has a typical dropout voltage of approximately 1.1V. It requires a minimum input of approximately 4.4V to regulate 3.3V. A single LiPo cell operates between 3.0V (cutoff) and 4.2V (full charge), meaning the AMS1117 cannot regulate for most of the discharge curve. The digital rail would be unregulated and drooping from the moment the cell falls below 4.4V — which is almost immediately after a full charge.

## Solution

Replace the AMS1117-3.3 with the AP2112K-3.3TRG1 (Diodes Incorporated). This is a CMOS LDO with a typical dropout of 250mV at 600mA, meaning it regulates 3.3V from an input as low as approximately 3.55V.

| **Parameter** | **AMS1117 (old)** | **AP2112K (new)** | **Notes**                                        |
|---------------|-------------------|-------------------|--------------------------------------------------|
| Package       | SOT-223           | SOT-25            | Different footprint — requires PCB layout change |
| Dropout       | ~1.1V             | ~250mV @ 600mA    | Regulatable from ~3.55V input                    |
| Max Iout      | 1A                | 600mA             | Adequate for ~500mA peak digital budget          |
| JLCPCB \#     | (various)         | C51118            | 185k+ in stock at LCSC                           |
| Price         | ~\$0.05           | ~\$0.07           | Negligible cost increase                         |

## Impact on Battery Life

The AP2112K can regulate down to approximately 3.55V input. Below this the output begins to droop, so the firmware undervoltage cutoff should be raised from 3.0V to 3.5V. On the recommended 2000mAh 103450 pouch cell, this sacrifices roughly 10–15% of usable capacity at the bottom of the discharge curve. Estimated runtime at 350mA average draw drops from approximately 5–6 hours to approximately 4.5–5 hours. This can be recovered by specifying a slightly larger cell (e.g. 2500mAh pouch).

## Changes Required

**Schematic:** Replace U_DVDD from AMS1117-3.3 (SOT-223) to AP2112K-3.3TRG1 (SOT-25). Add enable pin connection (tie EN to VIN for always-on, or route to master GPIO for power sequencing). Note the AP2112K has 5 pins (VIN, GND, EN, NC, VOUT) versus 3 functional pins on the AMS1117.

**PCB layout:** New SOT-25 footprint. Remove AMS1117 heatsink pad. The AP2112K dissipates far less heat due to lower dropout. Maintain 1µF ceramic on input plus 1µF ceramic on output (per datasheet; the 100µF electrolytic on output can remain for bulk storage).

**Firmware:** Update VBAT undervoltage threshold from 3.0V to 3.5V in battery monitoring code on master ESP32.

**BOM:** Replace 1x AMS1117-3.3 (SOT-223) with 1x AP2112K-3.3TRG1 (SOT-25, LCSC C51118). Update BOM quantity: digital LDO count is 1, not 2 (remove the duplicate entry from v2.0 BOM).

# R02 — Anti-Aliasing Filter Upgrade

## Problem

The v2.0 spec calls for a single-pole passive RC low-pass at 22kHz (22kΩ + 330pF) per channel. A single-pole filter provides only 6dB/octave rolloff. At 24kHz (the Nyquist frequency at 48kHz Fs), attenuation is less than 1dB. Pickup harmonics and electromagnetic interference above Nyquist will alias into the audible band.

While the ES8388 includes internal digital decimation filtering that provides some protection, relying solely on it is not best practice. An analog anti-aliasing filter should attenuate significantly before the ADC input.

## Solution

Replace the single-pole RC with a 2nd-order Sallen-Key low-pass filter using one section of the existing NE5532 op-amps. Target cutoff remains approximately 22kHz with a Butterworth (maximally flat) response, giving 12dB/octave rolloff. At 48kHz this provides roughly 6–7dB attenuation; combined with the ES8388 internal oversampling, aliasing artefacts are effectively eliminated.

## Component Values (per channel)

Sallen-Key unity-gain Butterworth, fc ≈ 22kHz:

| **Ref**    | **Value**                  | **Notes**                               |
|------------|----------------------------|-----------------------------------------|
| R1         | 7.15kΩ (7.5kΩ nearest E24) | Series input resistor                   |
| R2         | 7.15kΩ (7.5kΩ nearest E24) | Series input resistor                   |
| C1         | 1nF ceramic (C0G/NP0)      | Shunt cap to virtual ground             |
| C2         | 1nF ceramic (C0G/NP0)      | Feedback cap to op-amp output           |
| U (op-amp) | NE5532 (1 section per ch)  | 4x dual ICs = 8 sections for 8 channels |

## Changes Required

**AFE Board schematic:** Remove passive RC (22kΩ + 330pF) per channel. Add Sallen-Key topology using one NE5532 section per channel. 4 additional dual NE5532 ICs are needed (8 filter channels). This brings total op-amp count on the AFE board to: 4x NE5532 (input buffers) + 4x NE5532 (direct output buffers) + 4x NE5532 (preamp) + 4x NE5532 (anti-alias filters) = 16x NE5532 dual ICs.

**PCB layout:** Additional footprints for 4x NE5532 SODIPs plus 16x resistors and 16x capacitors. Use C0G/NP0 ceramic caps for frequency stability. Board area may increase; review 100x100mm constraint.

**BOM:** Add 4x NE5532 dual op-amp, 16x 7.5kΩ 0603, 16x 1nF C0G 0603. Remove 8x 22kΩ and 8x 330pF.

# R03 — Output DAC Replacement: PCM5102A → HT8988A

## Rationale

The HT8988A (HTCSEMI) is a stereo audio codec with a built-in headphone amplifier capable of driving over 40mW into 16Ω loads. It replaces the PCM5102A and eliminates the need for an external headphone amplifier IC. The HT8988A also provides separate line-level outputs, allowing both a line out and a headphone out from a single IC.

| **Parameter** | **PCM5102A (old)** | **HT8988A (new)** | **Notes**                                          |
|---------------|--------------------|-------------------|----------------------------------------------------|
| DAC SNR       | 112dB              | 100dB (A-wtd)     | Slight reduction; still excellent for guitar synth |
| DAC THD       | -93dB              | -90dB             | Comparable                                         |
| HP output     | None               | \>40mW @ 16Ω      | Built-in Class G headphone amp                     |
| HP SNR        | N/A                | 90dB @ 16Ω        | Adequate for monitoring                            |
| Line out      | 2.1Vrms            | 1Vrms (typical)   | True line level; no attenuator needed              |
| Interface     | I2S only           | I2S + I2C control | Requires I2C init; share bus with ES8388s          |
| Supply        | 3.3V DVDD          | 3.3V AVDD + DVDD  | Needs both rails; route AVDD to analog pins        |
| Package       | TSSOP-20           | QFN-28            | Different footprint                                |

## New Output Configuration

The DAC + Router Board gains two 3.5mm stereo TRS sockets on the HT8988A outputs:

**Line out (3.5mm TRS):** Connected to HT8988A LOUT/ROUT pins. Fixed line-level output suitable for feeding mixers, audio interfaces, or powered monitors.

**Headphone out (3.5mm TRS):** Connected to HT8988A HPOUTL/HPOUTR pins via a 10kΩ audio taper potentiometer for volume control. The pot is wired as a voltage divider between the HP output pins and the jack, with the wiper feeding the jack tip/ring.

These 3.5mm outputs are in addition to the main 6.35mm output jacks on the analog routing matrix.

## Changes Required

**Schematic:** Remove PCM5102A and its FMT/XSMT/SCK tie resistors. Add HT8988A with QFN-28 footprint. Route I2S (BCLK, LRCK, DIN) from master GPIO13/8/9. Add I2C (SDA/SCL) connection to shared bus (master GPIO21/38). Assign unique I2C address (consult datasheet for ADDR pin config — must not conflict with ES8388 addresses 0x10/0x11). Route LOUT/ROUT to line out jack. Route HPOUTL/HPOUTR through 10kΩ pot to headphone jack.

**PCB layout:** New QFN-28 footprint with exposed pad (connect to AGND). Add 2x 3.5mm stereo TRS socket footprints. Add 10kΩ audio taper pot footprint (9mm or 16mm, panel mount). Ensure AVDD and AGND routing to HT8988A analog pins from the analog rail.

**Firmware:** Add I2C initialisation for HT8988A on master startup: set DAC sample rate to 48kHz, I2S format, enable headphone amp, set default volume. Volume control for headphone is analog (pot), but digital volume registers can be used for mute/soft-start.

**BOM:** Remove 1x PCM5102A (TSSOP-20). Add 1x HT8988A (QFN-28). Add 2x 3.5mm stereo TRS socket. Add 1x 10kΩ audio taper potentiometer. Confirm JLCPCB/LCSC stock for HT8988A before finalising (HTCSEMI parts are stocked at LCSC but confirm assembly availability).

# R04 — Audio Output Connectors Standardised to 6.35mm

## Change

All audio output connectors on the analog routing matrix and direct output paths are standardised to 6.35mm (1/4") mono TS sockets. This replaces the previous mix of DB25, 3.5mm, and multi-pin header options discussed in the v2.0 spec.

This resolves the contradiction between sections 4.3 (3.5mm/header), 10.2 (DB25 recommended), and the open items decision (6.35mm). The decision is now final and consistent throughout.

## Connector Inventory

| **Output**  | **Qty** | **Type**          | **Signal**                            |
|-------------|---------|-------------------|---------------------------------------|
| Direct outs | 8       | 6.35mm TS mono    | Per-string buffered pickup signal     |
| Main L      | 1       | 6.35mm TRS stereo | Routing matrix output left            |
| Main R      | 1       | 6.35mm TRS stereo | Routing matrix output right           |
| Line out    | 1       | 3.5mm TRS stereo  | HT8988A line output (new, R03)        |
| Headphone   | 1       | 3.5mm TRS stereo  | HT8988A HP output with pot (new, R03) |

## Changes Required

**BOM:** Remove 1x DB25 female connector. Add 8x 6.35mm TS mono switched socket (e.g. Neutrik NJ3FP6C or Lumberg KLBM 3). Retain 2x 6.35mm TRS for main stereo output. Add 2x 3.5mm TRS stereo socket for line and headphone outs.

**Mechanical:** 8x additional 6.35mm jacks require significant panel space. Review enclosure design for jack mounting. Consider grouping the 8 direct output jacks in a row along one edge.

# R05 — 4th Slave ESP32 for Strings 7+8

## Problem

The v2.0 spec assigns strings 1–6 across three slave ESP32s (two strings per slave, one per core) but handles strings 7 and 8 with a vague note: “handled on master spare cycles, or add a fifth ESP32.” The master is already heavily loaded with pitch detection for all 8 strings, I2S mixing from 3 slaves, DAC output, mux control, battery monitoring, and OTA management. Running two additional real-time synth voices on the master is not feasible without risking audio glitches.

## Solution

Add a 4th slave board (ESP32 \#5), identical to the existing slave boards, handling strings 7 and 8 in the same two-core architecture.

| **Board**               | **Core 0**          | **Core 1**          | **I2S Return**    |
|-------------------------|---------------------|---------------------|-------------------|
| ESP32 \#2 (slave 1)     | String 1 osc+filter | String 2 osc+filter | Master GPIO10     |
| ESP32 \#3 (slave 2)     | String 3 osc+filter | String 4 osc+filter | Master GPIO11     |
| ESP32 \#4 (slave 3)     | String 5 osc+filter | String 6 osc+filter | Master GPIO12     |
| **ESP32 \#5 (slave 4)** | String 7 osc+filter | String 8 osc+filter | **Master GPIO14** |

## Changes Required

**Master board:** Add header socket for slave \#4 I2S data return on GPIO14 (DIN_D). Add OTA control GPIOs: BOOT \#5 (assign a free master GPIO) and EN \#5 (assign a free master GPIO). Extend UART1 TX broadcast wiring to include slave \#4 GPIO40. Extend shared I2S BCLK/LRCK bus to slave \#4 headers.

**Slave board:** No hardware change — the 4th slave is identical to the existing 3 slave boards. Manufacture 4 instead of 3.

**Firmware (master):** Software mixer must now sum 4 I2S return streams instead of 3. UART broadcast already reaches all slaves in parallel. OTA code needs awareness of the 4th slave ID.

**I2S peripheral architecture:** The ESP32-S3 has 2 I2S peripherals. Each peripheral supports TDM (Time Division Multiplex) mode with up to 4 SD (serial data) lines and 16 channels. The recommended configuration is: I2S peripheral 0 handles ADC input (2 SD lines from ES8388 \#1 and \#2, shared BCLK/LRCK); I2S peripheral 1 handles both slave audio returns (4 SD input lines from slaves \#2–#5 in TDM mode) and DAC output (1 SD output line to HT8988A), all on a shared BCLK/LRCK bus. The TDM BCLK for the slave return bus runs at 48000 × 32 × 8 = 12.288 MHz (8 channels across 4 stereo pairs), which is well within the ESP32-S3 I2S clock specification. Each slave outputs its stereo pair on its own dedicated SD line in standard I2S slave mode — no firmware changes needed on the slave side. This is a hardware-supported configuration, not a software workaround.

**Power budget:** Add ~80mA to DVDD budget. New total: ~430mA typical, ~580mA peak. The AP2112K-3.3 (600mA max) is tight at peak. If margin is insufficient, consider the AP2114H-3.3 (1A, same family, SOT-223) or return to a low-dropout alternative with higher current rating.

**BOM:** Add 1x ESP32-S3 DevKit N16R8, 1x slave board PCB, 2x 1x8 machined pin female headers.

# R06 — Specification Cleanup

## Op-Amp Consolidation

The v2.0 spec contains contradictions about the OPA2134 package (single vs dual), whether spare sections exist for direct output buffers, and how many ICs are needed. Sections 4.2, 4.3, and 10.1 disagree with each other.

Resolution: all op-amps on the AFE board are NE5532 dual (DIP-8 or SOIC-8). The OPA2134 and OPA4134 references in the AFE section are removed. The OPA4134 remains on the DAC + Router board for the dry path summing amplifier only.

| **Stage**               | **Qty (dual ICs)** | **Notes**                                                   |
|-------------------------|--------------------|-------------------------------------------------------------|
| Input buffers           | 4x NE5532          | 8 sections, one per channel                                 |
| Direct output buffers   | 4x NE5532          | 8 sections, one per channel                                 |
| Variable gain preamp    | 4x NE5532          | 8 sections, non-inverting, 0–20dB                           |
| Anti-alias filter (new) | 4x NE5532          | 8 sections, Sallen-Key 2nd-order (R02)                      |
| Virtual ground buffer   | 1x NE5532          | 1 section used, 1 spare (tie unused input to VG, output NC) |
| **TOTAL (AFE board)**   | **17x NE5532**     | 34 sections total; 33 used, 1 spare                         |

## BOM Corrections

Digital LDO quantity corrected from 2 to 1 (the v2.0 BOM listed 2x AMS1117-3.3 with no justification for the second unit). DB25 connector removed. PCM5102A removed. HT8988A added. Slave board quantity increased from 3 to 4. ESP32-S3 DevKit quantity increased from 4 to 5.

## Gain Formula Note

Section 4.4 states gain range “0dB to +20dB” but the formula (1 + Rf/Rg with Rg=1kΩ, Rf=0–10kΩ trimpot) gives 1x to 11x, which is 0dB to +20.8dB. Corrected in v2.1 to read “0dB to +21dB” for accuracy.

## PCM5102A Output Level Note

The v2.0 spec stated 2.1Vrms output from the PCM5102A while also calling the output “instrument level (-10dBu).” 2.1Vrms is line level, not instrument level. With the HT8988A replacement, the line output is approximately 1Vrms (true line level), and the headphone output is variable via potentiometer. The mismatch is resolved.

# R07 — Firmware: Pitch Detection, Amplitude Tracking, and UART Frame Format

## Pitch Detection Correction

The v2.0 spec references the YIN algorithm for pitch detection. The actual implementation uses bitstream autocorrelation, which is significantly cheaper on the ESP32-S3. Bitstream autocorrelation converts each ADC sample to a single sign bit (1-bit quantisation), then computes autocorrelation using XNOR and popcount operations on packed 32-bit words instead of floating-point multiply-accumulate. This reduces both CPU load and memory footprint, making it well-suited to running all 8 channels on a single core.

All references to “YIN algorithm” in the specification are replaced with “bitstream autocorrelation.”

## Amplitude Tracking

Per-string amplitude tracking is added to the master’s DSP pipeline. The master already receives full 24-bit ADC samples from all 8 strings via I2S. Before converting samples to 1-bit bitstream for the pitch detector, the master computes a peak amplitude value from the full-resolution sample block for each channel.

Peak detection is used rather than RMS: for each block of samples, the master records the maximum absolute sample value per channel. This costs approximately 64 comparisons per channel per block (assuming 64-sample blocks at 48kHz), totalling roughly 512 comparisons for all 8 channels — negligible CPU cost, well under 1% of one core.

The amplitude value provides the slaves with dynamics information they cannot derive from the pitch/gate data alone. This enables envelope following, dynamics-responsive filter modulation, amplitude-modulated effects, auto-wah, velocity-sensitive synthesis, and compressor/gate behaviour on each voice — all without any hardware changes.

## Master DSP Pipeline (per block, all 8 channels)

The master’s Core 0 processes each incoming ADC sample block in the following order:

| **Step** | **Operation**                            | **Cost (approx.)** | **Notes**                                       |
|----------|------------------------------------------|--------------------|-------------------------------------------------|
| 1        | DMA delivers 24-bit samples from ES8388s | Zero (hardware)    | I2S peripheral + DMA, no CPU involvement        |
| 2        | Peak amplitude detection (8 channels)    | \<1% of one core   | Max absolute value per channel per block        |
| 3        | Convert to 1-bit bitstream               | ~1–2%              | Sign bit extraction, pack into 32-bit words     |
| 4        | Bitstream autocorrelation (8 channels)   | ~15–25%            | XNOR + popcount over lag range per channel      |
| 5        | Peak picking and pitch estimation        | ~2–5%              | Find autocorrelation peak, convert to frequency |
| 6        | Pack UART frame, broadcast to slaves     | \<1%               | Core 1 handles UART TX (see frame format below) |

Total estimated CPU load on Core 0: approximately 20–35% at 48kHz with 64-sample blocks. This leaves substantial headroom for future additions such as onset detection, spectral analysis, or polyphonic pitch refinement.

## UART Frame Format (v2.1)

The pitch data UART frame is extended to include a 16-bit amplitude field per string. The frame is broadcast from the master (GPIO17, UART1 TX) to all slaves in parallel at 200Hz update rate.

| **Field** | **Size** | **Description**                                                            |
|-----------|----------|----------------------------------------------------------------------------|
| SYNC      | 1 byte   | 0xAA — frame start marker                                                  |
| STRING_ID | 1 byte   | 0x00–0x07 (string 1–8)                                                     |
| PITCH     | 2 bytes  | Unsigned 16-bit pitch in units of 0.01 Hz (e.g. 44000 = 440.00 Hz)         |
| GATE      | 1 byte   | 0x00 = string silent, 0x01 = string active, 0x02 = new onset               |
| AMPLITUDE | 2 bytes  | Unsigned 16-bit peak amplitude (0x0000 = silence, 0xFFFF = ADC full scale) |
| CHECKSUM  | 1 byte   | XOR of all preceding bytes (STRING_ID through AMPLITUDE)                   |
| END       | 1 byte   | 0x55 — frame end marker                                                    |

Total frame size: 9 bytes per string. At 200Hz update rate with 8 strings, this is 14,400 bytes/sec = 115.2 kbaud, well within the UART capacity. A single broadcast frame containing all 8 strings (72 bytes) can alternatively be sent as one packet with a single sync/end wrapper to reduce overhead — this is a firmware implementation choice.

## Gate States

The GATE field distinguishes three states to support ADSR envelope triggering on the slaves:

**0x00 (OFF):** String is silent or below noise floor. Slaves should enter release phase of any active envelope.

**0x01 (SUSTAIN):** String is sounding and pitch is stable. Slaves maintain current envelope phase (sustain).

**0x02 (ONSET):** New note onset detected (rising amplitude crossing threshold, or pitch change exceeding semitone threshold). Slaves trigger attack phase of ADSR envelope. This state is sent for one frame only, then reverts to 0x01.

Onset detection is performed on the master using a combination of amplitude threshold crossing and pitch stability. The exact onset detection parameters (threshold, hold-off time, pitch stability window) are configurable in firmware and do not affect the frame format.

# Remaining Open Items

| **\#** | **Item**                                                                                                                                                                                                                                                            | **Status**          |
|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|
| 1      | Confirm HT8988A JLCPCB/LCSC part number and assembly availability before finalising DAC board BOM.                                                                                                                                                                  | **OPEN**            |
| 2      | Confirm HT8988A I2C address configuration does not conflict with ES8388 addresses (0x10, 0x11).                                                                                                                                                                     | **OPEN**            |
| 3      | I2S return from 4 slaves: resolved. ESP32-S3 I2S TDM mode supports 4 SD input lines on a single peripheral. Peripheral 0 = ADC input (2 lines), Peripheral 1 = slave returns (4 lines) + DAC output (1 line). Confirm TDM slot mapping in firmware during bring-up. | **RESOLVED**        |
| 4      | Review AP2112K 600mA limit against 5-ESP32 power budget (~580mA peak). Consider AP2114H-3.3 (1A) if margin is insufficient.                                                                                                                                         | **OPEN**            |
| 5      | Review AFE board dimensions with 17x NE5532 + passives. May exceed 100x100mm JLCPCB pricing tier.                                                                                                                                                                   | **OPEN**            |
| 6      | Add RC click suppression on analog routing matrix output (per v2.0 open items decision).                                                                                                                                                                            | **DECIDED — DO IT** |
| 7      | Footswitch pinouts confirmed: one footswitch per output mode, user wires as appropriate.                                                                                                                                                                            | **DECIDED**         |

*End of Revision Brief — Version 2.0 → 2.1*
