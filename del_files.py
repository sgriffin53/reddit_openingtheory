import main
import os

filenames = main.get_filenames()
i = 0
total_deleted = 0
for filename in filenames:
    text = main.get_text(filename)
    is_valid = False
    count = 0
    for line in text.split("\n"):
        if "Moves:" in line: continue
        if len(line) < 1: continue
        if "parent:" in line.lower(): continue
        if "eco code:" in line.lower(): continue
        if "notation" in line.lower(): continue
       # if "moves:" in line.lower(): continue
        if "**" in line.lower(): continue
        if "wikipedia" in line.lower(): continue
        if line.split(" ")[0].replace(".","").isnumeric() and line.split(" ")[0][-1] != "." and "." in line.split(" ")[0]: continue
        count += len(line)
        is_valid = True
    if count == 0: is_valid = False
    if not is_valid:
        i += 1
        print(filename, count)
        print(text)
        os.system("del " + filename)
        print("deleted", i)