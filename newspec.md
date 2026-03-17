8-Channel Per-String Guitar Pickup System
Full System Specification — Version 2.0
Analog Front End · ADC · Multi-ESP32 DSP · Synthesis · Analog Routing

1. Project Overview
This document specifies a complete electronic system for an 8-string (or multi-string) guitar with independent per-string pickup processing. Each string's signal is captured, buffered, and made available simultaneously on three paths:

A dedicated buffered direct output per string (unity gain, uncoloured)
An 8-channel ADC path feeding the digital DSP system (pitch detection, oscillator synthesis, filtering)
An analog summing and EQ path for traditional amplifier use with Wal-style active tone shaping

The system is designed around two ES8388 codec ICs for ADC, four ESP32-S3 microcontrollers for DSP, and a PCM5102A for the final stereo DAC output. Power is supplied by a single-cell LiPo battery charged via USB-C, providing a clean, noise-free supply independent of USB switching noise.

2. System Signal Flow
8x String Pickups
    |
    v
8x Input Buffer (unity gain, 1MOhm input impedance)
    |
    +---> 8x Buffered Direct Output (per-string thru jack or header)
    |
    v
8x Variable Gain Preamp (0-20dB trimpot)
    |
    v
8x Anti-Aliasing Filter (22kHz single-pole RC)
    |
    v
2x ES8388 ADC (4 channels each, I2S TDM to master ESP32)
    |
    v
ESP32 #1 MASTER
    - Pitch detection all 8 strings (YIN algorithm, Core 0)
    - UART broadcast to slaves (Core 1)
    - I2S return mix from slaves
    - Final mix to PCM5102A DAC
    |
    +---> UART pitch data ---> ESP32 #2 (strings 1+2, Core 0+1)
    +---> UART pitch data ---> ESP32 #3 (strings 3+4, Core 0+1)
    +---> UART pitch data ---> ESP32 #4 (strings 5+6, Core 0+1)
    |           |                   |                   |
    |      I2S return          I2S return          I2S return
    |           |                   |                   |
    +-----------+-------------------+-----------+
                                                |
                                                v
                                        Software mix (master)
                                                |
                                                v
                                        PCM5102A DAC (stereo out)
                                                |
                                                v
                                    Analog Routing Matrix
                                    (CD4052B x2, GPIO controlled)
                                                |
                          +--------------------+--------------------+
                          |                    |                    |
                     Dry output           Mix output          Wet/dry split
                     (summed analog)      (synth + dry)       (L=dry, R=synth)

3. Power Supply
3.1 Architecture
The system runs entirely from a single-cell LiPo battery (3.7V nominal). USB-C is used for charging only. There is no 5V rail. Slave ESP32 DevKits are powered directly from the 3.3V DVDD rail, bypassing their onboard AMS1117 LDOs.
USB-C VBUS (5V)
    |
    v
MCP73831T-2ACI/OT (SOT-23-5)
    |
    v
LiPo Cell (single cell, 3.7V nominal, 4.2V full, 3.0V cutoff)
    |
    +---> LP2985-33DBVR --> 3.3V AVDD   (analog rail, ultra-low noise)
    +---> AMS1117-3.3   --> 3.3V DVDD   (digital rail)
3.2 MCP73831 Charger

Package: SOT-23-5
RPROG = 4.7kOhm -> ~210mA charge current (suitable for 1000-2000mAh cell)
STAT pin -> master ESP32 free GPIO for charge status LED
Add reverse protection Schottky diode on VBAT line (BAT54 or SS14)
Decouple VBAT with 100uF electrolytic + 100nF ceramic at charger output

3.3 Analog Rail — LP2985-33DBVR (AVDD)

Package: SOT-23-5
Output: 3.3V AVDD
Noise: ~30uV RMS (critical for ADC SNR — do not substitute with AMS1117 on this rail)
Feeds: ES8388 AVDD pins, all AFE op-amps, virtual ground reference
Decoupling: 1uF ceramic (required for LP2985 stability) + 10uF electrolytic at output
Copper pour: AGND, separate from DGND

