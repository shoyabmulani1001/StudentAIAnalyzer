import sys
sys.path.append('backend')
import excel_reader

records = excel_reader.read_all_files()
names_list = sorted(list(set(r['name'] for r in records)))
with open("names_list.txt", "w") as f:
    for n in names_list:
        f.write(n + "\n")

print("Wrote names to names_list.txt")
