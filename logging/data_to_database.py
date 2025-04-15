#!/usr/bin/env python3

import iskra_data_collection as iskra
import fronius_data_collection_rtu as fronius
import eastron_data_collection as eastron
import example_data_collection as example
import psycopg2
import sys
from datetime import datetime
import pytz
import time
import threading

sensors = [example] # [iskra, eastron, fronius]
# data = {sensor.database_name: {key: 0 for key in sensor.data_def} for sensor in sensors}
# num_measurements_from_sensor = {sensor.database_name: 0 for sensor in sensors}
debug = True

num_measurements = 1
seconds_per_measurement = 3

# global variables for every thread
start = time.time()
threadlock = threading.Lock()
insert_query = ""

timezone = pytz.timezone('Europe/Vienna')

def get_measurements(sensor):
  num_measurements_from_sensor = 0
  
  data = {key: 0 for key in sensor.data_def}
  for i in range(num_measurements):
    try:
      temp = sensor.get_measurements()
      if temp:
        num_measurements_from_sensor += 1
        for measurement in sensor.data_def:
          if 'max' in measurement: # total max power of 30s
            data[measurement] = max(data[measurement], temp[measurement]) 
          elif 'power' in measurement: # sum up for average
            data[measurement] += temp[measurement] # accumulate power
          else: # newest value
            data[measurement] = temp[measurement] # newest value for everything than power
    except BaseException as err:
      print(f"{timezone.localize(datetime.now())} >> Error with get_measurements #{i+1} of {sensor.database_name}:\n{format(err)}\n", file=sys.stderr)
      # data = None
      pass
    finally:
      global start # Get global scope for the thread of this sensor
      sleep_duration = seconds_per_measurement*(i+1)-(time.time()-start)
      if i < num_measurements - 1:
        if debug:
          print(f'Sleep {i} duration: {sleep_duration}')
        # if sleep_duration < 0:
        #   print(f'{timezone.localize(datetime.now())} >> Error, sleep of thread_{sensor.database_name} under 0 seconds: {sleep_duration}', file=sys.stderr)
        time.sleep(max(sleep_duration, 0))
      # else: # No Sleep after last measurement, but has it laken longer?
      if sleep_duration < 0:
        print(f'{timezone.localize(datetime.now())} >> Error, sleep of thread_{sensor.database_name} under 0 seconds: {sleep_duration}', file=sys.stderr)
  
  if num_measurements_from_sensor == 0:
    data = None
    print(f'{timezone.localize(datetime.now())} >> Error, not a single measurement from thread_{sensor.database_name}.')
  else:
    for measurement in sensor.data_def:
      if 'max' in measurement:
        pass
      elif 'power' in measurement:
        data[measurement] /= num_measurements_from_sensor
      elif 'energy' in measurement and data[measurement] == 0: # Invalid then
        data = None
        break
  
  if data: # When data is valid
    # print(data)
    global threadlock
    try:
      if threadlock.acquire(blocking=True) == True:
        global insert_query
        insert_query += f"INSERT INTO {sensor.database_name} (time"
        for entry in data:
          insert_query += f', {entry}'
        insert_query += ") values (date_bin('10s',now()-interval'5s',date_trunc('minute', now()))"
        for entry in data:
          insert_query += f', {data[entry]}'
        insert_query += ");\n"
      else:
        print("Unable to acquire threadlock, no data written to insert_query")
    finally:
      if threadlock.locked():
        threadlock.release()

threads = list()

for sensor in sensors:
  x = threading.Thread(target=get_measurements, args=(sensor,), name=f'thread_{sensor.database_name}')
  threads.append(x)
  x.start()

for i, t in enumerate(threads):
  t.join()
  print(f"Thread {t.name} finished...")


print(insert_query)
CONNECTION = "postgres://postgres:postgres@database/smart_monitor"
conn = psycopg2.connect(CONNECTION)
cursor = conn.cursor()
cursor.execute(insert_query)
conn.commit()
cursor.close()
conn.close()

print("Written to database, exiting")
exit()