3.4 Digital Rail — AMS1117-3.3 (DVDD)

Package: SOT-223
Output: 3.3V DVDD
Feeds: all four ESP32-S3 DevKits (via 3V3 header pins), ES8388 DVDD pins, PCM5102A
Decoupling: 100uF electrolytic + 100nF ceramic at output
Current budget: 4x ESP32-S3 at ~80mA typical (WiFi disabled on slaves) = ~320mA
plus ES8388 x2 ~10mA, PCM5102A ~15mA. Total ~350mA typical, 500mA peak.
AMS1117 rated 1A — adequate with heatsink pad connected to ground plane
Copper pour: DGND, separate from AGND

3.5 Ground Plane Rules (CRITICAL)
AGND and DGND are separate copper pours on all boards. They connect at exactly ONE
star point, located near the power entry connector on the master board. A ferrite bead
(BLM21PG221SN1 or equivalent) bridges them at this single point.

No digital traces cross the AGND pour
No analog traces cross the DGND pour
ES8388 AGND and DGND pins connect to their respective pours
All op-amp ground pins connect to AGND only

3.6 LiPo Cell Recommendation

Recommended: 103450 LiPo, ~2000mAh, 10x34x50mm
Connector: JST-PH 2.0mm 2-pin, hand soldered after JLCPCB delivery
Runtime estimate: ~350mA draw -> ~5-6 hours per charge
Cell protection: MCP73831 includes overcharge protection. Add undercharge cutoff
via ESP32 ADC monitoring (voltage divider on VBAT -> master ADC pin)


4. Analog Front End (AFE Board)
The AFE board handles all 8 pickup inputs. Each channel is identical. The board runs
entirely on 3.3V AVDD with a virtual ground at 1.65V.
4.1 Virtual Ground Generation

Two 10kOhm resistors from AVDD to AGND form 1.65V mid-rail reference
Buffered by one section of TL072 in unity gain configuration
Decouple virtual ground node with 100uF + 100nF to AGND
This virtual ground is the AC reference for all audio coupling on the AFE board

4.2 Input Buffer Stage (per channel, x8)
Provides high input impedance to avoid loading the pickup, and unity-gain buffering
for both the direct output path and the preamp path.

Op-amp: OPA2134 (preferred) or TL072 (budget). One dual op-amp per 2 channels = 4 ICs
Configuration: non-inverting unity gain (output tied directly to inverting input)
Input coupling: 10nF film capacitor in series from pickup input
Input impedance: 1MOhm resistor from op-amp non-inverting input to virtual ground (1.65V)
Supply: 3.3V AVDD single supply, mid-rail biased at 1.65V virtual ground
Output impedance: ~50 Ohm (op-amp output)
Output swing: +/- 1.65V (limited by single supply headroom — adequate for guitar levels)

4.3 Buffered Direct Output (per channel, x8) — NEW
Each channel provides a dedicated buffered direct output tapped immediately after the
input buffer, before the variable gain preamp. This output is unity gain, uncoloured,
and represents the raw pickup signal at low impedance.

Tap point: output of input buffer op-amp (after 10nF coupling cap, before preamp)
Second buffer: one additional op-amp section per channel in unity gain
(use remaining sections of the OPA2134 dual ICs — 4 ICs x 2 sections = 8 sections
available, 4 used for input buffers, 4 available for direct output buffers)
NOTE: This exactly uses all 8 sections of the 4 dual op-amp ICs. No additional ICs needed.
Output coupling: 10uF electrolytic to remove DC offset (1.65V virtual ground offset)
Output impedance: ~600 Ohm series resistor for cable driving and short-circuit protection
Output connector: 8x 3.5mm mono jack or multi-pin header depending on mechanical design
Level: approximately the same as the pickup output (~100mV-1V peak depending on playing)
This output is suitable for feeding into another preamp, audio interface, or effects unit

4.4 Variable Gain Preamp Stage (per channel, x8)

