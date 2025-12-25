import json
import os

benchmarks_dir = "/Users/velocityworks/IdeaProjects/z5d-prime-predictor/benchmarks"
summary = []

for exp in range(4, 12):
    filename = f"{benchmarks_dir}/band_10_{exp}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            summary.append(data)

with open(f"{benchmarks_dir}/summary_bands.json", "w") as f:
    json.dump(summary, f, indent=2)

print("Summary JSON created.")
