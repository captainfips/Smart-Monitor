#!/usr/bin/python3

import serial
import time
import binascii
import sys
import string
from datetime import datetime
from Cryptodome.Cipher import AES
from utils import pretty_print_dict, exit_failure

database_name = "iskra_data"
data_def = ["energy_in", "energy_out", "power_in", "power_out"]

def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + b
    return result

# Got to find the source of this again, somewhere on stackoverflow...
CRC_INIT=0xffff
POLYNOMIAL=0x1021
def byte_mirror(c):
    c=(c&0xF0)>>4|(c&0x0F)<<4
    c=(c&0xCC)>>2|(c&0x33)<<2
    c=(c&0xAA)>>1|(c&0x55)<<1
    return c

def calc_crc16(data):
  crc=CRC_INIT
  for i in range(len(data)):
    c=byte_mirror(data[i])<<8
    for j in range(8):
      if (crc^c)&0x8000: crc=(crc<<1)^POLYNOMIAL
      else: crc=crc<<1
      crc=crc%65536
      c=(c<<1)%65536
  crc=0xFFFF-crc
  return 256*byte_mirror(crc//256)+byte_mirror(crc%256)

def verify_crc16(input, skip=0, last=2, cut=0):
  lenn=len(input)
  data=input[skip:lenn-last-cut]
  goal=input[lenn-last-cut:lenn-cut]
  if   last == 0: return hex(calc_crc16(data))
  elif last == 2: return calc_crc16(data)==goal[0]*256 + goal[1]
  return False

# Key from Grid/Meter Operator
def get_measurements(key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", debug = True, last_measurements = None):
  # Comport Config/Init
  ser = serial.Serial( 
    port="/dev/ttyAMA0",
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    timeout=0.025,
  )
  max_retries = 200

  number_of_bytes=103

  # dict that holds data
  data={k: 0 for k in data_def}

  try:
    if not ser.is_open:
      ser.open()
    i = 0
    while i < max_retries: # Wait for starting bytes
      first = ser.read().hex()
      if first == "7e":
        second = ser.read().hex()
        if second == "a0":
          break
      i = i + 1
    if i == max_retries:
      ser.close()
      #if debug:
      print(f'{datetime.now()} >> No Data received from Iskra Smartmeter in {max_retries} tries.', file=sys.stderr)
      return None
      # exit_failure([ser], f"Beginning Text not received within {i} tries!")
    # Found starting text!
    ser.timeout = 0.5
    raw_data = bytearray(ser.read(size=number_of_bytes)) # if valid beginning found read rest
    ser.close()
    raw_data[0:0] = bytearray(b'\x7e\xa0')
    if debug:
      print(f"Beginning Text after {i} tries!")
      print(raw_data.hex())
    decoded = 0
    if verify_crc16(raw_data, 1, 2, 1):
      nonce=bytes(raw_data[14:22]+raw_data[24:28]) # systemTitle+invocation counter
      cipher=AES.new(binascii.unhexlify(key), AES.MODE_CTR, nonce=nonce, initial_value=2)
      decoded = cipher.decrypt(raw_data[28:-3])
    else:
      print(f'{datetime.now()} >> Iskra CRC not correct...', file=sys.stderr)
      return None
      # exit_failure([ser], "CRC not correct")
    
    data["energy_in"]=bytes_to_int(decoded[35:39])    #+A Wh
    data["energy_out"]=bytes_to_int(decoded[40:44])   #-A Wh
    data["power_in"]=bytes_to_int(decoded[55:59])     #+P W
    data["power_out"]=bytes_to_int(decoded[60:64])    #-P W

    # c=bytes_to_int(decoded[45:49])/1000.000  #+R varh
    # d=bytes_to_int(decoded[50:54])/1000.000  #-R varh
    # g=bytes_to_int(decoded[65:69])           #+Q var
    # h=bytes_to_int(decoded[70:74])           #-Q var
    # yyyy=bytes_to_int(decoded[22:24])
    # mm=bytes_to_int(decoded[24:25])
    # dd=bytes_to_int(decoded[25:26])
    # hh=bytes_to_int(decoded[27:28])
    # mi=bytes_to_int(decoded[28:29])
    # ss=bytes_to_int(decoded[29:30])
    # print ("Output: %10.3fkWh, %10.3fkWh, %10.3fkvarh, %10.3fkvarh, %5dW, %5dW, %5dvar, %5dvar at %02d.%02d.%04d-%02d:%02d:%02d" %(a,b,c,d,e,f,g,h, dd,mm,yyyy,hh,mi,ss))
    
    return data
  except BaseException as err:
    print(f"{datetime.now()} >> Script failed: {format(err)}")
    return None

if __name__ == "__main__":
  print("Smartmeter Values: ")
  for i in range(100):
    pretty_print_dict(get_measurements(debug=True))
    time.sleep(1)
