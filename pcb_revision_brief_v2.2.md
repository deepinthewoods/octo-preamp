**PCB REVISION BRIEF**

8-Channel Per-String Guitar Pickup System

Specification Version 2.1 → 2.2

Date: 17 March 2026

Status: For Review

Prerequisite: All changes from v2.0 → 2.1 revision brief are incorporated

# Revision Summary

This document covers a single architectural change: replacing the UART control link between master and slaves with a unified bidirectional I2S TDM bus, enabling a dual-mode system (synth mode and effects mode) with no hardware changes between modes.

| **REV \#** | **Scope**           | **Summary**                                                                                 |
|------------|---------------------|---------------------------------------------------------------------------------------------|
| **R08**    | System Architecture | Unified bidirectional I2S TDM bus replaces UART for master↔slave data                       |
| **R09**    | Master Board        | UART pins (GPIO17/18) freed; I2S forward data path added to slave headers                   |
| **R10**    | Slave Boards        | Add I2S DIN pin assignment for receiving audio/control from master                          |
| **R11**    | Firmware Spec       | Dual-mode operation: synth mode and effects mode; TDM slot allocation; control data packing |
| **R12**    | UART Retention      | UART retained for OTA and debug only; no longer carries real-time audio control data        |

NOTE: we only have 2 boards now, main and preamp

# R08 — Unified Bidirectional I2S TDM Bus

## Motivation

The v2.1 architecture uses two separate communication paths between master and slaves: I2S (slave→master, audio return) and UART (master→slave, pitch/gate/amplitude control data). This works but limits the system to synth-only operation — there is no way to send actual audio from the master to the slaves for effects processing.

By replacing UART with I2S for the master→slave direction, both audio and control data can travel on a single unified bus. The system gains a second operating mode (per-string effects processing) with no additional hardware beyond reassigning two GPIO pins.

## Architecture

All master↔slave communication now runs on a single I2S TDM bus using the ESP32-S3’s I2S Peripheral 1:

| **Signal** | **Direction**       | **Master GPIO** | **Notes**                           |
|------------|---------------------|-----------------|-------------------------------------|
| BCLK       | Master → All slaves | GPIO8           | Shared bit clock (unchanged)        |
| LRCK       | Master → All slaves | GPIO9           | Shared word select (unchanged)      |
| SD_RET1    | Slave 1 → Master    | GPIO10 (in)     | Return audio, strings 1+2           |
| SD_RET2    | Slave 2 → Master    | GPIO11 (in)     | Return audio, strings 3+4           |
| SD_RET3    | Slave 3 → Master    | GPIO12 (in)     | Return audio, strings 5+6           |
| SD_RET4    | Slave 4 → Master    | GPIO14 (in)     | Return audio, strings 7+8           |
| SD_FWD_AB  | Master → Slaves 1+2 | GPIO17 (out)    | Forward audio/control, strings 1–4  |
| SD_FWD_CD  | Master → Slaves 3+4 | GPIO18 (out)    | Forward audio/control, strings 5–8  |
| SD_DAC     | Master → HT8988A    | GPIO13 (out)    | Final stereo mix to DAC (unchanged) |

## TDM Configuration

The bus runs at 48kHz sample rate with 8 TDM slots of 16 bits each, giving a BCLK of 48000 × 16 × 8 = 6.144 MHz. Each slot carries one mono channel. The 8 slots map to the 8 strings.

### 16-Bit Slot Width Decision

The ESP32-S3 I2S TDM hardware imposes a hard limit on the number of simultaneous slots per peripheral based on slot width: 4 slots at 32-bit, 8 slots at 16-bit, or 16 slots at 8-bit. Since the system requires 8 channels (one per string), 16-bit slot width is the minimum that fits all 8 channels on a single peripheral. This is a hardware constraint documented in the ESP-IDF technical reference.

Impact: the ES8388 ADCs capture at 24-bit internally, but the I2S bus truncates to 16 bits (discarding the least significant byte). This gives 96dB of dynamic range, which is more than adequate for guitar pickup signals (typical pickup SNR is 60–80dB). For pitch detection, the data is further reduced to 1-bit (sign only), so the truncation has zero effect on pitch accuracy. For amplitude tracking, 16 bits provides far more resolution than the 8-bit value sent to slaves. For effects mode audio processing, 16-bit is CD quality and matches or exceeds the fidelity of most guitar effects hardware.

This is a software-only configuration change. No hardware modifications are needed — the physical I2S bus, wiring, and all connected ICs are agnostic to the slot bit width. The BCLK frequency is set by the master ESP32’s clock divider registers; the ES8388s, HT8988A, and slave ESP32s all follow whatever clock is provided.

