# build_polygon.py
from pathlib import Path
from src.polygon_tools import read_checkpoints, build_polygon_from_checkpoints, save_polygon

checkpoints = read_checkpoints(Path("data/north_checkpoints.txt"))
coords = build_polygon_from_checkpoints(checkpoints)
save_polygon(coords)  # crée data/north_polygon.json
