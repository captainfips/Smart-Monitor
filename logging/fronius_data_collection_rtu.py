#!/usr/bin/env python3

import serial
import struct
import minimalmodbus

import sys
from datetime import datetime
from utils import *
import time
import math

database_name = "fronius_data"
data_def = ["energy_day", "energy_year", "energy_total", "ac_power", "ac_frequency", "dc_power", "dc1_power", "dc1_current", "dc1_voltage", "dc2_power", "dc2_current", "dc2_voltage"]

def get_measurements(debug = False):
  try:
    data = {}
    port = None
    try:
      port = serial.Serial(port="/dev/ttySC1", baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=2)
    except:
      print("Couln't open serial port...")
    # port.open() # Opens on creation and closes automatically when script ends
    fronius = minimalmodbus.Instrument(port=port, slaveaddress=1, mode=minimalmodbus.MODE_RTU, debug=debug)
    temp = fronius.read_registers(registeraddress=499, functioncode=3, number_of_registers=14)
    temp_packed = struct.pack('>' + 'H' * len(temp), *temp)
    values = struct.unpack('>IQQQ', temp_packed) # I = uint32, Q = uint64
    if debug:
      print(temp_packed)
      print(values)
    data["ac_power"] = values[0]
    data["energy_day"] = values[1]
    data["energy_year"] = values[2]
    data["energy_total"] = values[3]
    temp = fronius.read_registers(registeraddress=40265, functioncode=3, number_of_registers=42)
    temp_packed = struct.pack('>' + 'H' * len(temp), *temp)
    values = struct.unpack('>hhhxx' + 'x'*26 + 'HHHxxxx' + 'x'*30 + 'HHHxxxx', temp_packed) # h = int16, H = uint16, x = unused 8bit
    if debug:
      print(temp_packed)
      print(values)
    data["dc1_current"] = values[3] * 10**values[0]
    data["dc1_voltage"] = values[4] * 10**values[1]
    data["dc1_power"]   = values[5] * 10**values[2]
    data["dc2_current"] = values[6] * 10**values[0]
    data["dc2_voltage"] = values[7] * 10**values[1]
    data["dc2_power"]   = values[8] * 10**values[2]
    data["dc_power"]    = data["dc1_power"] + data["dc2_power"]
    data["ac_frequency"] = 50 # Pad for db

    if (data["ac_power"] == 0 or data["dc_power"] == 0) or any([math.isnan(data[key]) for key in data_def]):
      # print(f'{datetime.now()} >> Error with these values: {data}', file=sys.stderr)
      # print(status_bits, file=sys.stderr)
      if debug:
        pretty_print_dict(data)
        print("Returning None, is it night?")
      data = None
      pass
  except:
    print(f"{datetime.now()} >> Error when reading fronius data, returning None")
    data = None
  return data

if __name__ == "__main__":
  print("Fronius Data:")
  start = time.time()
  pretty_print_dict(get_measurements(debug=True))
  print(f'Taken: {(time.time() - start)*1000:.2f}ms')