Op-amp: NE5532 or OPA2134 (dual, 4 ICs for 8 channels)
Configuration: non-inverting amplifier
Gain range: 0dB to +20dB (1x to 11x)
Formula: Gain = 1 + Rf/Rg. Rg = 1kOhm fixed, Rf = 0-10kOhm trimpot
DC bias: 1.65V virtual ground on non-inverting input via 10kOhm resistor
Output coupling: 10uF electrolytic before anti-aliasing filter

4.5 Anti-Aliasing Filter (per channel, x8)

Topology: single-pole passive RC low-pass
Cutoff: ~22kHz (R = 22kOhm, C = 330pF)
Purpose: attenuate frequencies above Nyquist at 48kHz sample rate
Placed between preamp output and ES8388 ADC input


5. ADC Board (2x ES8388)
5.1 ES8388 Overview
Two ES8388 ICs provide 8 ADC channels total (4 channels per IC). Both share the same
I2S clock bus and I2C control bus, with separate data output lines to the master ESP32.

ADC resolution: 24-bit
ADC SNR: 93 dBFS typical
Sample rate: 48kHz
Supply: 3.3V AVDD (analog) + 3.3V DVDD (digital)
Control: I2C
Audio output: I2S

5.2 I2C Address Configuration

ES8388 #1 (channels 1-4, strings 1-4): ADDR pin tied to AGND -> address 0x10
ES8388 #2 (channels 5-8, strings 5-8): ADDR pin tied to AVDD via 10kOhm -> address 0x11
Shared I2C bus: SDA and SCL with 4.7kOhm pull-ups to AVDD

5.3 JLCPCB Part

ES8388: JLCPCB part number C365736, in stock ~$0.53-$1.05 per unit
Extended component: $1.50 setup fee (one-time per unique part, not per placement)
Do NOT substitute HT8988A — it is stereo only (2 ADC channels) and cannot replace ES8388

5.4 ES8388 Startup Configuration (I2C, performed by master ESP32)

Set ADC sample rate to 48kHz
Set MCLK divider for 256x Fs ratio (MCLK = 12.288MHz)
Enable all 4 ADC input channels on each IC
Set ADC PGA gain: start at 0dB, adjustable per channel in firmware
Set I2S format: standard I2S, 24-bit word length
Power up ADC sections, power down DAC sections (DAC unused on ES8388)


