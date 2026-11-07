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


def R(ref, val, lcsc, a, b, desc="", fp=R0402, mpn=""):
    return (ref, "Device:R", val, fp, lcsc, mpn, {"1": a, "2": b}, [], desc)


def C(ref, val, lcsc, a, b="GND", fp=C0402, desc="", mpn=""):
    return (ref, "Device:C", val, fp, lcsc, mpn, {"1": a, "2": b}, [], desc)


def L(ref, val, lcsc, a, b, fp=L0201, desc="", mpn=""):
    return (ref, "Device:L", val, fp, lcsc, mpn, {"1": a, "2": b}, [], desc)


def TP(ref, val, net, fp=TP08, desc=""):
    return (ref, "Connector:TestPoint", val, fp, "", "", {"1": net}, [], desc)


NRF_NC = ["3", "4", "5", "6", "7", "8", "9", "14", "17", "20", "21", "23", "24", "27", "28", "29"]
PARTS = [
    # ---------------- radio: nRF54L15 (Nordic QFN48 reference circuit, config 1) ----------------
    ("U1", "wakeband:nRF54L10-QFAA", "nRF54L10-QFAA", "Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm", "C44800139", "Nordic NRF54L10-QFAA-R7",
     {"10": "VDD_1V8", "22": "VDD_1V8", "36": "VDD_1V8", "47": "VDD_1V8", "48": "VDD_1V8",
      "46": "DCC", "45": "DECD", "43": "DECA", "33": "DECA", "34": "XC1", "35": "XC2", "1": "XL1", "2": "XL2",
      "31": "ANT", "32": "GND", "30": "nRESET_IC", "25": "SWDIO", "26": "SWDCLK", "44": "GND", "49": "GND",
      "37": "PMIC_INT", "38": "DOCK_PG", "39": "I2C_SDA", "40": "I2C_SCL", "41": "ACC_INT1", "42": "ACC_INT2",
      "11": "HAPT_EN", "12": "CHG_CD", "13": "LS_CTRL", "15": "LED_DBG", "16": "LED_EN", "18": "UART_RX", "19": "UART_TX"},
     NRF_NC, "BLE SoC (nRF54L05/L15-QFAA fit unchanged); I2C on clock pins P1.11/P1.12, interrupts on P1 (wake-capable), outputs on P2"),
    L("L1", "4.7uH", "C114862", "DCC", "DECD", fp="Inductor_SMD:L_0603_1608Metric", mpn="Murata LQM18PN4R7MFRL", desc="DC/DC inductor"),
    C("C1", "2.2uF", "C12530", "DECD", desc="DECD"),
    ("FB1", "Device:FerriteBead_Small", "120R@100MHz", "Inductor_SMD:L_0402_1005Metric", "C107331", "TDK MPZ1005S121CT000",
     {"1": "DECD", "2": "DECA"}, [], "DECD to DECA/DECRF"),
    C("C2", "2.2uF", "C12530", "DECA", desc="DECA/DECRF"),
    C("C5", "2.2nF", "C1531", "DECA", desc="DECRF (pin 33); 2.2 nF per datasheet v1.0"), C("C12", "10nF", "C15195", "DECA", desc="DECA (pin 43)"),
    C("C3", "10uF", "C15525", "VDD_1V8", desc="VDD pins 47/48"), C("C10", "100nF", "C1525", "VDD_1V8", desc="VDD pins 47/48"),
    C("C4", "100nF", "C1525", "VDD_1V8", desc="VDD pin 10"), C("C7", "100nF", "C1525", "VDD_1V8", desc="VDD pin 22"),
    C("C8", "100nF", "C1525", "VDD_1V8", desc="VDD pin 36"),
    R("R1", "1k", "C11702", "nRESET", "nRESET_IC", desc="nRESET series"), C("C13", "3.9pF", "C3907811", "nRESET_IC", desc="nRESET filter"),
    ("X1", "Device:Crystal", "32.768kHz 9pF", "Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm", "C96341", "Epson FC-12M X1A0000610008",
     {"1": "XL1", "2": "XL2"}, [], "LFXO (wake from System OFF on the GRTC); internal load caps"),
    ("X2", "Device:Crystal_GND24", "32MHz 8pF", "Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm", "C2965582", "Yangxing XL7EL89CKI-111YLC-32M",
     {"1": "XC1", "3": "XC2", "2": "GND", "4": "GND"}, [], "HFXO; internal load caps"),
    # RF: Nordic low-pass ladder (exact reference parts, 0201), then a pi network for the antenna
    L("L2", "2.7nH", "C7216765", "ANT", "RF1", mpn="Murata LQP03HQ2N7B02D"),
    C("C6", "1.5pF", "C435397", "RF1", fp=C0201, mpn="Murata GJM0335C1E1R5WB01D", desc="ground only to VSS_PA (pin 32)"),
    L("L3", "3.5nH", "C3911055", "RF1", "RF2", mpn="Murata LQP03HQ3N5B02D"),
    C("C9", "2.0pF", "C668326", "RF2", fp=C0201, mpn="Murata GJM0335C1E2R0WB01D", desc="ground on the bottom layer only"),
    L("L4", "3.5nH", "C3911055", "RF2", "RF_50", mpn="Murata LQP03HQ3N5B02D"),
    C("C11", "0.3pF", "C76927", "RF_50", fp=C0201, mpn="Murata GRM0335C1HR30BA01D"),
    C("C14", "DNP", "", "RF_50", desc="antenna match: shunt 1 (tune; fitted parts per README)"),
    R("R2", "0R", "C17168", "RF_50", "ANT_FEED", desc="antenna match: series (tune; 0R to start)"),
    C("C15", "DNP", "", "ANT_FEED", desc="antenna match: shunt 2 (tune)"),
    ("AE1", "Device:Antenna_Chip", "2450AT18A0100001E", "RF_Antenna:Johanson_2450AT18x100", "C17430588", "Johanson 2450AT18A0100001E",
     {"1": "ANT_FEED"}, ["2"], "2.4 GHz chip antenna, 3.2 x 1.6 x 1.3 mm"),
    # ---------------- sensors ----------------
    ("U401", "wakeband:LIS2DW12", "LIS2DW12TR", "Package_LGA:LGA-12_2x2mm_P0.5mm", "C189624", "ST LIS2DW12TR",
     {"1": "I2C_SCL", "2": "VDD_1V8", "3": "VDD_1V8", "4": "I2C_SDA", "5": "GND", "6": "GND", "7": "GND", "8": "GND",
      "9": "VDD_1V8", "10": "VDD_1V8", "11": "ACC_INT2", "12": "ACC_INT1"}, [], "accelerometer, I2C 0x19"),
    C("C401", "100nF", "C1525", "VDD_1V8"), C("C402", "100nF", "C1525", "VDD_1V8"),
    R("R203", "4.7k", "C25900", "VDD_1V8", "I2C_SDA", desc="I2C pull-up"), R("R204", "4.7k", "C25900", "VDD_1V8", "I2C_SCL", desc="I2C pull-up"),
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
      "A4": "SW", "B5": "VDD_1V8", "B4": "PMID", "C4": "PMID", "C5": "VLED",
      "C1": "ISET", "C2": "GND", "C3": "TS", "D1": "GND",
      "E4": "I2C_SDA", "E5": "I2C_SCL", "D2": "PMIC_INT", "D4": "DOCK_PG", "E2": "CHG_CD", "E3": "LS_CTRL", "E1": "CHG_MR"},
     ["D3"], "charger 4.2 V, buck 1.8 V (default), LS/LDO for the LED driver (firmware sets LS mode), I2C 0x6A; BQ25120A fits unchanged"),
    ("L201", "Device:L", "2.2uH", "Inductor_SMD:L_Murata_DFE201610P", "C337891", "Murata DFE201610E-2R2M", {"1": "SW", "2": "VDD_1V8"}, [], "buck inductor"),
    C("C201", "1uF", "C52923", "VIN", desc="IN (25 V)"),
    C("C206", "10uF", "C96446", "PMID", fp=C0603, desc="PMID and VINLS (>= 10x the LS cap)"),
    C("C205", "10uF", "C96446", "VDD_1V8", fp=C0603, desc="SYS"),
    C("C202", "2.2uF", "C23630", "VBAT", fp=C0603, desc="BAT"),
    R("R202", "6.65k", "C45194", "ISET", "GND", desc="30 mA charge (200 AOhm / 6.65k)"),
    R("R207", "14k", "C54831", "VIN", "TS", desc="TS divider, high side (from VIN)"),
    R("R208", "14.3k", "C25855", "TS", "GND", desc="TS divider, low side"),
    ("TH201", "Device:Thermistor_NTC", "10k B3380", R0402, "C77131", "Murata NCP15XH103F03RC", {"1": "TS", "2": "GND"}, [], "NTC at the cell"),
    R("R209", "100k", "C25741", "VDD_1V8", "PMIC_INT", desc="/INT pull-up"),
    R("R210", "100k", "C25741", "VDD_1V8", "DOCK_PG", desc="/PG pull-up (dock detect)"),
    ("JP201", "Jumper:SolderJumper_2_Bridged", "I_BAT", "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm", "", "",
     {"1": "BATT_P", "2": "VBAT"}, [], "cut to measure battery current"),
    TP("TP201", "BAT+ pad", "BATT_P", "TestPoint:TestPoint_Pad_2.0x2.0mm", "cell +"),
    TP("TP202", "BAT- pad", "GND", "TestPoint:TestPoint_Pad_1.5x1.5mm", "cell -"),
    TP("TP203", "MR", "CHG_MR", TP08, "BQ25120A /MR (short to GND: wake, ship-mode exit, reset)"),
    # ---------------- LED ----------------
    ("U202", "wakeband:IS31FL3193", "IS31FL3193", "Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm", "C2653363", "Lumissil IS31FL3193-DLS2-TR",
     {"1": "LED_EN", "2": "VLED", "3": "LED_R", "4": "LED_G", "5": "LED_B", "6": "GND", "7": "GND", "8": "I2C_SCL", "9": "I2C_SDA", "11": "GND"},
     ["10"], "RGB LED driver, I2C 0x68"),
    C("C208", "1uF", "C52923", "VLED"), C("C209", "100nF", "C1525", "VLED"),
    R("R211", "100k", "C25741", "LED_EN", "GND", desc="SDB pull-down (LED driver off by default)"),
    ("D702", "Device:LED_ABGR", "TJ-S1615SW6TGLCCYRGB-A5", "wakeband:LED_TOGIALED_1615_RGB_CommonAnode", "C273610", "TOGIALED TJ-S1615SW6TGLCCYRGB-A5",
     {"1": "VLED", "2": "LED_B", "3": "LED_G", "4": "LED_R"}, [], "RGB status LED"),
    # ---------------- dock contacts and debug ----------------
    ("J601", "Connector_Generic:Conn_01x06", "Dock landing pads", "wakeband:DockLanding_4xB_D1.6mm_2xUART", "", "",
     {"1": "VIN", "2": "GND", "3": "PAD_SWDCLK", "4": "PAD_SWDIO", "5": "PAD_RX", "6": "PAD_TX"}, [], "4 B-side pogo landings + 2 UART pads"),
    ("D601", "Device:D_Zener", "SMF12A", "Diode_SMD:D_SOD-123F", "C207255", "Littelfuse SMF12A", {"1": "VIN", "2": "GND"}, [], "VIN TVS"),
    ("D602", "Device:D_TVS", "TPD1E10B06", "Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm", "C48260", "TI TPD1E10B06DPYR", {"1": "PAD_SWDCLK", "2": "GND"}, [], "ESD"),
    ("D603", "Device:D_TVS", "TPD1E10B06", "Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm", "C48260", "TI TPD1E10B06DPYR", {"1": "PAD_SWDIO", "2": "GND"}, [], "ESD"),
    ("D604", "Device:D_TVS", "TPD1E10B06", "Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm", "C48260", "TI TPD1E10B06DPYR", {"1": "PAD_RX", "2": "GND"}, [], "ESD"),
    ("D605", "Device:D_TVS", "TPD1E10B06", "Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm", "C48260", "TI TPD1E10B06DPYR", {"1": "PAD_TX", "2": "GND"}, [], "ESD"),
    R("R601", "100", "C25076", "PAD_SWDCLK", "SWDCLK"), R("R602", "100", "C25076", "PAD_SWDIO", "SWDIO"),
    R("R603", "100", "C25076", "PAD_RX", "UART_RX"), R("R604", "100", "C25076", "PAD_TX", "UART_TX"),
    R("R605", "100k", "C25741", "UART_RX", "GND", desc="RX idle pull-down"),
    ("D701", "Device:LED", "red DNP", "LED_SMD:LED_0402_1005Metric", "", "XINGLIGHT XL-1005SURC", {"1": "GND", "2": "LED_A"}, [], "debug LED (not fitted)"),
    R("R701", "1k DNP", "", "LED_DBG", "LED_A", desc="debug LED (not fitted)"),
    TP("TP401", "ACC_INT2", "ACC_INT2"), TP("TP701", "nRESET", "nRESET"),  TP("TP705", "PMID", "PMID"), TP("TP706", "VBAT", "VBAT"), TP("TP707", "GND", "GND"),
]
FLAGS = ["VIN", "GND", "VBAT", "DECD", "DECA", "VDD_1V8", "REG"]
DNP = {"C14", "C15", "D701", "R701"}
