#!/usr/bin/env python3
"""Generate the Karetao bench wiring schematic as a KiCad 8 project.

Run:  python3 generate_schematic.py [--preview preview.png]
Writes karetao_bench_wiring.kicad_sch and karetao_bench_wiring.kicad_pro beside this file.
Every symbol is embedded in the schematic, so no KiCad library is needed to open it.

Facts come from Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md (STM32 pins), SYSTEM_CONFIGURATION.md
section 2.1 (axis to mux channel map, fitted encoders, motor 0 CAN ID), the Pi README (header pins) and the
vendor references in icm-project/references. Anything the documents do not state is marked Provisional in
a note on the sheet; see README.md beside this file for the list.
"""
import argparse, uuid, os, sys

MM = 2.54
FONT = "(effects (font (size 1.27 1.27)))"
def U(): return str(uuid.uuid4())
def q(s): return '"' + s.replace('"', '\\"') + '"'

# ---------------------------------------------------------------- symbol library (lib coordinates, y up)
class Sym:
    def __init__(self, name, hw, left, right, desc="", power=False, value=None, ref="U"):
        self.name, self.hw, self.left, self.right, self.desc, self.power = name, hw, left, right, desc, power
        self.value, self.ref = value or name, ref
        n = max(len(left), len(right))
        self.hh = (n + 1) * MM / 2 if not power else 0
        self.pins = {}   # number -> (name, etype, lib_x, lib_y, angle)
        num = 1
        for i, (pname, et) in enumerate(left):
            self.pins[str(num)] = (pname, et, -(hw + MM), self.hh - MM * (i + 1), 0); num += 1
        for i, (pname, et) in enumerate(right):
            self.pins[str(num)] = (pname, et, (hw + MM), self.hh - MM * (i + 1), 180); num += 1
    def pin_by_name(self, pname):
        for num, p in self.pins.items():
            if p[0] == pname: return num
        raise KeyError(pname)
    def sexp(self, prefix="karetao:"):
        lid = f"{prefix}{self.name}"
        out = [f'  (symbol {q(lid)} (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)']
        out.append(f'    (property "Reference" {q(self.ref)} (at 0 {self.hh + 1.27:.2f} 0) {FONT})')
        out.append(f'    (property "Value" {q(self.value)} (at 0 {-(self.hh + 1.27):.2f} 0) {FONT})')
        out.append(f'    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (property "Description" {q(self.desc)} (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
        out.append(f'    (symbol "{self.name}_0_1"')
        out.append(f'      (rectangle (start {-self.hw:.2f} {self.hh:.2f}) (end {self.hw:.2f} {-self.hh:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))')
        out.append(f'    (symbol "{self.name}_1_1"')
        for num, (pname, et, x, y, ang) in self.pins.items():
            out.append(f'      (pin {et} line (at {x:.2f} {y:.2f} {ang}) (length {MM}) (name {q(pname)} {FONT}) (number {q(num)} {FONT}))')
        out.append('    ))')
        return "\n".join(out)

class PowerSym:
    """KiCad-style power symbol: one hidden pin at the origin; Value is the net name."""
    def __init__(self, name, etype="power_in", flag=False):
        self.name, self.etype, self.flag = name, etype, flag
        self.pins = {"1": (name, etype, 0.0, 0.0, 90)}
        self.hh = 0; self.ref = "#PWR" if not flag else "#FLG"; self.value = name
    def sexp(self, prefix="karetao:"):
        lid = f"{prefix}{self.name}"
        if self.name == "GND":
            gfx = '(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))'
            vpos = "0 -3.81"
        elif self.flag:
            gfx = '(polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))'
            vpos = "0 3.81"
        else:
            gfx = '(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none))) (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27) (xy -0.762 1.27)) (stroke (width 0) (type default)) (fill (type outline)))'
            vpos = "0 3.81"
        return "\n".join([
            f'  (symbol {q(lid)} (power) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
            f'    (property "Reference" {q(self.ref)} (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (property "Value" {q(self.name)} (at {vpos} 0) {FONT})',
            f'    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (property "Description" {q("Power symbol: net " + self.name)} (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (symbol "{self.name}_0_1" {gfx})',
            f'    (symbol "{self.name}_1_1" (pin {self.etype} line (at 0 0 90) (length 0) hide (name {q(self.name)} {FONT}) (number "1" {FONT})))',
            '  )'])

class RSym:
    """Two-pin resistor, vertical: pin 1 at top, pin 2 at bottom (lib coords)."""
    name = "R"; ref = "R"; value = "R"; hh = 3.81
    pins = {"1": ("1", "passive", 0.0, 3.81, 270), "2": ("2", "passive", 0.0, -3.81, 90)}
    def pin_by_name(self, n): return n
    def sexp(self, prefix="karetao:"):
        return "\n".join([
            f'  (symbol "{prefix}R" (pin_numbers hide) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
            f'    (property "Reference" "R" (at 2.54 0 90) {FONT})',
            f'    (property "Value" "R" (at -2.54 0 90) {FONT})',
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (property "Description" "Resistor" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (symbol "R_0_1" (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none))))',
            '    (symbol "R_1_1"',
            f'      (pin passive line (at 0 3.81 270) (length 1.27) (name "~" {FONT}) (number "1" {FONT}))',
            f'      (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" {FONT}) (number "2" {FONT})))',
            '  )'])