6. Master ESP32-S3 (ESP32 #1)
Board: ESP32-S3 DevKit N16R8 (16MB flash, 8MB PSRAM)
6.1 Responsibilities

Generate I2S master clock (MCLK, BCLK, LRCK) for both ES8388 ICs
Receive 8-channel ADC data from both ES8388s over I2S
Run per-string pitch detection (YIN algorithm) on Core 0
Broadcast pitch/note data to all three slave ESP32s over UART on Core 1
Receive I2S audio return streams from all three slaves
Software mix all audio streams into final stereo output
Drive PCM5102A output DAC via I2S
Control analog routing matrix (CD4052B) via 3 GPIOs
Monitor LiPo battery voltage via ADC pin
Handle footswitch inputs for output mode switching
Optionally initiate OTA firmware updates to slave boards

6.2 Master GPIO Assignments
I2S — ES8388 ADC Input (I2S Master Out)
GPIOSignalDestinationNotesGPIO5MCLKBoth ES8388 MCLK12.288MHz at 48kHz FsGPIO6BCLKBoth ES8388 BCLKBit clockGPIO7LRCKBoth ES8388 LRCKWord selectGPIO15ADCDAT_AES8388 #1 ADCDAT outChannels 1-4GPIO16ADCDAT_BES8388 #2 ADCDAT outChannels 5-8
I2C — ES8388 Control
GPIOSignalDestinationNotesGPIO21SDABoth ES8388 SDA4.7kOhm pull-up to AVDDGPIO38SCLBoth ES8388 SCL4.7kOhm pull-up to AVDD
I2S — Slave Audio Return
GPIOSignalDestinationNotesGPIO8BCLK outAll 3 slave BCLK inputsShared clock broadcastGPIO9LRCK outAll 3 slave LRCK inputsShared word select broadcastGPIO10DIN_ASlave #2 DOUTAudio return strings 1+2GPIO11DIN_BSlave #3 DOUTAudio return strings 3+4GPIO12DIN_CSlave #4 DOUTAudio return strings 5+6GPIO13DOUTPCM5102A DINFinal stereo mix to DAC
UART — Pitch Data and OTA
GPIOSignalDestinationNotesGPIO17UART1 TXAll 3 slave GPIO40Broadcast, wired in parallelGPIO18UART1 RXAll 3 slave GPIO41Wired OR, 10kOhm pull-up
OTA Flash Control
GPIOSignalDestinationNotesGPIO2BOOT #2Slave #2 GPIO0Pull low for bootloaderGPIO1BOOT #3Slave #3 GPIO0Pull low for bootloaderGPIO42BOOT #4Slave #4 GPIO0Pull low for bootloaderGPIO41EN #2Slave #2 RSTPulse low to resetGPIO40EN #3Slave #3 RSTPulse low to resetGPIO39EN #4Slave #4 RSTPulse low to reset
Analog Routing Matrix Control (CD4052B)
GPIOSignalDestinationNotesGPIO45MUX_ABoth CD4052B pin AAddress bit 0GPIO46MUX_BBoth CD4052B pin BAddress bit 1GPIO35MUX_INHBoth CD4052B pin INHInhibit — mute during switch
Output Mode Truth Table (CD4052B)
MUX_AMUX_BMode00Dry only10Synth only01Hybrid11Wet/dry split
Miscellaneous
GPIOSignalNotesGPIO43U0TXDReserved — USB debug serial. Do not connect.GPIO44U0RXDReserved — USB debug serial. Do not connect.GPIO3LOGOutputs boot log. Do not connect to signals.GPIO48RGB LEDOnboard status LED, usable in firmwareGPIO36VBAT_MONVoltage divider from VBAT for battery monitoring

7. Slave ESP32-S3 Boards (ESP32 #2, #3, #4)
Board: ESP32-S3 DevKit N16R8 (same as master, identical hardware)
Firmware: differs from master — oscillator synthesis + filter DSP only
7.1 String Assignment
BoardCore 0Core 1ESP32 #2String 1 osc+filterString 2 osc+filterESP32 #3String 3 osc+filterString 4 osc+filterESP32 #4String 5 osc+filterString 6 osc+filter
Strings 7 and 8 (if applicable beyond 6-string): handled on master spare cycles,
or add a fifth ESP32 slave using the same architecture.
7.2 Slave GPIO Assignments
Top-Left Header (1x8, power + I2S + reset)
PinDevKit PinSignalDirectionNotes13V33.3V powerInFrom DVDD rail23V33.3V powerInSecond pin for current capacity3RSTResetIn from masterMaster can reboot slave4GPIO4SPARE—Reserved5GPIO5I2S BCLKIn from masterBit clock6GPIO6I2S LRCKIn from masterWord select7GPIO7I2S DOUTOut to masterAudio output8GPIO15SPARE—Reserved
Top-Right Header (1x8, ground + UART)
PinDevKit PinSignalDirectionNotes1GNDGround—DGND2GPIO43(U0TXD)—Leave unconnected, debug only3GPIO44(U0RXD)—Leave unconnected, debug only4GPIO1SPARE—Reserved5GPIO2SPARE—Reserved6GPIO42SPARE—Reserved7GPIO41UART TXOut to masterDebug / OTA acknowledge8GPIO40UART RXIn from masterPitch data + OTA firmware
7.3 Slave Internal GPIO Assignments (not on headers)
GPIOSignalNotesGPIO0BOOTConnected to master BOOT control GPIOs aboveGPIO48RGB LEDOnboard status, usable in firmwareGPIO43U0TXDLeave free for USB debug during developmentGPIO44U0RXDLeave free for USB debug during development
7.4 WiFi Policy
WiFi is disabled on all slave boards at firmware level. This eliminates ~200mA transmit
current spikes that would cause DVDD voltage droop and potential audio glitches.
Bluetooth is also disabled. All communication is wired UART only.
7.5 Per-Core DSP Chain
Each core runs the following in a real-time FreeRTOS task at 48kHz:
UART RX (pitch frame, 200Hz update rate)
    |
    v
Oscillator Engine
    - DDS (Direct Digital Synthesis) via 32-bit phase accumulator
    - Waveform: sine / sawtooth / square / triangle / wavetable (selectable)
    - Frequency: set from pitch data, smoothed with portamento filter
    - Amplitude: ADSR envelope triggered by gate signal in pitch frame
    - Sub-oscillator: optional octave-down mix, level configurable
    |
    v
Filter Stage
    - Biquad IIR filter (state-variable topology)
    - Types: low-pass, high-pass, band-pass, notch (selectable)
    - Cutoff: configurable, optional keyboard tracking
    - Resonance Q: 0.5 to 10, configurable
    - Optional cutoff ADSR envelope for synth sweeps
    |
    v
I2S DMA buffer
    - Left channel: string A (Core 0)
    - Right channel: string B (Core 1)
    - Output to master via I2S slave
7.6 OTA Firmware Update Architecture
Slaves ship with a custom OTA bootloader flashed via USB-C before installation.
All subsequent updates are delivered by the master over UART.
Partition table (16MB flash):
nvs          (16kB)   — config, string ID, tuning params
otadata      (8kB)    — tracks active OTA partition
app0/OTA_0   (4MB)    — currently running firmware
app1/OTA_1   (4MB)    — master writes new firmware here
bootloader   (custom) — listens on UART for update trigger
UART protocol on GPIO40 (RX):
Normal pitch frame:   0xAA [frame data] [checksum] 0x55
OTA trigger:          0xBE 0xEF [firmware size 4 bytes]
OTA data:             [raw binary blocks with CRC per block]
OTA complete:         0xDE 0xAD -> slave reboots into new firmware
Master uses esp-serial-flasher library (Espressif, open source) for the update process.
Update takes approximately 5 seconds. Pitch processing pauses during update and resumes
on reboot. No physical access to slave boards is required after initial USB flash.

8. Output DAC — PCM5102A

Resolution: 32-bit
SNR: 112 dBFS
THD+N: -93 dB
Output level: 2.1Vrms single-ended
Interface: I2S, no I2C configuration required
Supply: 3.3V DVDD
Package: TSSOP-20
Receives final stereo mix from master GPIO13 (I2S DOUT)
FMT, XSMT, SCK pins: tie per datasheet for standalone I2S slave operation


9. Analog Routing Matrix
9.1 CD4052B Dual 4:1 Analog Multiplexer
Two CD4052B ICs provide stereo switchable routing between the dry analog signal
(summed from all 8 channels) and the synthesised output from the PCM5102A DAC.
Control lines shared between both ICs:

MUX_A -> master GPIO45
MUX_B -> master GPIO46
MUX_INH -> master GPIO35 (assert high briefly during switching to prevent clicks)

9.2 Output Modes
MUX_AMUX_BModeOutput A (TRS L)Output B (TRS R)00Dry onlyDry summedDry summed10Synth onlySynth LSynth R01HybridDry + Synth LDry + Synth R11Wet/dry splitDry (unprocessed)Synth only
9.3 Analog Summing Amplifier (Dry Path)
Sums all 8 buffered/pre-amped channels to stereo for the dry output path.

Op-amp: OPA4134 (quad) — one IC handles all 8 inputs to stereo
8x 10kOhm input resistors (one per channel)
Feedback resistor: 1.2kOhm (unity-gain sum of 8 inputs)
Optional stereo image: strings 1-4 summed to left with slight pan, 5-8 to right
Output coupling: 100uF electrolytic per output

9.4 Output Stage

Output coupling capacitors: 100uF electrolytic per output
Output impedance: 1kOhm series resistor per output (cable driving + short circuit protection)
Output connectors: 2x 6.35mm TRS jack (main L+R out)
Optional: XLR balanced via Lundahl LL1935 or Jensen JT-DB-EPC output transformer
Level: instrument level (-10dBu) by default, optional op-amp stage for line level (+4dBu)


10. Buffered Direct Outputs (NEW)
Each of the 8 strings has a dedicated buffered direct output providing the raw pickup
signal at low impedance. This is tapped after the input buffer, before the gain stage.
10.1 Circuit

Tap point: output of input buffer stage (after 10nF input coupling cap)
Buffer: second op-amp section of the existing OPA2134 dual ICs (no additional ICs)
The 4x OPA2134 dual ICs provide 8 sections total:

Sections 1-4: input buffers (one per channel pair, one section per channel)

Wait — OPA2134 is a single op-amp, OPA2134 is single channel.
Use OPA2134PA (single) x8 for input buffers, or switch to:
OPA2604AP (dual) x4 for input buffers — leaving 4 spare sections for direct out buffers.
OR use OPA2134 (dual) — confirm package. If dual, 4 ICs = 8 sections, all used.
DESIGNER NOTE: Confirm op-amp package. If using dual op-amps (2 channels per IC),
4 ICs cover 8 input buffers with nothing spare. A separate buffer op-amp stage for
direct outputs will require 4 additional dual op-amp ICs (one section per channel,
4 ICs x 2 sections = 8 sections for 8 channels). Use NE5532 for this stage to keep cost down.
Configuration: unity gain non-inverting
Output coupling: 10uF electrolytic (removes 1.65V DC offset)
Output impedance: 600 Ohm series resistor
Output level: raw pickup level (~100mV-1V peak)

10.2 Output Connector Options
Option A — 8x 3.5mm mono jack (TS): standard, accessible, suits individual pedal/interface use
Option B — DB25 connector (Tascam pinout): standard for 8-channel snake cables to audio interfaces
Option C — 8-pin header (2.54mm): internal connection to another board in the system
Recommend Option B (DB25) for a professional installation, with a breakout cable to
individual jacks. This is the same pinout used by most 8-channel audio interfaces
(Focusrite Scarlett 18i20, MOTU 8pre, etc.).

11. Board Architecture
11.1 Board List
AFE Board
    - 8x input buffer (OPA2134 or NE5532 dual)
    - 8x buffered direct output buffer (NE5532 dual)
    - 8x variable gain preamp (NE5532 or OPA2134)
    - 8x anti-aliasing RC filter
    - Virtual ground generation (1.65V, buffered)
    - Input connectors (pickup inputs)
    - Direct output connector (DB25 or 8x 3.5mm)

ADC Board
    - 2x ES8388 (JLCPCB C365736)
    - I2C pull-ups (4.7kOhm x2 to AVDD)
    - I2S routing to master
    - Local AVDD + AGND decoupling

Master Board
    - ESP32-S3 DevKit N16R8 in 2x 1x8 machined-pin headers (top edge)
    - MCP73831T charger IC
    - LP2985-33DBVR (AVDD LDO)
    - AMS1117-3.3 (DVDD LDO)
    - USB-C connector (charging only)
    - JST-PH 2.0mm LiPo connector
    - VBAT voltage divider -> GPIO36
    - I2S connections to ADC board
    - I2S connections to slave headers
    - UART connections to slave headers
    - OTA control GPIOs to slave headers
    - I2C connections to ADC board
    - I2S connection to DAC/router board

Slave Boards x3 (identical)
    - ESP32-S3 DevKit N16R8 in 2x 1x8 machined-pin headers (top edge)
    - DevKit hangs off top edge of board
    - Top-left header: 3V3(x2), RST, GPIO4, GPIO5, GPIO6, GPIO7, GPIO15
    - Top-right header: GND, GPIO43, GPIO44, GPIO1, GPIO2, GPIO42, GPIO41, GPIO40
    - M2 standoff holes aligned with DevKit mounting holes
    - No components other than headers and standoffs — board is essentially a breakout

DAC + Router Board
    - PCM5102A output DAC
    - 2x CD4052B analog mux
    - OPA4134 summing amplifier (dry path)
    - Output coupling capacitors
    - 2x 6.35mm TRS output jacks
    - Optional XLR via output transformer
    - Footswitch connectors -> GPIO45, GPIO46 on master (via header to master board)
11.2 PCB Layout Rules

4-layer stackup recommended: Signal / GND / PWR / Signal
Separate AGND and DGND pours — star connection via ferrite bead at one point on master board
No digital traces cross AGND pour
No copper pour under ESP32-S3 antenna clearance zone (3mm minimum clearance)
ESP32-S3 USB-C ports must remain physically accessible after assembly (initial flash)
I2S clock lines (BCLK, LRCK, MCLK) routed as short as possible, matched length
ES8388 power pins: 100nF ceramic + 10uF electrolytic as close as possible to each pin
Keep board dimensions under 100x100mm per board for lowest JLCPCB pricing tier
Consider panelising AFE + ADC boards together if they fit within 100x100mm

11.3 JLCPCB Assembly Notes

Assembly type: Economic PCBA where possible
ESP32-S3 DevKits: NOT JLCPCB assembled — hand insert into machined-pin headers after delivery
Mark all ESP32 header footprints DNF (Do Not Fit) in BOM
Extended components (ES8388 C365736, PCM5102A): $1.50 setup fee per unique part type
Through-hole items for hand soldering: 1x8 headers, TRS jacks, JST connector, USB-C
Slave boards contain only headers — may not require PCBA at all, just PCB + hand solder


12. Full Bill of Materials (Key Components)
QtyComponentPartFunction4MicrocontrollerESP32-S3 DevKit N16R81x master, 3x slave2Audio ADC codecES8388 (C365736)4ch ADC each, I2S out1Output DACPCM5102A32-bit stereo DAC1LiPo chargerMCP73831T-2ACI/OTUSB-C to LiPo charging1Analog LDOLP2985-33DBVR3.3V AVDD, ultra-low noise2Digital LDOAMS1117-3.33.3V DVDD2Analog muxCD4052BOutput routing matrix1Quad op-ampOPA4134 or TL074Dry path summing amplifier4Dual op-amp (input buf)OPA2134 (dual) or NE55328x input buffers4Dual op-amp (direct out)NE55328x buffered direct outputs4Dual op-amp (preamp)NE5532 or OPA21348x variable gain preamp8Gain trimpot10kOhm cermetPer-channel gain trim8Input coupling cap10nF filmAC coupling at pickup input8Anti-alias RC22kOhm + 330pF22kHz low-pass per channel8Direct out coupling10uF electrolyticDC blocking on direct outputs8Direct out resistor600 OhmOutput impedance, cable drive1LiPo cell103450, ~2000mAhMain power supply1LiPo connectorJST-PH 2.0mm 2-pinBattery connection1Output connectorDB25 female8x buffered direct outputs2Output jack6.35mm TRSMain stereo output8Machined pin header1x8 female 2.54mm2x per slave board (x3 slaves)2Machined pin header1x8 female 2.54mmMaster board ESP32 socket1Ferrite beadBLM21PG221SN1AGND/DGND bridge1Fuel gauge (optional)MAX17048LiPo state of charge via I2C

13. Open Items



Confirm dual vs single op-amp package choice for input buffer stage. If using
dual op-amps (e.g. NE5532, OPA2134 dual), 4 ICs cover 8 input buffer channels
but leave no spare sections for direct output buffers. A separate set of 4 dual
op-amp ICs is required for the 8 buffered direct output stages. - DECISION: USE NE5532 for all
Confirm DB25 connector pinout for direct outputs (Tascam standard recommended).
Decide on mechanical format for direct outputs — DB25 snake cable vs 8x 3.5mm
individual jacks vs internal header. DECISION: use mono 6.5mm for each.

Confirm PCM5102A JLCPCB part number and stock before finalising DAC board BOM.

Decide number and type of footswitches for output mode switching. - have pinouts for a footswitch for each mode, user will wire as appropriate.
Confirm whether MUX_INH click suppression is sufficient or whether a small
RC on the analog output is also needed during switching transients. DECISION: do the rc


End of specification — Version 2.0
This document supersedes the previous guitar_system_spec.docx (Version 1.0)
PCB revision changes are documented separately in pcb_revision_brief.docx
