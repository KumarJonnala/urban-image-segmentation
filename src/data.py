from pathlib import Path
import requests
from pyproj import Transformer

from config import AREAS


WMS_URL = "https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest"
WMS_LAYER = "lsa_lvermgeo_dop20_2"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "orthophotos"

_transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)


def get_bbox(name: str) -> dict:
    if name not in AREAS:
        raise KeyError(f"Unknown area '{name}'. Available: {list(AREAS.keys())}")
    return AREAS[name]


def get_all_bboxes() -> dict:
    return AREAS


def fetch_and_save(bbox: dict, filename: str, output_dir: Path = OUTPUT_DIR, width: int = 1200, height: int = 1200) -> Path:
    min_x, min_y = _transformer.transform(bbox["west"], bbox["south"])
    max_x, max_y = _transformer.transform(bbox["east"], bbox["north"])
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": WMS_LAYER,
        "STYLES": "",
        "CRS": "EPSG:25832",
        "BBOX": f"{min_x},{min_y},{max_x},{max_y}",
        "WIDTH": width,
        "HEIGHT": height,
        "FORMAT": "image/png",
        "TRANSPARENT": "false",
    }
    print(f"Fetching {filename} ...")
    r = requests.get(WMS_URL, params=params, timeout=60)
    r.raise_for_status()
    out_path = output_dir / filename
    out_path.write_bytes(r.content)
    print(f"  Saved {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
    return out_path


def fetch_all(output_dir: Path = OUTPUT_DIR, width: int = 1200, height: int = 1200) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        fetch_and_save(bbox, f"dop20_{name}.png", output_dir, width, height)
        for name, bbox in AREAS.items()
    ]


if __name__ == "__main__":
    print(f"Fetching {len(AREAS)} areas -> {OUTPUT_DIR}\n")
    paths = fetch_all()
    print(f"\nDone. {len(paths)} image(s) saved.")