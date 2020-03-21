import sys
import json
from pathlib import Path

try:
  input_file = Path(sys.argv[1])
except IndexError:
  print("[ERR] Please put the path to the txt file as a first argument")

input_file_contents = input_file.read_text("utf-8")

lines = input_file_contents.split("\n")

output = {"meta": {"total_length": 0, "total_offset": 0}}
output["lines"] = []

for l in lines:
  segments_list = l.split(";")
  time = segments_list.pop(0)
  segments_per_line = []
  for idx, s in enumerate(segments_list):
    segments_per_line.append({"text": s, "keys": []})
    segments_per_line[idx]["keys"].append({"offset": time, "value": 1})

  output["lines"].append({"segments": segments_per_line})


print(json.dumps(output, indent=2))

