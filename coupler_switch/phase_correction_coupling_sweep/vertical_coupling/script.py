from pathlib import Path
import re

folder = Path(
    "./coupler_switch/phase_correction_coupling_sweep/vertical_coupling"
)

pattern = re.compile(
    r"pullaway_(TE|TM)_W(\d+)nm_H(\d+)nm_g(\d+)nm\.csv"
)

for file in folder.glob("*.csv"):

    match = pattern.match(file.name)

    if not match:
        continue

    pol = match.group(1)
    W = match.group(2)
    H = match.group(3)
    g = match.group(4)

    new_name = (
        f"pullaway_{pol}_"
        f"Wbus{W}nm_"
        f"Hbus{H}nm_"
        f"Wcpl{W}nm_"
        f"Hcpl{H}nm_"
        f"g{g}nm.csv"
    )

    new_path = file.with_name(new_name)

    print(f"{file.name}  -->  {new_name}")

    file.rename(new_path)

print("Done.")