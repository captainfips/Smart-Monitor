def pretty_print_dict(dict):
  if dict:
    for k, v in dict.items():
      print("  --" + str(k) + ": " + str(v))

def exit_failure(stufftoclose, message="None"):
  for element in stufftoclose:
    element.close()
  print(message)
  exit()