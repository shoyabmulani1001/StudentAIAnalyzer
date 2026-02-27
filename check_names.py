import sys
sys.path.append('backend')
import excel_reader

records = excel_reader.read_all_files()
names = set()
duplicates = set()
for r in records:
    name = r["name"]
    # Check if there's a highly similar name
    for existing in names:
        if existing != name and existing.replace(" ", "") == name.replace(" ", ""):
            duplicates.add((existing, name))
    names.add(name)

print("Duplicates or similar names found:")
for d in duplicates:
    print(d)

names_list = sorted(list(names))
print(f"Total unique names: {len(names_list)}")
