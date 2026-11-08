"""Write ../wakeband.kicad_sym: LIS2DW12 (from rev A) plus box symbols for the rev B parts
(nRF54L10-QFAA, BQ25125, IS31FL3193). Pin lists follow the datasheets (see ../README.md)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import symlib
REVA = os.path.join(HERE, '..', '..', 'rigid-rev-a', 'wakeband.kicad_sym')
OUT = os.path.join(HERE, '..', 'wakeband.kicad_sym')

# (number, name, type) per side, listed top-to-bottom (left/right) as drawn
NRF = dict(
    name='nRF54L10-QFAA', ref='U', fp='Package_DFN_QFN:QFN-48-1EP_6x6mm_P0.4mm_EP4.6x4.6mm',
    desc='Nordic nRF54L10 BLE SoC, QFN48 6x6 mm (pin-compatible with nRF54L05/L15-QFAA)', ds='https://docs.nordicsemi.com/bundle/ps_nrf54L15/page/keyfeatures_html5.html',
    left=[('10', 'VDD', 'power_in'), ('22', 'VDD', 'power_in'), ('36', 'VDD', 'power_in'), ('47', 'VDD', 'power_in'), ('48', 'VDD', 'power_in'), None,
          ('46', 'DCC', 'passive'), ('45', 'DECD', 'passive'), ('43', 'DECA', 'passive'), ('33', 'DECRF', 'passive'), None,
          ('34', 'XC1', 'passive'), ('35', 'XC2', 'passive'), ('1', 'P1.00/XL1', 'bidirectional'), ('2', 'P1.01/XL2', 'bidirectional'), None,
          ('31', 'ANT', 'passive'), ('32', 'VSS_PA', 'passive'), None,
          ('30', 'nRESET', 'input'), ('25', 'SWDIO', 'bidirectional'), ('26', 'SWDCLK', 'input'), None,
          ('44', 'VSS', 'power_in'), ('49', 'EP', 'power_in')],
    right=[('23', 'P0.00', 'bidirectional'), ('24', 'P0.01', 'bidirectional'), ('27', 'P0.02', 'bidirectional'), ('28', 'P0.03', 'bidirectional'),
           ('29', 'P0.04', 'bidirectional'), None,
           ('3', 'P1.02/NFC1', 'bidirectional'), ('4', 'P1.03/NFC2', 'bidirectional'), ('5', 'P1.04', 'bidirectional'), ('6', 'P1.05', 'bidirectional'),
           ('7', 'P1.06', 'bidirectional'), ('8', 'P1.07', 'bidirectional'), ('9', 'P1.08', 'bidirectional'), ('37', 'P1.09', 'bidirectional'),
           ('38', 'P1.10', 'bidirectional'), ('39', 'P1.11', 'bidirectional'), ('40', 'P1.12', 'bidirectional'), ('41', 'P1.13', 'bidirectional'),
           ('42', 'P1.14', 'bidirectional'), None,
           ('11', 'P2.00', 'bidirectional'), ('12', 'P2.01', 'bidirectional'), ('13', 'P2.02', 'bidirectional'), ('14', 'P2.03', 'bidirectional'),
           ('15', 'P2.04', 'bidirectional'), ('16', 'P2.05', 'bidirectional'), ('17', 'P2.06', 'bidirectional'), ('18', 'P2.07', 'bidirectional'),
           ('19', 'P2.08', 'bidirectional'), ('20', 'P2.09', 'bidirectional'), ('21', 'P2.10', 'bidirectional')])
BQ = dict(
    name='BQ25125', ref='U', fp='wakeband:TI_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm',
    desc='TI BQ25125 (BQ25120A family) linear charger, 1.8 V buck, LS/LDO, I2C (DSBGA-25 YFP)', ds='https://www.ti.com/lit/ds/symlink/bq25125.pdf',
    left=[('A2', 'IN', 'power_in'), ('A3', 'PMID', 'power_out'), ('B3', 'PMID', 'passive'), ('B1', 'BAT', 'power_in'), ('B2', 'BAT', 'passive'), None,
          ('C3', 'TS', 'input'), ('C1', 'ISET', 'passive'), ('C2', 'ILIM', 'passive'), ('D1', 'IPRETERM', 'passive'), None,
          ('A1', 'GND', 'power_in'), ('D5', 'GND', 'passive'), ('A5', 'PGND', 'passive')],
    right=[('A4', 'SW', 'power_out'), ('B5', 'SYS', 'input'), ('B4', 'VINLS', 'power_in'), ('C4', 'VINLS', 'passive'), ('C5', 'LS/LDO', 'power_out'), None,
           ('E4', 'SDA', 'bidirectional'), ('E5', 'SCL', 'input'), ('D2', '~{INT}', 'open_collector'), ('D4', '~{PG}', 'open_collector'),
           ('D3', '~{RESET}', 'open_collector'), None,
           ('E2', '~{CD}', 'input'), ('E3', 'LSCTRL', 'input'), ('E1', '~{MR}', 'input')])
IS31 = dict(
    name='IS31FL3193', ref='U', fp='Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm',
    desc='Lumissil IS31FL3193 3-channel LED driver, I2C, DFN-10 3x3', ds='https://www.lumissil.com/assets/pdf/core/IS31FL3193_DS.pdf',
    left=[('2', 'VCC', 'power_in'), ('1', 'SDB', 'input'), ('7', 'AD', 'input'), ('8', 'SCL', 'input'), ('9', 'SDA', 'bidirectional')],
    right=[('3', 'OUT1', 'open_collector'), ('4', 'OUT2', 'open_collector'), ('5', 'OUT3', 'open_collector'), ('10', 'V_BM', 'output'), None,
           ('6', 'GND', 'power_in'), ('11', 'EP', 'passive')])


def prop(k, v, x, y, hide=False):
    h = '\n\t\t\t(hide yes)' if hide else ''
    return (f'\t\t(property "{k}" "{v}"\n\t\t\t(at {x:g} {y:g} 0){h}\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
            f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')


def pin(num, name, typ, x, y, ang, hide_name=False):
    return (f'\t\t\t(pin {typ} line\n\t\t\t\t(at {x:g} {y:g} {ang})\n\t\t\t\t(length 2.54)\n'
            f'\t\t\t\t(name "{name}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
            f'\t\t\t\t(number "{num}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n')


def box(d, width=25.4):
    n = max(len(d['left']), len(d['right']))
    top = round(n * 2.54 / 2 / 2.54) * 2.54
    hw = width / 2
    s = (f'\t(symbol "{d["name"]}"\n\t\t(pin_names\n\t\t\t(offset 1.016)\n\t\t)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
         f'\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)\n')
    s += prop('Reference', d['ref'], -hw, top + 2.54) + prop('Value', d['name'], hw, top + 2.54)
    s += prop('Footprint', d['fp'], 0, 0, True) + prop('Datasheet', d['ds'], 0, 0, True) + prop('Description', d['desc'], 0, 0, True)
    s += (f'\t\t(symbol "{d["name"]}_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start {-hw:g} {top + 1.27:g})\n\t\t\t\t(end {hw:g} {top - n * 2.54 - 1.27 + 2.54:g})\n'
          f'\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')
    s += f'\t\t(symbol "{d["name"]}_1_1"\n'
    for side, x, ang in (('left', -hw - 2.54, 0), ('right', hw + 2.54, 180)):
        for i, p in enumerate(d[side]):
            if p: s += pin(p[0], p[1], p[2], x, round(top - i * 2.54, 2), ang)
    s += '\t\t)\n\t\t(embedded_fonts no)\n\t)\n'
    return s


LDO = dict(
    name='TPS7A0220', ref='U', fp='wakeband:Texas_X2SON-4_1x1mm_P0.65mm_SilkTrim',
    desc='TI TPS7A0220 2.0 V LDO, 25 nA Iq, X2SON-4 (DQN)', ds='https://www.ti.com/lit/ds/symlink/tps7a02.pdf',
    left=[('4', 'IN', 'power_in'), ('3', 'EN', 'input'), None, ('2', 'GND', 'power_in'), ('5', 'EP', 'passive')],
    right=[('1', 'OUT', 'power_out')])
lis = symlib.get('wakeband', 'LIS2DW12', REVA)
txt = ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n\t(generator_version "10.0")\n'
       + '\t' + lis + '\n' + box(NRF, 30.48) + box(BQ, 22.86) + box(IS31, 17.78) + box(LDO, 12.7) + ')\n')
open(OUT, 'w').write(txt)
print('wrote', OUT)