| **TDM Slot** | **String** | **Forward Data Line** | **Return Data Line** | **Slave**       |
|--------------|------------|-----------------------|----------------------|-----------------|
| 0            | String 1   | SD_FWD_AB             | SD_RET1              | Slave 1, Core 0 |
| 1            | String 2   | SD_FWD_AB             | SD_RET1              | Slave 1, Core 1 |
| 2            | String 3   | SD_FWD_AB             | SD_RET2              | Slave 2, Core 0 |
| 3            | String 4   | SD_FWD_AB             | SD_RET2              | Slave 2, Core 1 |
| 4            | String 5   | SD_FWD_CD             | SD_RET3              | Slave 3, Core 0 |
| 5            | String 6   | SD_FWD_CD             | SD_RET3              | Slave 3, Core 1 |
| 6            | String 7   | SD_FWD_CD             | SD_RET4              | Slave 4, Core 0 |
| 7            | String 8   | SD_FWD_CD             | SD_RET4              | Slave 4, Core 1 |

Each forward data line carries 4 TDM slots (4 mono channels). Each slave listens to 2 of those slots (its assigned string pair) and ignores the rest. The return data lines each carry 2 TDM slots (one stereo pair per slave), as in v2.1.

## Forward Data Line Routing

Two forward data lines are needed because the ESP32-S3 I2S TDM peripheral supports up to 4 SD lines, but each slave only has one I2S DIN pin. Slaves 1 and 2 share SD_FWD_AB (each reading different TDM slots); slaves 3 and 4 share SD_FWD_CD. The physical wiring is:

**GPIO17 (SD_FWD_AB):** Wired to slave 1 I2S DIN and slave 2 I2S DIN in parallel. Slave 1 reads slots 0+1; slave 2 reads slots 2+3.

**GPIO18 (SD_FWD_CD):** Wired to slave 3 I2S DIN and slave 4 I2S DIN in parallel. Slave 3 reads slots 4+5; slave 4 reads slots 6+7.

This works because TDM is a time-slotted protocol — all data is present on the line, and each slave simply DMA-reads only its assigned slot positions. No bus contention occurs.

# R09 — Master Board GPIO Changes

## Pin Reassignment

| **GPIO** | **v2.1 Function**     | **v2.2 Function**   | **Notes**                  |
|----------|-----------------------|---------------------|----------------------------|
| 17       | UART1 TX (pitch data) | I2S SD_FWD_AB (out) | Forward data to slaves 1+2 |
| 18       | UART1 RX (slave ack)  | I2S SD_FWD_CD (out) | Forward data to slaves 3+4 |

All other master GPIO assignments are unchanged from v2.1.

## Freed Pins

UART1 TX/RX are no longer needed for real-time control data. However, UART is retained for OTA firmware updates and debug (see R12). Since OTA is an infrequent operation, the master firmware can dynamically reconfigure GPIO17/18 between I2S (normal operation) and UART (OTA mode) at runtime using the ESP32-S3’s GPIO matrix. No hardware change is needed to support both functions — pin muxing is purely a firmware register write.

## PCB Routing

GPIO17 and GPIO18 are already routed from the master board to the slave headers (they were UART lines to slave GPIO40/41). The physical traces remain the same; only the signal assignment changes. Ensure these traces are routed with I2S signal integrity in mind: keep them short, matched length where possible, and avoid running them adjacent to noisy digital lines. At 6.144 MHz BCLK this is not critical, but good practice.

# R10 — Slave Board GPIO Changes

## Pin Reassignment

| **GPIO** | **v2.1 Function**       | **v2.2 Function**          | **Notes**                 |
|----------|-------------------------|----------------------------|---------------------------|
| 40       | UART RX (pitch data in) | I2S DIN (audio/control in) | Forward data from master  |
| 41       | UART TX (OTA ack)       | UART TX (OTA/debug only)   | Retained for OTA; see R12 |

All other slave GPIO assignments are unchanged from v2.1. The slave I2S peripheral configuration changes from 1-pin output (DOUT on GPIO7) to 2-pin bidirectional: DOUT on GPIO7 (return, unchanged) and DIN on GPIO40 (forward, new).

## Slave Header Update

The slave board top-right header pin 8 (GPIO40) changes designation from “UART RX — Pitch data + OTA firmware” to “I2S DIN — Forward audio/control from master.” The physical connection is unchanged. The header pinout table for the slave boards is updated accordingly:

