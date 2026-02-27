import sys
sys.path.append('backend')
import excel_reader

records = excel_reader.read_all_files()
names_dict = {}
for r in records:
    name = r["name"]
    normalized_name = " ".join(name.split())
    
    if normalized_name not in names_dict:
        names_dict[normalized_name] = r
    
sorted_names = sorted(names_dict.keys())

# Print all names to see if Phad Ajaykumar etc. appear earlier
for i, name in enumerate(sorted_names):
    if "PHAD" in name or "YELMATE" in name or "PARDESHI" in name:
        print(f"{i}: {name}")
