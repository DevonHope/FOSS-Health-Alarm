"""WakeBand rigid rev B: parts and netlist (single source for the schematic, the board and the BOM).
Every assembled part has an LCSC number so JLCPCB can build the whole board.
(ref, lib:symbol, value, footprint, LCSC, MPN, {pin: net}, [no-connect pins], description, sheet group)"""
R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0201 = "Capacitor_SMD:C_0201_0603Metric"
L0201 = "Inductor_SMD:L_0201_0603Metric"
L0402 = "Inductor_SMD:L_0402_1005Metric"
TP08 = "wakeband:TestPoint_Pad_D0.8mm"
NC0201 = "wakeband:Nordic_CAPC0603X03L_C"
NC0402 = "wakeband:Nordic_CAPC1005X04L"
NL0201 = "wakeband:Nordic_INDC0603X03L_C"
NR0201 = "wakeband:Nordic_RESC0603X03L_C"
NL1608 = "wakeband:Nordic_INDC1608X06L"


def R(ref, val, lcsc, a, b, desc="", fp=R0402, mpn=""):
    return (ref, "Device:R", val, fp, lcsc, mpn, {"1": a, "2": b}, [], desc)


def C(ref, val, lcsc, a, b="GND", fp=C0402, desc="", mpn=""):
    return (ref, "Device:C", val, fp, lcsc, mpn, {"1": a, "2": b}, [], desc)


def L(ref, val, lcsc, a, b, fp=L0201, desc="", mpn=""):
    return (ref, "Device:L", val, fp, lcsc, mpn, {"1": a, "2": b}, [], desc)


def TP(ref, val, net, fp=TP08, desc=""):
    return (ref, "Connector:TestPoint", val, fp, "", "", {"1": net}, [], desc)