| **Pin** | **DevKit Pin** | **Signal** | **Direction**  | **Notes**                            |
|---------|----------------|------------|----------------|--------------------------------------|
| 1       | GND            | Ground     | —              | DGND                                 |
| 2       | GPIO43         | (U0TXD)    | —              | Leave unconnected, debug only        |
| 3       | GPIO44         | (U0RXD)    | —              | Leave unconnected, debug only        |
| 4       | GPIO1          | SPARE      | —              | Reserved                             |
| 5       | GPIO2          | SPARE      | —              | Reserved                             |
| 6       | GPIO42         | SPARE      | —              | Reserved                             |
| 7       | GPIO41         | UART TX    | Out to master  | OTA acknowledge / debug only         |
| 8       | GPIO40         | I2S DIN    | In from master | Forward audio or packed control data |

# R11 — Dual-Mode Firmware Architecture

## Overview

The system supports two operating modes, selectable at runtime via footswitch, GPIO, or I2C command. Both modes use identical hardware and the same I2S TDM bus. The difference is purely in what the master puts into the forward TDM slots and how the slaves interpret the data they receive.

## Mode A: Synth Mode

This is the default mode from v2.1. The master runs pitch detection (bitstream autocorrelation) and amplitude tracking on all 8 ADC channels. Instead of broadcasting the results over UART, the master sends control data via the forward I2S TDM slots using interleaved frames.

### Interleaved Control Frames

Each TDM slot is 16 bits wide at 48kHz. Rather than cramming all control data into a single 16-bit word, the master alternates between two frame types on consecutive I2S frames:

| **Frame** | **Bits** | **Content**                                                                                                               |
|-----------|----------|---------------------------------------------------------------------------------------------------------------------------|
| Even (N)  | \[15:0\] | Pitch — unsigned 16-bit, units of 0.01 Hz (e.g. 44000 = 440.00 Hz). Full guitar range 20–1400 Hz with 0.01 Hz resolution. |
| Odd (N+1) | \[15:2\] | Amplitude — unsigned 14-bit peak amplitude (0x0000 = silence, 0x3FFF = ADC full scale). 84dB dynamic range.               |
|           | \[1:0\]  | Gate — 0b00 = OFF, 0b01 = SUSTAIN, 0b10 = ONSET, 0b11 = reserved                                                          |

The slave latches each frame type into its respective register and combines them into a complete control state. A new complete pitch + amplitude + gate tuple arrives every 2 frames = 41.7 µs (24 kHz effective update rate). This is orders of magnitude faster than the pitch detector produces new data — bitstream autocorrelation output rates range from ~40 Hz (lowest 8-string fundamental) to ~750 Hz (highest harmonics), so the control bus has roughly 30–600x more bandwidth than needed.

Frame discrimination: the slave distinguishes even/odd frames by a simple toggle counter synchronised to the LRCK edge, or the master can set bit \[15\] as a frame-type flag (0 = pitch, 1 = amplitude/gate), reducing pitch to 15 bits (0.02 Hz resolution, still more than adequate) and amplitude to 13 bits (78dB range).

Between pitch detector updates, the master repeats the last known values. The slave sees a steady stream of identical control words until the pitch or amplitude genuinely changes. No interpolation or smoothing is required at the transport layer, though the slave’s oscillator may apply portamento filtering on the pitch value.

## Mode B: Effects Mode

In effects mode, the master does not run pitch detection. Instead, it routes the 16-bit ADC audio for each string directly into the corresponding forward TDM slot. Each slot now carries a true 16-bit audio sample rather than a packed control word.

The slave receives its 2 assigned audio channels via I2S DIN, processes them through its per-core effects chain, and sends the processed audio back to the master via I2S DOUT. The master then mixes the return streams and sends the result to the HT8988A DAC.

## Effects Mode DSP Budget (per slave)

| **Resource**                 | **Value**     | **Notes**                                        |
|------------------------------|---------------|--------------------------------------------------|
| Clock per sample per channel | 5,000 cycles  | 240 MHz / 48 kHz = 5,000; one core per channel   |
| Biquad cost                  | ~10–15 cycles | 5 MACs + overhead per biquad section             |
| Max biquads per channel      | ~300+         | Theoretical; practical limit set by cache/memory |
| Typical effects chain        | ~5–10% CPU    | 10-band parametric EQ + HP/LP + compressor       |
| PSRAM available              | 8 MB          | Delay lines, reverb buffers, IR storage          |

Each slave has approximately 5,000 cycles per sample per channel with one core per string. This is enough for a complete per-string effects chain: parametric EQ, dynamics processing, modulation effects, and short delay/reverb using PSRAM for buffer storage. Both cores are available since each slave processes exactly 2 channels.

## Mode Discrimination

The slave needs to know which mode it is in so it can interpret the forward TDM data correctly. Two options:

**Option A — Magic value:** In synth mode, the control word always has specific bit patterns in the reserved/gate fields that cannot occur in valid 24-bit audio (e.g. the bottom 2 bits encode gate state, which is never 0b11 in synth mode). The slave auto-detects the mode from the data pattern.

