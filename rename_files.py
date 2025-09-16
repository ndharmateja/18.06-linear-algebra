import os
import re

# Rename all PDFs in the current directory
for filename in os.listdir("."):
    if filename.endswith(".pdf") and "Ses" in filename:
        # Keep only the part starting with Ses
        new_name = re.sub(r".*?(Ses\d+\.\d+(sum|prob)\.pdf)", r"\1", filename)
        if new_name != filename:
            os.rename(filename, new_name)
            print(f"Renamed: {filename} -> {new_name}")

print("✅ Renaming complete.")