PI = "power_in"; PO = "power_out"; BI = "bidirectional"; IN = "input"; OUT = "output"; PA = "passive"
LIB = {}
def add(sym): LIB[sym.name] = sym; return sym

STM32 = add(Sym("STM32F405_BOARD", 21.59,
    [("VIN_5V", PI), ("3V3", PO), ("NRST", IN), ("PA13_SWDIO", BI), ("PA14_SWCLK", IN), ("GND", PI)],
    [("PB6_I2C1_SCL", BI), ("PB7_I2C1_SDA", BI), ("PB8_CAN1_RX", IN), ("PB9_CAN1_TX", OUT),
     ("PA15_SPI3_NSS", IN), ("PC10_SPI3_SCK", IN), ("PC11_SPI3_MISO", OUT), ("PC12_SPI3_MOSI", IN), ("PA8_DATA_READY", OUT)],
    "STM32F405RGT6 board, LQFP64, HSE 8 MHz (board type and supply input Provisional)", value="STM32F405RGT6 board"))
MUX = add(Sym("TCA9548A", 12.7,
    [("VCC", PI), ("SDA", BI), ("SCL", IN), ("nRESET", IN), ("A0", IN), ("A1", IN), ("A2", IN), ("GND", PI)],
    [(f"S{k}{n}", BI) for n in range(8) for k in ("C", "D")],
    "TI TCA9548A 8-channel I2C switch, address 0x70", value="TCA9548A"))
AS = add(Sym("AS5600", 10.16, [("VDD", PI), ("SCL", IN), ("SDA", BI), ("DIR", IN)], [("OUT", OUT), ("PGO", IN), ("GND", PI)],
    "AS5600 magnetic rotary position sensor on a breakout board (3.3 V mode)", value="AS5600"))
XCVR = add(Sym("CAN_XCVR", 12.7, [("VCC", PI), ("TXD", IN), ("RXD", OUT), ("VREF", OUT), ("S", IN), ("GND", PI)],
    [("CANH", BI), ("CANL", BI)], "NXP TJA1050 high-speed CAN transceiver, 5 V supply; S low = high-speed mode", value="TJA1050"))
DRV_LEFT = [("VIN+", PI), ("CANH", BI), ("CANL", BI), ("VIN-", PI), ("GND", PI)]
DRV_IO = [("A+", PA), ("A-", PA), ("B+", PA), ("B-", PA), ("EVCC", PO), ("EGND", PO), ("COM", IN), ("EN", IN), ("DIR", IN), ("STP", IN), ("IN_1", IN)]
DRV57 = add(Sym("MKS_SERVO57D", 10.16, DRV_LEFT, DRV_IO + [("IN_2", IN), ("OUT_1", OUT), ("OUT_2", OUT), ("RS485_A", BI), ("RS485_B", BI)],
    "MKS SERVO57D closed-loop stepper driver, 12 to 24 V; EVCC/EGND 5 V 20 mA with DIP 2 and 3 ON (MKS manual p. 19)", value="MKS SERVO57D", ref="M"))
DRV42 = add(Sym("MKS_SERVO42D", 10.16, DRV_LEFT, DRV_IO,
    "MKS SERVO42D closed-loop stepper driver, 12 to 24 V; EVCC/EGND 5 V 20 mA (MKS manual p. 10)", value="MKS SERVO42D", ref="M"))
STEP = add(Sym("STEPPER_BIPOLAR", 7.62, [("A+", PA), ("A-", PA), ("B+", PA), ("B-", PA)], [],
    "Bipolar stepper motor, two coils (A, B)", value="Stepper", ref="MOT"))
KY003 = add(Sym("KY003", 7.62, [("Vin", PI), ("GND", PI), ("S", OUT)], [],
    "KY-003 Hall-effect switch module (limit switch)", value="KY-003", ref="SW"))
WSH231 = add(Sym("WSH231", 7.62, [("VCC", PI), ("GND", PI), ("N_OUT", OUT), ("S_OUT", OUT)], [],
    "WSH231 Hall-effect switch module (home switch)", value="WSH231", ref="SW"))
CANAD = add(Sym("USB_CAN_ADAPTER", 10.16, [], [("CANH", BI), ("CANL", BI), ("GND", PI)],
    "USB-CAN adapter (MKS Canable) for bring-up from a PC", value="USB-CAN adapter (MKS Canable)", ref="J"))
SPST = add(Sym("SWITCH_SPST", 5.08, [("1", PA)], [("2", PA)], "Single-pole rocker switch in the motor supply", value="Rocker switch", ref="SW"))
RPI = add(Sym("RPI5_HEADER", 17.78, [],
    [("1_3V3", PO), ("2_5V", PO), ("19_GPIO10_MOSI", OUT), ("21_GPIO9_MISO", IN), ("23_GPIO11_SCLK", OUT),
     ("24_GPIO8_CE0", OUT), ("22_GPIO25_DATA_READY", IN), ("6_GND", PI), ("20_GND", PI)],
    "Raspberry Pi 5 40-pin header, SPI0 CE0 and GPIO25 (only the pins used)", value="Raspberry Pi 5 header", ref="J"))