**Option B — Explicit signal:** The master sends a mode-switch command via UART before reconfiguring the TDM content. Since UART is retained for OTA (R12), it can also carry infrequent control commands. The slave receives the mode command, switches its processing pipeline, and acknowledges.

Recommendation: Option B. It is unambiguous, costs nothing (UART is already available), and the mode switch is an infrequent event (user presses footswitch). The UART carries a single-byte command, not a continuous stream.

# R12 — UART Retention for OTA and Debug

## Change

UART is no longer used for real-time control data (pitch/gate/amplitude). It is retained exclusively for:

**OTA firmware updates:** The master pauses I2S, reconfigures GPIO17 as UART1 TX, sends firmware binary to the target slave over UART, then reconfigures back to I2S. This is an infrequent operation (firmware update only) and takes approximately 5 seconds.

**Debug logging:** During development, slaves can send debug output over GPIO41 (UART TX). This does not conflict with I2S since GPIO41 is not part of the I2S bus.

**Mode switching commands:** A single-byte command from master to slaves to switch between synth mode and effects mode. The master briefly reconfigures GPIO17 to UART, sends the command, waits for acknowledgement on GPIO18 (also briefly reconfigured to UART RX), then restores both to I2S. Total interruption: \<1ms.

## Pin Muxing Strategy

The ESP32-S3 GPIO matrix allows any peripheral signal to be routed to any GPIO at runtime. The master firmware maintains two configurations:

| **GPIO** | **Normal (I2S) Mode**              | **OTA / Command Mode** |
|----------|------------------------------------|------------------------|
| 17       | I2S Peripheral 1, SD_FWD_AB output | UART1 TX               |
| 18       | I2S Peripheral 1, SD_FWD_CD output | UART1 RX               |

Switching between configurations takes a few microseconds (GPIO matrix register writes). Audio output is muted during OTA via the MUX_INH pin on the CD4052B routing matrix to prevent clicks.

# Updated System Signal Flow

## Synth Mode

Pickups → AFE → ES8388 ADC → I2S to master → Master runs pitch detection + amplitude tracking → Packs control data into forward TDM slots → I2S to slaves → Slaves generate synth audio → I2S return to master → Master mixes → HT8988A DAC → Outputs

## Effects Mode

Pickups → AFE → ES8388 ADC → I2S to master → Master routes raw audio into forward TDM slots (no pitch detection) → I2S to slaves → Slaves process audio (EQ, dynamics, effects) → I2S return to master → Master mixes → HT8988A DAC → Outputs

## Hybrid Mode (Future)

A future firmware revision could support hybrid operation where some slaves run in synth mode and others in effects mode simultaneously. For example, slaves 1–2 generate synth voices for strings 1–4 while slaves 3–4 apply effects to the raw audio of strings 5–8. This requires per-slave mode commands (extend the mode-switch UART command with a slave ID field) but no hardware changes.

# Open Items

| **\#** | **Item**                                                                                                                                                                                                                 | **Status**   |
|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| 1      | Confirm HT8988A JLCPCB/LCSC part number and assembly availability before finalising DAC board BOM.                                                                                                                       | **OPEN**     |
| 2      | Confirm HT8988A I2C address configuration does not conflict with ES8388 addresses (0x10, 0x11).                                                                                                                          | **OPEN**     |
| 3      | I2S TDM slot width: resolved. 16-bit slot width selected, giving 8 slots per peripheral. This is a hardware limitation of the ESP32-S3 (max 4 slots at 32-bit). No hardware changes needed; software configuration only. | **RESOLVED** |
| 4      | I2S full-duplex TDM on slave: confirmed supported by ESP-IDF. TX (DOUT) and RX (DIN) share BCLK/LRCK on a single peripheral in full-duplex mode.                                                                         | **RESOLVED** |
| 5      | Synth mode control word packing: resolved. Interleaved frames give full 16-bit pitch and 14-bit amplitude + 2-bit gate on alternating frames at 24kHz effective update rate. No compromises needed.                      | **RESOLVED** |
| 6      | Review AP2112K 600mA limit against 5-ESP32 power budget (~580mA peak). Consider AP2114H-3.3 (1A) if margin is insufficient.                                                                                              | **OPEN**     |
| 7      | Review AFE board dimensions with 17x NE5532 + passives. May exceed 100x100mm JLCPCB pricing tier.                                                                                                                        | **OPEN**     |
| 8      | Determine latency impact of pin-muxing GPIO17/18 between I2S and UART for mode switching / OTA. Muted via MUX_INH during switch.                                                                                         | **LOW RISK** |

*End of Revision Brief — Version 2.1 → 2.2*
