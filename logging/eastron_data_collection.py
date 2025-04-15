#!/usr/bin/env python3

import serial
import minimalmodbus
from utils import pretty_print_dict, exit_failure
import time
from datetime import datetime
import sys

database_name = "eastron_data"
data_def = ["frequency", "energy_keller", "power_keller", "energy_erdgeschoss", "power_erdgeschoss", "energy_obergeschoss", "power_obergeschoss", "power_total_max"]

def get_measurements(addresses=[0,1,2], debug=False):
  port = None
  try:
    port = serial.Serial(port="/dev/ttySC0", baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=2)
  except:
    print("Couln't open serial port...")
  # port.open() # Opens on creation and closes automatically when script ends
  devices = []
  devices.append(minimalmodbus.Instrument(port=port, slaveaddress=1, mode=minimalmodbus.MODE_RTU, debug=debug))
  devices.append(minimalmodbus.Instrument(port=port, slaveaddress=2, mode=minimalmodbus.MODE_RTU, debug=debug))
  devices.append(minimalmodbus.Instrument(port=port, slaveaddress=3, mode=minimalmodbus.MODE_RTU, debug=debug))

  # dict that holds data
  data = {k: 0 for k in data_def}
  for i, device in enumerate(devices):
    if debug:
      print(device)
  if debug:
    print("Connected to all Eastron SDM72D-M Submeters")
  try:
    data["frequency"] = float(devices[0].read_float(registeraddress=70, functioncode=4)) # frequency
    data["energy_keller"] = int(devices[0].read_float(registeraddress=342, functioncode=4) * 1000) # total_energy_active
    data["power_keller"] = float(devices[0].read_float(registeraddress=52, functioncode=4)) # total_power
    data["energy_erdgeschoss"] = int(devices[1].read_float(registeraddress=342, functioncode=4) * 1000) # total_energy_active
    data["power_erdgeschoss"] = float(devices[1].read_float(registeraddress=52, functioncode=4)) # total_power
    data["energy_obergeschoss"] = int(devices[2].read_float(registeraddress=342, functioncode=4) * 1000) # total_energy_active
    data["power_obergeschoss"] = float(devices[2].read_float(registeraddress=52, functioncode=4)) # total_power
    data["power_total_max"] = data["power_keller"] + data["power_erdgeschoss"] + data["power_obergeschoss"]
  except:
    data = None
  try:
    port.close()
  except:
    print("Couldn't close port...")
  return data
  # print("Data: ", frequency, power, energy)

if __name__=="__main__":
  print("Submeter data: ")
  start = time.time()
  pretty_print_dict(get_measurements(debug=False))
  print(f'Taken: {(time.time() - start)*1000:.2f}ms')