NRF_NC = ["3", "4", "11", "12", "14", "15", "16", "17", "18", "19", "20", "21", "23", "28", "29", "37", "40", "41", "42"]
PARTS = [
    # ---------------- radio: nRF54L15 (Nordic QFN48 reference circuit, config 1) ----------------
    ("U1", "wakeband:nRF54L10-QFAA", "nRF54L10-QFAA", "wakeband:Nordic_QFN40P600X600X90-48N", "C44800139", "Nordic NRF54L10-QFAA-R7",
     {"10": "VDD_2V0", "22": "VDD_2V0", "36": "VDD_2V0", "47": "VDD_2V0", "48": "VDD_2V0",
      "46": "DCC", "45": "DECD", "43": "DECA", "33": "DECA", "34": "XC1", "35": "XC2", "1": "XL1", "2": "XL2",
      "31": "ANT", "32": "GND", "30": "nRESET_IC", "25": "SWDIO", "26": "SWDCLK", "44": "GND", "49": "GND",
      "9": "I2C_SDA", "5": "I2C_SCL", "6": "PMIC_INT", "7": "DOCK_PG", "8": "HAPT_EN", "27": "ACC_INT1", "24": "ACC_INT2",
      "38": "LED_EN", "39": "CHG_CD", "13": "LS_CTRL", },
     NRF_NC, "BLE SoC (nRF54L05/L15-QFAA fit unchanged); I2C on clock pins P1.08/P1.04, interrupts on P0/P1 (wake-capable); pins chosen for the fan-out"),
    # Nordic QFN48 reference layout v0.8: same designators, footprints and pin order (copied layout)
    L("L1", "4.7uH", "C76799", "DCC", "DECD", fp=NL1608, mpn="TDK MLZ1608M4R7WT000", desc="DC/DC inductor"),
    C("C1", "2.2uF", "C335106", "GND", "DECD", fp=NC0201, mpn="Murata GRM033R61A225KE47D", desc="DECD"),
    ("FB1", "Device:FerriteBead_Small", "120R@100MHz", NL0201, "C97850", "Murata BLM03AG121SN1D",
     {"1": "DECD", "2": "DECA"}, [], "DECD to DECA/DECRF"),
    C("C2", "2.2uF", "C335106", "GND", "DECA", fp=NC0201, mpn="Murata GRM033R61A225KE47D", desc="DECA/DECRF"),
    C("C5", "2.2nF", "C161479", "GND", "DECA", fp=NC0201, mpn="Murata GRM033R71A222KA01D", desc="DECRF (pin 33); 2.2 nF per datasheet v1.0"),
    C("C12", "10nF", "C76941", "GND", "DECA", fp=NC0201, mpn="Murata GRM033R71A103KA01D", desc="DECA (pin 43)"),
    C("C3", "10uF", "C15525", "GND", "VDD_2V0", fp=NC0402, desc="VDD bulk"),
    C("C10", "100nF", "C307380", "VDD_2V0", "GND", fp=NC0201), C("C4", "100nF", "C307380", "VDD_2V0", "GND", fp=NC0201),
    C("C7", "100nF", "C307380", "VDD_2V0", "GND", fp=NC0201), C("C8", "100nF", "C307380", "VDD_2V0", "GND", fp=NC0201),
    R("R1", "1k", "C270365", "nRESET_IC", "nRESET", fp=NR0201, desc="nRESET series"),
    C("C13", "3.9pF", "C76926", "GND", "nRESET_IC", fp=NC0201, mpn="Murata GRM0335C1H3R9CA01D", desc="nRESET filter"),
    ("X1", "Device:Crystal", "32.768kHz 9pF", "wakeband:Nordic_XTAL_2012", "C96341", "Epson FC-12M X1A0000610008",
     {"1": "XL2", "2": "XL1"}, [], "LFXO (wake from System OFF on the GRTC); internal load caps"),
    ("X2", "Device:Crystal_GND24", "32MHz 8pF", "wakeband:Nordic_BT-XTAL_2016", "C2965582", "Yangxing XL7EL89CKI-111YLC-32M",
     {"1": "XC1", "3": "XC2", "2": "GND", "4": "GND"}, [], "HFXO; internal load caps"),
    # RF: Nordic low-pass ladder (exact reference parts, 0201), then a pi network for the antenna
    L("L2", "2.7nH", "C7216765", "ANT", "RF1", fp=NL0201, mpn="Murata LQP03HQ2N7B02D"),
    C("C6", "1.5pF", "C435397", "GND", "RF1", fp=NC0201, mpn="Murata GJM0335C1E1R5WB01D", desc="ground only to VSS_PA (pin 32)"),
    L("L3", "3.5nH", "C3911055", "RF1", "RF2", fp=NL0201, mpn="Murata LQP03HQ3N5B02D"),
    C("C9", "2.0pF", "C668326", "GND", "RF2", fp=NC0201, mpn="Murata GJM0335C1E2R0WB01D", desc="ground on the bottom layer only"),
    L("L4", "3.5nH", "C3911055", "RF2", "RF_50", fp=NL0201, mpn="Murata LQP03HQ3N5B02D"),
    C("C11", "0.3pF", "C76927", "GND", "RF_50", fp=NC0201, mpn="Murata GRM0335C1HR30BA01D"),
    C("C14", "DNP", "", "RF_50", desc="antenna match: shunt 1 (tune; fitted parts per README)"),
    R("R2", "0R", "C17168", "RF_50", "ANT_FEED", desc="antenna match: series (tune; 0R to start)"),
    C("C15", "DNP", "", "ANT_FEED", desc="antenna match: shunt 2 (tune)"),
    ("AE1", "Device:Antenna_Chip", "2450AT18A0100001E", "RF_Antenna:Johanson_2450AT18x100", "C17430588", "Johanson 2450AT18A0100001E",
     {"1": "ANT_FEED"}, ["2"], "2.4 GHz chip antenna, 3.2 x 1.6 x 1.3 mm"),
    # ---------------- sensors ----------------
    ("U401", "wakeband:LIS2DW12", "LIS2DW12TR", "Package_LGA:LGA-12_2x2mm_P0.5mm", "C189624", "ST LIS2DW12TR",
     {"1": "I2C_SCL", "2": "VDD_2V0", "3": "VDD_2V0", "4": "I2C_SDA", "5": "GND", "6": "GND", "7": "GND", "8": "GND",
      "9": "VDD_2V0", "10": "VDD_2V0", "11": "ACC_INT2", "12": "ACC_INT1"}, [], "accelerometer, I2C 0x19"),
    C("C401", "100nF", "C1525", "VDD_2V0"), C("C402", "100nF", "C1525", "VDD_2V0"),
    R("R203", "4.7k", "C25900", "VDD_2V0", "I2C_SDA", desc="I2C pull-up"), R("R204", "4.7k", "C25900", "VDD_2V0", "I2C_SCL", desc="I2C pull-up"),
    # ---------------- haptics ----------------
    ("U501", "Driver:DRV2605LDGS", "DRV2605LDGSR", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "C527464", "TI DRV2605LDGSR",
     {"1": "REG", "2": "I2C_SCL", "3": "I2C_SDA", "4": "GND", "5": "HAPT_EN", "6": "VBAT", "7": "LRA_P", "8": "GND", "9": "LRA_N", "10": "VBAT"},
     [], "LRA driver, I2C 0x5A, powered from the cell"),
    C("C501", "1uF", "C52923", "VBAT"), C("C502", "1uF", "C52923", "REG"),
    ("TP501", "Connector:TestPoint", "LRA+", "wakeband:Pad_SMD_1.0x1.5mm", "", "", {"1": "LRA_P"}, [], "LRA lead"),
    ("TP502", "Connector:TestPoint", "LRA-", "wakeband:Pad_SMD_1.0x1.5mm", "", "", {"1": "LRA_N"}, [], "LRA lead"),
    # ---------------- power: BQ25125 (BQ25120A pin-compatible) ----------------
    ("U201", "wakeband:BQ25125", "BQ25125", "wakeband:TI_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm", "C2871567", "TI BQ25125YFPR",
     {"A1": "GND", "D5": "GND", "A5": "GND", "A2": "VIN", "A3": "PMID", "B3": "PMID", "B1": "VBAT", "B2": "VBAT",
      "A4": "SW", "B5": "VSYS", "B4": "PMID", "C4": "PMID", "C5": "VLED",
      "C1": "ISET", "C2": "GND", "C3": "TS", "D1": "GND",
      "E4": "I2C_SDA", "E5": "I2C_SCL", "D2": "PMIC_INT", "D4": "DOCK_PG", "E2": "CHG_CD", "E3": "LS_CTRL", "E1": "CHG_MR"},
     ["D3"], "charger 4.2 V, buck 1.8 V (default, unused), LS/LDO for the LED driver (firmware sets LS mode), I2C 0x6A; BQ25120A fits unchanged"),
    ("L201", "Device:L", "2.2uH", "Inductor_SMD:L_Murata_DFE201610P", "C337891", "Murata DFE201610E-2R2M", {"1": "SW", "2": "VSYS"}, [], "buck inductor (SYS buck must stay enabled: the BQ25125's /CD and LSCTRL thresholds are referenced to VSYS; output unloaded)"),
    C("C201", "1uF", "C52923", "VIN", desc="IN (25 V)"),
    C("C206", "10uF", "C96446", "PMID", fp=C0603, desc="PMID and VINLS (>= 10x the LS cap)"),
    C("C205", "10uF", "C96446", "VSYS", fp=C0603, desc="SYS (buck output, unloaded)"),
    C("C202", "2.2uF", "C23630", "VBAT", fp=C0603, desc="BAT"),
    ("U203", "wakeband:TPS7A0220", "TPS7A0220", "wakeband:Texas_X2SON-4_1x1mm_P0.65mm_SilkTrim", "C2860934", "TI TPS7A0220PDQNR",
     {"4": "PMID", "3": "PMID", "1": "VDD_2V0", "2": "GND", "5": "GND"}, [], "2.0 V logic rail (1.97 V min, clears the nRF54L power-on-reset minimum of 1.75 V)"),
    C("C210", "1uF", "C307385", "PMID", fp=NC0201, mpn="Samsung CL03A105MO3NRNH", desc="LDO input"), C("C211", "1uF", "C307385", "VDD_2V0", fp=NC0201, mpn="Samsung CL03A105MO3NRNH", desc="LDO output"),
    R("R202", "6.65k", "C45194", "ISET", "GND", desc="30 mA charge (200 AOhm / 6.65k)"),
    R("R207", "14k", "C54831", "VIN", "TS", desc="TS divider, high side (from VIN)"),
    R("R208", "14.3k", "C25855", "TS", "GND", desc="TS divider, low side"),
    ("TH201", "Device:Thermistor_NTC", "10k B3380", R0402, "C77131", "Murata NCP15XH103F03RC", {"1": "TS", "2": "GND"}, [], "NTC at the cell"),
    ("JP201", "Jumper:SolderJumper_2_Bridged", "I_BAT", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm", "", "",
     {"1": "BATT_P", "2": "VBAT"}, [], "cut to measure battery current"),
    TP("TP201", "BAT+ pad", "BATT_P", "TestPoint:TestPoint_Pad_2.0x2.0mm", "cell +"),
    TP("TP202", "BAT- pad", "GND", "TestPoint:TestPoint_Pad_1.5x1.5mm", "cell -"),
    TP("TP203", "MR", "CHG_MR", TP08, "BQ25120A /MR (short to GND: wake, ship-mode exit, reset)"),
    # ---------------- LED ----------------
    ("U202", "wakeband:IS31FL3193", "IS31FL3193", "Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm", "C2653363", "Lumissil IS31FL3193-DLS2-TR",
     {"1": "LED_EN", "2": "PMID", "3": "LED_G", "4": "LED_B", "5": "LED_R", "6": "GND", "7": "GND", "8": "I2C_SCL", "9": "I2C_SDA", "11": "GND"},
     ["10"], "RGB LED driver, I2C 0x68; VCC on PMID (always up, so its I2C pins never clamp the bus); OUT1 green, OUT2 blue, OUT3 red (pins chosen for layout)"),
    C("C208", "1uF", "C52923", "VLED", desc="LS/LDO output (LED anode)"), C("C209", "100nF", "C1525", "PMID", desc="IS31FL3193 VCC"),
    R("R211", "100k", "C25741", "LED_EN", "GND", desc="SDB pull-down (LED driver off by default)"),
    ("D702", "Device:LED_ABGR", "TJ-S1615SW6TGLCCYRGB-A5", "wakeband:LED_TOGIALED_1615_RGB_CommonAnode", "C273610", "TOGIALED TJ-S1615SW6TGLCCYRGB-A5",
     {"1": "VLED", "2": "LED_B", "3": "LED_G", "4": "LED_R"}, [], "RGB status LED"),
    # ---------------- dock contacts and debug ----------------
    ("J601", "Connector_Generic:Conn_01x04", "Dock landing pads", "wakeband:DockLanding_4xB_D1.6mm", "", "",
     {"1": "VIN", "2": "GND", "3": "PAD_SWDCLK", "4": "PAD_SWDIO"}, [], "4 B-side pogo landings (logs: SEGGER RTT over SWD)"),
    ("D601", "Device:D_Zener", "ESD5681N07", "Diode_SMD:D_SOD-882", "C240204", "Will Semi ESD5681N07-2/TR", {"1": "VIN", "2": "GND"}, [], "VIN TVS"),
    ("D602", "Device:D_TVS", "TPD1E10B06", "Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm", "C48260", "TI TPD1E10B06DPYR", {"1": "PAD_SWDCLK", "2": "GND"}, [], "ESD"),
    ("D603", "Device:D_TVS", "TPD1E10B06", "Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm", "C48260", "TI TPD1E10B06DPYR", {"1": "PAD_SWDIO", "2": "GND"}, [], "ESD"),
    R("R601", "100", "C25076", "PAD_SWDCLK", "SWDCLK"), R("R602", "100", "C25076", "PAD_SWDIO", "SWDIO"),
    TP("TP401", "ACC_INT2", "ACC_INT2"), TP("TP701", "nRESET", "nRESET"),  TP("TP705", "PMID", "PMID"), TP("TP706", "VBAT", "VBAT"), TP("TP707", "GND", "GND"),
]
FLAGS = ["VIN", "GND", "VBAT", "DECD", "DECA", "REG", "VSYS"]
DNP = {"C14", "C15"}