SWD = add(Sym("SWD_HEADER", 10.16, [], [("3V3", PI), ("SWDIO", BI), ("SWCLK", OUT), ("NRST", OUT), ("GND", PI)],
    "SWD debug header (connector type Provisional)", value="SWD header", ref="J"))
PSUM = add(Sym("PSU_MOTOR", 12.7, [], [("V+", PO), ("V-", PO)], "Motor supply 12 to 24 V DC (voltage Provisional)", value="Motor PSU 24 V (Provisional)", ref="PS"))
PSUL = add(Sym("PSU_LOGIC", 12.7, [], [("5V", PO), ("GND", PO)], "Logic 5 V supply for the STM32 board (source Provisional)", value="Logic PSU 5 V (Provisional)", ref="PS"))
EST = add(Sym("ESTOP_2P", 12.7, [("IN1", PA), ("IN2", PA)], [("OUT1", PA), ("OUT2", PA)],
    "Two-pole E-stop or power switch in the motor supply (SAFE-01; to be fitted, ruling R25b)", value="E-STOP (to be fitted)", ref="SW"))
R = add(RSym())
for n in ("+3V3", "+5V", "GND", "VMOT", "VMOT_SW"): add(PowerSym(n))
add(PowerSym("PWR_FLAG", "power_out", flag=True))

# ---------------------------------------------------------------- sheet model (sheet coordinates, y down)
ROOT = U()
items = []        # s-expressions
preview = []      # (kind, data) for the PNG renderer
checks = []       # (x, y) points that must be wire endpoints
wire_ends = set()

