#!/usr/bin/env python3

from utils import pretty_print_dict, exit_failure
import time
import random
from datetime import datetime
import sys




database_name = "example_data"
data_def = ["frequency", "power_example", "energy_example"]

def get_measurements(debug=False):

  # dict that holds data
  data = {k: 0 for k in data_def}
  data["frequency"] = random.uniform(49.5, 50.5) # frequency
  data["power_example"] = random.uniform(0,450)
  data["energy_example"] = random.randrange(500, 40500)
  return data
  # print("Data: ", frequency, power, energy)

if __name__=="__main__":
  print("Submeter data: ")
  start = time.time()
  pretty_print_dict(get_measurements(debug=False))
  print(f'Taken: {(time.time() - start)*1000:.2f}ms')