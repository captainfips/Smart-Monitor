#!/usr/bin/env python3

from pyModbusTCP import utils
from pyModbusTCP.client import ModbusClient
import sys
from datetime import datetime
import time
import math
from utils import pretty_print_dict, exit_failure

database_name = "fronius_data"
data_def = ["energy_day", "energy_year", "energy_total", "ac_power", "ac_frequency", "dc_power", "dc1_power", "dc1_current", "dc1_voltage", "dc2_power", "dc2_current", "dc2_voltage"]

def decode(dtype, values):
  if dtype == "float32":
    data = utils.word_list_to_long(values)
    data = utils.decode_ieee(data[0])
    return data
  elif dtype == "uint16":
    return values[0]
  elif dtype == "uint32":
    return utils.word_list_to_long(values, long_long=False)[0]
  elif dtype == "uint64":
    return utils.word_list_to_long(values, long_long=True)[0]
  elif dtype == "bitfield16":
    return [(values[0] & 8) >> 3, (values[0] & 4) >> 2, (values[0] & 2) >> 1, values[0] & 1]
  elif dtype == "scale" or dtype == "int16":
    return utils.twos_c(values[0])
  return

def get_measurements(ip="192.168.1.162", last_measurements = None):
  if last_measurements:
    print("FRONIUS:")
    print(last_measurements)
  try:
    fronius = ModbusClient(host=ip, port=502, auto_open=False, auto_close=False, debug=False)
    
    # print(ip + ": Client created successfully.")
    data = {}
    if fronius.open():
      raw_data = fronius.read_holding_registers(499, 14) # Cumulative data
      # total_cumulative_power, raw_data = temp[0:2], temp[2:]
      # print(total_cumulative_power)
      temp = fronius.read_holding_registers(40091, 18)
      raw_data += temp[0:4] # fronius.read_holding_registers(40091, 4) # AC Power, AC Freq
      raw_data += temp[16:] # fronius.read_holding_registers(40107, 2) # DC Power (correct sum!)

      temp = fronius.read_holding_registers(40193, 112)
      raw_data += temp[0:1] # fronius.read_holding_registers(40193, 1) # Status bits
      raw_data += temp[72:75] # fronius.read_holding_registers(40265, 3) # Scale Factors and String raw_data
      raw_data += temp[89:92] # fronius.read_holding_registers(40282, 3) # Scale Factors and String raw_data
      raw_data += temp[109:112] # fronius.read_holding_registers(40302, 3) # Scale Factors and String raw_data
      fronius.close()

      
      # energy_day = decode("uint64", raw_data[2:6])
      # energy_year = decode("uint64", raw_data[6:10])
      # energy_total = decode("uint64", raw_data[10:14])
      # ac_power = decode("float32", raw_data[14:16])
      # ac_frequency = decode("float32", raw_data[16:18])
      # dc_power = decode("float32", raw_data[18:20])
      
      # # print(status_bits)
      # scale_factors = utils.twos_c_l(raw_data[21:24])
      # # print(raw_data)
      # # print(status_bits)
      # # print(scale_factors)
      
      # # ac_power = decode("float32", raw_data[14:16])
      # # ac_frequency = decode("float32", raw_data[16:18])
      # # dc_power = decode("float32", raw_data[30:32])
      # # print(ac_freq) 
      # # print(ac_power)
      # # print(dc_power)
      # dc1_current = decode("uint16", raw_data[24:25]) * 10**scale_factors[0]# 65=31 -> 82=48
      # dc1_voltage = decode("uint16", raw_data[25:26]) * 10**scale_factors[1]
      # dc1_power = decode("uint16", raw_data[26:27]) * 10**scale_factors[2]
      # # # print(dc1_current)
      # # # print(dc1_voltage)
      # # # print(dc1_power)
      # dc2_current = decode("uint16", raw_data[27:28]) * 10**scale_factors[0]# 65=31 -> 102=68
      # dc2_voltage = decode("uint16", raw_data[28:29]) * 10**scale_factors[1]
      # dc2_power = decode("uint16", raw_data[29:30]) * 10**scale_factors[2]
      # print(dc2_current)
      # print(dc2_voltage)
      # print(dc2_power)
      # if ac_power == 0:
      #   dc1_current = dc1_voltage = dc1_power = dc2_current = dc2_voltage = dc2_power = 0.

      cumulative_power = decode("uint32", raw_data[0:2])
      data["energy_day"] = decode("uint64", raw_data[2:6])
      data["energy_year"] = decode("uint64", raw_data[6:10])
      data["energy_total"] = decode("uint64", raw_data[10:14])
      data["ac_power"] = decode("float32", raw_data[14:16])
      data["ac_frequency"] = decode("float32", raw_data[16:18])
      data["dc_power"] = decode("float32", raw_data[18:20])

      scale_factors = utils.twos_c_l(raw_data[21:24])
      data["dc1_current"] = decode("uint16", raw_data[24:25]) * 10**scale_factors[0]
      data["dc1_voltage"] = decode("uint16", raw_data[25:26]) * 10**scale_factors[1]
      data["dc1_power"] = decode("uint16", raw_data[26:27]) * 10**scale_factors[2]
      data["dc2_current"] = decode("uint16", raw_data[27:28]) * 10**scale_factors[0]
      data["dc2_voltage"] = decode("uint16", raw_data[28:29]) * 10**scale_factors[1]
      data["dc2_power"] = decode("uint16", raw_data[29:30]) * 10**scale_factors[2]

      status_bits = decode("bitfield16", raw_data[20:21])

      if (not 1 in status_bits or cumulative_power == 0) or any([math.isnan(data[key]) for key in data_def]):
        # print(f'{datetime.now()} >> {data}', file=sys.stderr)
        # print(status_bits, file=sys.stderr)
        data = None
    else:
      print("Couldn't open connection to Fronius", file=sys.stderr)
  except:
    print("Error when reading modbus data, returning None", file = sys.stderr)
    data = None
  return data

if __name__ == "__main__":
  print("Fronius Data:")
  start = time.time()
  pretty_print_dict(get_measurements("192.168.1.162"))
  print(f'Taken: {(time.time() - start)*1000:.2f}ms')