def wire(x1, y1, x2, y2):
    items.append(f'(wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    wire_ends.add((round(x1, 2), round(y1, 2))); wire_ends.add((round(x2, 2), round(y2, 2)))
    preview.append(("wire", (x1, y1, x2, y2)))

named_points = []   # (net name, x, y) for labels and power pins
def label(name, x, y, direction):
    named_points.append((name, x, y))
    ang, just = (0, "left") if direction > 0 else (180, "right")
    items.append(f'(label {q(name)} (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid "{U()}"))')
    checks.append((x, y)); preview.append(("label", (name, x, y, direction)))

def no_connect(x, y):
    items.append(f'(no_connect (at {x:.2f} {y:.2f}) (uuid "{U()}"))'); preview.append(("nc", (x, y)))

def text(s, x, y, size=1.27):
    items.append(f'(text {q(s)} (at {x:.2f} {y:.2f} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))')
    preview.append(("text", (s, x, y, size)))

def junction(x, y):
    items.append(f'(junction (at {x:.2f} {y:.2f}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')

class Inst:
    def __init__(self, sym, ref, x, y, value=None, dnp=False, rot=0):
        self.sym, self.ref, self.x, self.y, self.dnp, self.rot = sym, ref, x, y, dnp, rot
        self.value = value or sym.value
        self.uuid = U()
        self.pin_uuids = {n: U() for n in sym.pins}
        preview.append(("sym", (self, )))
    def pin_pos(self, number):
        _, _, px, py, _ = self.sym.pins[number]
        if self.rot == 0: return (self.x + px, self.y - py)
        if self.rot == 90: return (self.x - py, self.y - px)   # not used
        raise ValueError
    def pin_dir(self, number):
        return 1 if self.sym.pins[number][4] == 180 else -1   # +1: pin points right of body (right side)
    def emit(self):
        hh = getattr(self.sym, "hh", 0)
        is_power = isinstance(self.sym, PowerSym)
        ref_at = f"{self.x:.2f} {self.y - hh - 1.27:.2f}" if not is_power else f"{self.x:.2f} {self.y + 6.35:.2f}"
        val_at = f"{self.x:.2f} {self.y + hh + 1.27:.2f}" if not is_power else (f"{self.x:.2f} {self.y + 3.81:.2f}" if self.sym.name == "GND" else f"{self.x:.2f} {self.y - 3.81:.2f}")
        if isinstance(self.sym, RSym):
            ref_at, val_at = f"{self.x + 2.54:.2f} {self.y - 1.27:.2f}", f"{self.x + 2.54:.2f} {self.y + 1.27:.2f}"
        out = [f'(symbol (lib_id {q("karetao:" + self.sym.name)}) (at {self.x:.2f} {self.y:.2f} {self.rot}) (unit 1) (exclude_from_sim no) (in_bom {"no" if is_power else "yes"}) (on_board yes) (dnp {"yes" if self.dnp else "no"}) (uuid "{self.uuid}")']
        out.append(f'  (property "Reference" {q(self.ref)} (at {ref_at} 0) (effects (font (size 1.27 1.27)){" hide" if is_power else ""}))')
        out.append(f'  (property "Value" {q(self.value)} (at {val_at} 0) {FONT})')
        out.append(f'  (property "Footprint" "" (at {self.x:.2f} {self.y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        out.append(f'  (property "Datasheet" "" (at {self.x:.2f} {self.y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        for n, pu in self.pin_uuids.items():
            out.append(f'  (pin {q(n)} (uuid "{pu}"))')
        out.append(f'  (instances (project "karetao_bench_wiring" (path "/{ROOT}" (reference {q(self.ref)}) (unit 1)))))')
        return "\n".join(out)

insts = []
_pwr_n = [0]
def place(sym, ref, x, y, **kw):
    if ref in ('#PWR', '#FLG'):
        _pwr_n[0] += 1; ref = f'{ref}{_pwr_n[0]:02d}'
    i = Inst(sym, ref, x, y, **kw); insts.append(i); return i

def stub(inst, pin_name, net=None, power=None, nc=False, length=None):
    """Draw a short wire from a pin and end it in a label, a power symbol or a no-connect."""
    num = inst.sym.pin_by_name(pin_name)
    x, y = inst.pin_pos(num); d = inst.pin_dir(num)
    if nc:
        no_connect(x, y); return
    if length is None:
        length = 3 * MM if power else MM
    x2 = x + d * length
    wire(x, y, x2, y)
    if net: label(net, x2, y, d)
    if power:
        p = place(LIB[power], "#PWR", x2, y)
        if power == "GND":
            wire(x2, y, x2, y + MM); p.x, p.y = x2, y + MM
        else:
            wire(x2, y, x2, y - MM); p.x, p.y = x2, y - MM
        checks.append((p.x, p.y)); named_points.append((power, p.x, p.y))

def gnd_bus(inst, pin_names, length=3 * MM):
    """Tie several pins on one side of a symbol to GND with a vertical bus and one GND symbol below the lowest."""
    pts = []
    for pn in pin_names:
        num = inst.sym.pin_by_name(pn); x, y = inst.pin_pos(num); d = inst.pin_dir(num)
        xb = x + d * length; wire(x, y, xb, y); pts.append((xb, y))
    pts.sort(key=lambda p: p[1])
    for (xa, ya), (xb_, yb) in zip(pts, pts[1:]):
        wire(xa, ya, xb_, yb)
    xl, yl = pts[-1]
    wire(xl, yl, xl, yl + MM); place(LIB["GND"], "#PWR", xl, yl + MM)
    checks.append((xl, yl + MM)); named_points.append(("GND", xl, yl + MM))

def rstub(rinst, pin, net=None, power=None):
    x, y = rinst.pin_pos(pin)
    if pin == "1":
        wire(x, y, x, y - MM)
        if power:
            p = place(LIB[power], "#PWR", x, y - MM); checks.append((x, y - MM)); named_points.append((power, x, y - MM))
        if net:
            wire(x, y - MM, x + MM, y - MM); label(net, x + MM, y - MM, 1)
    else:
        wire(x, y, x, y + MM)
        if power:
            p = place(LIB[power], "#PWR", x, y + MM); checks.append((x, y + MM)); named_points.append((power, x, y + MM))
        if net:
            wire(x, y + MM, x + MM, y + MM); label(net, x + MM, y + MM, 1)

# ---------------------------------------------------------------- placement
# Pi and SWD on the left, STM32 centre-left, mux and sensors right, CAN below, drives along the bottom.
J1 = place(RPI, "J1", 45.72, 66.04)
stub(J1, "1_3V3", nc=True); stub(J1, "2_5V", nc=True)
gnd_bus(J1, ["6_GND", "20_GND"])
stub(J1, "19_GPIO10_MOSI", "SPI_MOSI"); stub(J1, "21_GPIO9_MISO", "SPI_MISO"); stub(J1, "23_GPIO11_SCLK", "SPI_SCK")
stub(J1, "24_GPIO8_CE0", "SPI_NSS"); stub(J1, "22_GPIO25_DATA_READY", "DATA_READY")

J2 = place(SWD, "J2", 45.72, 121.92)
stub(J2, "3V3", power="+3V3"); stub(J2, "SWDIO", "SWDIO"); stub(J2, "SWCLK", "SWCLK"); stub(J2, "NRST", "NRST"); stub(J2, "GND", power="GND")

U1 = place(STM32, "U1", 127.0, 91.44)
stub(U1, "VIN_5V", power="+5V", length=MM); stub(U1, "3V3", power="+3V3", length=3 * MM); stub(U1, "GND", power="GND")
stub(U1, "NRST", "NRST"); stub(U1, "PA13_SWDIO", "SWDIO"); stub(U1, "PA14_SWCLK", "SWCLK")
stub(U1, "PB6_I2C1_SCL", "I2C1_SCL"); stub(U1, "PB7_I2C1_SDA", "I2C1_SDA")
stub(U1, "PB8_CAN1_RX", "CAN_RX"); stub(U1, "PB9_CAN1_TX", "CAN_TX")
stub(U1, "PA15_SPI3_NSS", "SPI_NSS"); stub(U1, "PC10_SPI3_SCK", "SPI_SCK"); stub(U1, "PC11_SPI3_MISO", "SPI_MISO")
stub(U1, "PC12_SPI3_MOSI", "SPI_MOSI"); stub(U1, "PA8_DATA_READY", "DATA_READY")

R3 = place(R, "R3", 177.8, 53.34, value="4k7"); rstub(R3, "1", power="+3V3"); rstub(R3, "2", "I2C1_SCL")
R4 = place(R, "R4", 203.2, 53.34, value="4k7"); rstub(R4, "1", power="+3V3"); rstub(R4, "2", "I2C1_SDA")
R5 = place(R, "R5", 228.6, 53.34, value="10k")
text("R3, R4: I2C pull-ups; R5: mux reset pull-up. Values and location Provisional.", 170.0, 70.0, 1.0); rstub(R5, "1", power="+3V3"); rstub(R5, "2", "MUX_NRESET")

U2 = place(MUX, "U2", 215.9, 111.76)
stub(U2, "VCC", power="+3V3"); stub(U2, "SDA", "I2C1_SDA"); stub(U2, "SCL", "I2C1_SCL"); stub(U2, "nRESET", "MUX_NRESET")
gnd_bus(U2, ["A0", "A1", "A2", "GND"])
text("A2 A1 A0 = L L L: address 0x70", 172.0, 128.0, 1.0)
for n in range(8):
    if n == 1:
        stub(U2, "SC1", nc=True); stub(U2, "SD1", nc=True)
    else:
        stub(U2, f"SC{n}", f"SCL_CH{n}"); stub(U2, f"SD{n}", f"SDA_CH{n}")

sensors = [  # (ref, y, channel, note, dnp)
    ("U3", 33.02, 0, "Bench sensor on SD0 (excluded from the arm)", False),
    ("U4", 63.5, 2, "Axis 0, Joint X: NO ENCODER FITTED (sensor on hand; NOT_FITTED, SYS-ENC-002)", True),
    ("U5", 93.98, 3, "Axis 1, Joint Y, encoder fitted", False),
    ("U6", 124.46, 4, "Axis 2, Joint Z, encoder fitted", False),
    ("U7", 154.94, 5, "Axis 3, Wrist Joint 1: NO ENCODER FITTED (NOT_FITTED, SYS-ENC-002)", True),
    ("U8", 185.42, 6, "Axis 4, Wrist Joint 2, encoder fitted", False),
    ("U9", 215.9, 7, "Axis 5, Wrist Joint 3, encoder fitted", False),
]
for ref, y, ch, note, dnp in sensors:
    s = place(AS, ref, 299.72, y, dnp=dnp)
    stub(s, "VDD", power="+3V3"); stub(s, "SCL", f"SCL_CH{ch}"); stub(s, "SDA", f"SDA_CH{ch}"); stub(s, "DIR", power="GND")
    stub(s, "GND", power="GND"); stub(s, "OUT", nc=True); stub(s, "PGO", nc=True)
    text(note, 322.58, y + 0.5, 1.0)

U10 = place(XCVR, "U10", 127.0, 165.1)
stub(U10, "VCC", power="+5V"); stub(U10, "TXD", "CAN_TX"); stub(U10, "RXD", "CAN_RX")
gnd_bus(U10, ["S", "GND"]); stub(U10, "VREF", nc=True); stub(U10, "CANH", "CAN_H"); stub(U10, "CANL", "CAN_L")
R1 = place(R, "R1", 175.26, 165.1, value="120R"); rstub(R1, "1", "CAN_H"); rstub(R1, "2", "CAN_L")
text("R1: termination at the hub end (Provisional)", 160.0, 180.0, 1.0)
text("U10 TJA1050 on +5V: RXD swings to 5 V into PB8 (FT, 5 V tolerant only while the STM32 is powered; no pull-up). S tied low (Provisional).", 95.0, 183.0, 1.0)

text("CAN bus: CAN_H and CAN_L daisy-chained U10 -> M1 ... M6 (and J3 when used), 120R at each end (R1, R2); every drive's own terminator off", 95.0, 186.0, 1.0)
text("(57D DIP 1, 42D shorting cap). Drives and adapter share GND with the hub (MKS manual p. 18). Drive blocks: bottom of the sheet.", 95.0, 189.4, 1.0)

J3 = place(CANAD, "J3", 127.0, 215.9)
stub(J3, "CANH", "CAN_H"); stub(J3, "CANL", "CAN_L"); stub(J3, "GND", power="GND")
text("J3: USB-CAN adapter for bring-up phase 7a. Its GND is connected (the Arctos drawing leaves it floating).", 104.0, 228.6, 1.0)

# drive blocks: (ref, axis, joint, role, model, CAN ID, motor, switch kind)
drives = [("M1", 0, "Joint X", "Base", "57D", "0x001", "NEMA 23, 2.8 A", "WSH231"),
          ("M2", 1, "Joint Y", "Shoulder", "57D", "0x002", "NEMA 23, 2.8 A", "KY003x2"),
          ("M3", 2, "Joint Z", "Elbow", "42D", "0x003", "NEMA 17, 2.1 A", "KY003x2"),
          ("M4", 3, "Wrist Joint 1", "Wrist 1", "42D", "0x004", "NEMA 17, 1.3 A", "WSH231"),
          ("M5", 4, "Wrist Joint 2", "Wrist 2", "42D", "0x005", "NEMA 17, 1.2 A", "KY003x2"),
          ("M6", 5, "Wrist Joint 3", "Wrist 3", "42D", "0x006", "NEMA 17, 1.2 A", "WSH231")]
text("Drive I/O, from the original Arctos wiring. Home and limit switch wiring and motor phase order are Provisional until confirmed on the bench (BRING_UP phase 1).", 20.32, 289.56, 1.2)
text("Phase A is crossed at every drive (drive A+ to motor A-), as in the Arctos drawing; it only sets the turning direction. Switch modules take 5 V from the drive's EVCC/EGND (20 mA budget).", 20.32, 293.0, 1.2)
sw_n = [0]
def sw_ref():
    sw_n[0] += 1; return f"SW{10 + sw_n[0]}"
for i, (ref, axis, joint, role, model, canid, motor, sw) in enumerate(drives):
    X0 = 20.32 + i * 91.44; n = f"AX{axis}_"
    text(f"Axis {axis}: {joint} ({role})", X0, 299.72, 1.2)
    text(f"CAN ID {canid}, SERVO{model}; motor {motor}", X0, 303.02, 1.0)
    text("Phase A crossed (Lenton recalls doing this on the 57D; confirm)" if model == "57D" else "Phase A crossed per the Arctos drawing (not confirmed)", X0, 309.62, 1.0)
    if model == "57D":
        text("Switches on IN_1 / IN_2. DIP 2, 3 ON: EVCC 5 V. DIP 1 (terminator) OFF.", X0, 306.32, 1.0)
    else:
        text("9EH port mapping on: left -> En, right -> Dir; COM to EVCC. IN_1 unused. Terminator cap off.", X0, 306.32, 1.0)
    m = place(DRV57 if model == "57D" else DRV42, ref, X0 + 20.32, 342.9)
    stub(m, "VIN+", power="VMOT_SW"); gnd_bus(m, ["VIN-", "GND"])
    stub(m, "CANH", "CAN_H"); stub(m, "CANL", "CAN_L")
    for pin in ("A+", "A-", "B+", "B-", "EVCC", "EGND"):
        stub(m, pin, n + pin)
    stub(m, "STP", nc=True)
    if model == "57D":
        for pin in ("COM", "EN", "DIR", "OUT_1", "OUT_2", "RS485_A", "RS485_B"): stub(m, pin, nc=True)
        stub(m, "IN_1", n + "IN_1"); stub(m, "IN_2", n + "IN_2")
        sig = (n + "IN_1", n + "IN_2")
    else:
        stub(m, "COM", n + "EVCC"); stub(m, "IN_1", nc=True)
        stub(m, "EN", n + "EN"); stub(m, "DIR", n + "DIR")
        sig = (n + "EN", n + "DIR")
    mot = place(STEP, f"MOT{axis + 1}", X0 + 71.12, 317.5, value=motor)
    # phase A crossed: motor A- on drive A+, motor A+ on drive A-
    stub(mot, "A-", n + "A+"); stub(mot, "A+", n + "A-"); stub(mot, "B+", n + "B+"); stub(mot, "B-", n + "B-")
    if sw == "WSH231":
        s = place(WSH231, sw_ref(), X0 + 71.12, 340.36, value="WSH231 (home)")
        stub(s, "VCC", n + "EVCC"); stub(s, "GND", n + "EGND"); stub(s, "N_OUT", sig[0]); stub(s, "S_OUT", sig[1])
    else:
        for k, (y, side) in enumerate(((337.82, "left"), (355.6, "right"))):
            s = place(KY003, sw_ref(), X0 + 71.12, y, value=f"KY-003 ({side} limit)")
            stub(s, "Vin", n + "EVCC"); stub(s, "GND", n + "EGND"); stub(s, "S", sig[k])
R2 = place(R, "R2", 276.86, 243.84, value="120R"); rstub(R2, "1", "CAN_H"); rstub(R2, "2", "CAN_L")
text("R2: far-end termination (Provisional)", 252.0, 256.0, 1.0)

PS1 = place(PSUM, "PS1", 33.02, 270.51)
SW2 = place(SPST, "SW2", 66.04, 269.24, value="Rocker switch (fitted)")
SW1 = place(EST, "SW1", 101.6, 270.51)
# real wires: PSU V+ -> rocker -> E-stop pole 1; PSU V- -> E-stop pole 2 (routed below the rocker)
x1, y1 = PS1.pin_pos(PS1.sym.pin_by_name("V+")); x2, y2 = SW2.pin_pos(SW2.sym.pin_by_name("1")); wire(x1, y1, x2, y2)
x1, y1 = SW2.pin_pos(SW2.sym.pin_by_name("2")); x2, y2 = SW1.pin_pos(SW1.sym.pin_by_name("IN1")); wire(x1, y1, x2, y2)
x1, y1 = PS1.pin_pos(PS1.sym.pin_by_name("V-")); x2, y2 = SW1.pin_pos(SW1.sym.pin_by_name("IN2"))
wire(x1, y1, x1 + MM, y1); wire(x1 + MM, y1, x1 + MM, y1 + 2 * MM); wire(x1 + MM, y1 + 2 * MM, x2 - MM, y1 + 2 * MM)
wire(x2 - MM, y1 + 2 * MM, x2 - MM, y2); wire(x2 - MM, y2, x2, y2)
stub(SW1, "OUT1", power="VMOT_SW"); stub(SW1, "OUT2", power="GND")
PS2 = place(PSUL, "PS2", 38.1, 177.8)
stub(PS2, "5V", power="+5V"); stub(PS2, "GND", power="GND")
# power flags for nets that ERC would otherwise report as undriven
for net, (fx, fy) in {"VMOT_SW": (139.7, 270.51)}.items():
    place(LIB["PWR_FLAG"], "#FLG", fx, fy); place(LIB[net], "#PWR", fx + 4 * MM, fy); named_points.append((net, fx + 4 * MM, fy))
    wire(fx, fy, fx + 4 * MM, fy); checks.append((fx, fy)); checks.append((fx + 4 * MM, fy))
text("PWR_FLAG: VMOT_SW is fed through the passive switches", 133.0, 278.0, 1.0)
text("Motor supply: PSU -> rocker switch (fitted) -> two-pole E-stop (to be fitted, in line after the rocker) -> VMOT_SW to every drive VIN+; drive VIN- to GND", 20.0, 258.0, 1.0)

# notes
notes = [
    ("Karetao bench wiring: STM32F405 hub, TCA9548A mux, AS5600 encoders, CAN to six MKS drives, SPI to the Raspberry Pi 5.", 1.6),
    ("Signals are connected by net labels of the same name. Power symbols: +3V3, +5V, GND, VMOT_SW (motor supply after the E-stop).", 1.2),
    ("Confirmed by the documents: STM32 pins (ARM_SENSOR_HUB.md), mux address 0x70 and axis N on channel N+2, encoder fitted per axis,", 1.2),
    ("drive models and CAN IDs 0x001 to 0x006 (SYSTEM_CONFIGURATION.md 2.1, 2.2), Pi header pins 19/21/23/24/22 (Pi README), 12 to 24 V drive supply (MKS manual).", 1.2),
    ("Provisional (not stated in any document): STM32 board type and its 5 V input; TJA1050 S pin tie; I2C pull-up values and location;", 1.2),
    ("mux RESET pull-up (no MCU line, FW-12); AS5600 DIR tied low; termination placement;", 1.2),
    ("motor supply voltage; the E-stop itself (SAFE-01, ruling R25b: to be fitted); drive switch and motor phase wiring (Arctos drawing, bench check).", 1.2),
    ("Decoupling on breakout boards is not drawn. Gripper parts (Nano, MCP2515, servo) are out of scope and not drawn (charter).", 1.2),
    ("Generated by Hardware/bench-wiring/generate_schematic.py; edit the script, not this file, then regenerate. Run ERC in KiCad after any change.", 1.2),
]
ty = 21.0
for s, sz in notes:
    text(s, 12.7, ty, sz); ty += 3.4

# ---------------------------------------------------------------- write files
def write(outdir):
    body = []
    body.append('(kicad_sch (version 20231120) (generator "karetao_generate_schematic") (generator_version "8.0")')
    body.append(f'  (uuid "{ROOT}")')
    body.append('  (paper "A2")')
    body.append('  (title_block (title "Karetao bench wiring") (date "2026-10-15") (rev "0.3") (company "Karetao")')
    body.append('    (comment 1 "System wiring at connector level; Provisional items noted on the sheet") (comment 2 "Source: Hardware/bench-wiring/generate_schematic.py"))')
    body.append('  (lib_symbols')
    for s in LIB.values(): body.append(s.sexp())
    body.append('  )')
    ends = {}
    for k, d in preview:
        if k == "wire":
            for pt in ((d[0], d[1]), (d[2], d[3])):
                key = (round(pt[0], 2), round(pt[1], 2)); ends[key] = ends.get(key, 0) + 1
    for (jx, jy), n in ends.items():
        if n >= 3: items.append(f'(junction (at {jx:.2f} {jy:.2f}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
    for it in items: body.append("  " + it.replace("\n", "\n  "))
    for i in insts: body.append("  " + i.emit().replace("\n", "\n  "))
    body.append(f'  (sheet_instances (path "/" (page "1")))')
    body.append(')')
    sch = "\n".join(body) + "\n"
    assert sch.count("(") == sch.count(")"), "unbalanced parentheses"
    open(os.path.join(outdir, "karetao_bench_wiring.kicad_sch"), "w").write(sch)
    pro = '{\n  "board": {"design_settings": {"defaults": {}}, "layer_presets": [], "viewports": []},\n  "boards": [],\n  "cvpcb": {"equivalence_files": []},\n  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},\n  "meta": {"filename": "karetao_bench_wiring.kicad_pro", "version": 1},\n  "net_settings": {"classes": [{"name": "Default", "wire_width": 6, "bus_width": 12, "clearance": 0.2, "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3}], "meta": {"version": 3}},\n  "pcbnew": {"page_layout_descr_file": ""},\n  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},\n  "sheets": [["' + ROOT + '", "Root"]],\n  "text_variables": {}\n}\n'
    open(os.path.join(outdir, "karetao_bench_wiring.kicad_pro"), "w").write(pro)
    lib = ['(kicad_symbol_lib (version 20231120) (generator "karetao_generate_schematic") (generator_version "8.0")']
    lib += [s.sexp(prefix="") for s in LIB.values()]
    lib.append(")")
    open(os.path.join(outdir, "karetao.kicad_sym"), "w").write("\n".join(lib) + "\n")
    open(os.path.join(outdir, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "karetao")(type "KiCad")(uri "${KIPRJMOD}/karetao.kicad_sym")(options "")(descr "Karetao bench wiring symbols (generated)"))\n)\n')
    # connectivity check: every label, no-connect and power pin must sit on a wire end
    missing = [c for c in checks if (round(c[0], 2), round(c[1], 2)) not in wire_ends]
    return sch, missing + net_conflicts()

def net_conflicts():
    """Union-find over wire segments, component pins and named points, as KiCad connects them."""
    R2 = lambda x, y: (round(x, 2), round(y, 2))
    segs = [d for k, d in preview if k == "wire"]
    pts = {}
    for i in insts:
        if isinstance(i.sym, PowerSym): continue
        for num in i.sym.pins:
            pts.setdefault(R2(*i.pin_pos(num)), []).append(f"{i.ref}.{i.sym.pins[num][0]}")
    for name, x, y in named_points:
        pts.setdefault(R2(x, y), []).append("NET:" + name)
    parent = {}
    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b): parent[find(a)] = find(b)
    def on_seg(p, s):
        (x, y), (x1, y1, x2, y2) = p, s
        return min(x1, x2) - 1e-6 <= x <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= y <= max(y1, y2) + 1e-6 and (abs(x1 - x2) < 1e-6 or abs(y1 - y2) < 1e-6)
    for s in segs:
        a, b = R2(s[0], s[1]), R2(s[2], s[3]); union(a, b)
        for p in list(pts) + [R2(o[0], o[1]) for o in segs] + [R2(o[2], o[3]) for o in segs]:
            if on_seg(p, s): union(p, a)
    groups = {}
    for p, members in pts.items():
        groups.setdefault(find(p), set()).update(m for m in members if m.startswith("NET:"))
    return [f"net conflict: {sorted(g)}" for g in groups.values() if len(g) > 1]

def render(path):
    from PIL import Image, ImageDraw, ImageFont
    S = 4.0; W, H = int(594 * S), int(420 * S)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10); small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
    except Exception: font = small = ImageFont.load_default()
    P = lambda x, y: (x * S, y * S)
    for kind, data in preview:
        if kind == "sym":
            i = data[0]; s = i.sym
            if isinstance(s, PowerSym):
                x, y = P(i.x, i.y)
                if s.name == "GND": d.line([x, y, x, y + 8], fill="red"); d.line([x - 5, y + 8, x + 5, y + 8], fill="red")
                else: d.line([x, y, x, y - 8], fill="red"); d.text((x - 10, y - 20), s.name, fill="red", font=small)
                continue
            if isinstance(s, RSym):
                x, y = P(i.x, i.y); d.rectangle([x - 4, y - 10, x + 4, y + 10], outline="black"); d.line([x, y - 15, x, y - 10], fill="black"); d.line([x, y + 10, x, y + 15], fill="black")
                d.text((x + 6, y - 6), f"{i.ref} {i.value}", fill="black", font=small); continue
            hw, hh = s.hw, s.hh
            x0, y0 = P(i.x - hw, i.y - hh); x1, y1 = P(i.x + hw, i.y + hh)
            d.rectangle([x0, y0, x1, y1], outline="black" if not i.dnp else "gray", width=1)
            d.text((x0, y0 - 12), f"{i.ref}  {i.value}", fill="black", font=font)
            for num, (pname, et, px, py, ang) in s.pins.items():
                cx, cy = i.pin_pos(num); bx = i.x + (px + MM if ang == 0 else px - MM)
                d.line([*P(cx, cy), *P(bx, cy)], fill="black")
                if ang == 0: d.text((P(bx, cy)[0] + 2, P(bx, cy)[1] - 5), pname, fill="black", font=small)
                else:
                    tw = d.textlength(pname, font=small); d.text((P(bx, cy)[0] - 2 - tw, P(bx, cy)[1] - 5), pname, fill="black", font=small)
        elif kind == "wire":
            x1, y1, x2, y2 = data; d.line([*P(x1, y1), *P(x2, y2)], fill="green", width=1)
        elif kind == "label":
            name, x, y, dirn = data; tx, ty = P(x, y)
            if dirn > 0: d.text((tx + 1, ty - 11), name, fill="blue", font=small)
            else: d.text((tx - 1 - d.textlength(name, font=small), ty - 11), name, fill="blue", font=small)
        elif kind == "nc":
            x, y = P(*data); d.line([x - 3, y - 3, x + 3, y + 3], fill="blue"); d.line([x - 3, y + 3, x + 3, y - 3], fill="blue")
        elif kind == "text":
            s_, x, y, sz = data; d.text((P(x, y)[0], P(x, y)[1] - 10), s_, fill="black", font=font if sz >= 1.2 else small)
    im.save(path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--preview"); ap.add_argument("--outdir", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    sch, missing = write(a.outdir)
    print(f"wrote {a.outdir}/karetao_bench_wiring.kicad_sch ({len(sch.splitlines())} lines, {len(insts)} symbols, {len(items)} items)")
    if missing: print("UNATTACHED POINTS:", missing); sys.exit(1)
    if a.preview: render(a.preview); print("preview:", a.preview)
