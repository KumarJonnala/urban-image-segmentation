"""Tree shadow casting: height estimation and geometric shadow projection."""

import math
import datetime as dt

import numpy as np
from pyproj import Transformer
from scipy.ndimage import label as cc_label

from src.shadow.solar import sun_position, _tile_center

_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)

_8CONN = np.ones((3, 3), dtype=int)


def _pixel_size_m(bbox: dict, shape: tuple[int, int]) -> float:
    """Return average metres-per-pixel for a tile."""
    H, W = shape
    west_m, south_m = _to_utm.transform(bbox["west"], bbox["south"])
    east_m, north_m = _to_utm.transform(bbox["east"], bbox["north"])
    return ((east_m - west_m) / W + (north_m - south_m) / H) / 2.0


def _shift_mask(mask: np.ndarray, dr: int, dc: int) -> np.ndarray:
    """Translate a boolean mask by (dr rows, dc cols), clipping at image edges."""
    H, W = mask.shape
    out = np.zeros_like(mask)
    src_r0 = max(0, -dr);  src_r1 = H - max(0, dr)
    dst_r0 = max(0,  dr);  dst_r1 = H + min(0, dr)
    src_c0 = max(0, -dc);  src_c1 = W - max(0, dc)
    dst_c0 = max(0,  dc);  dst_c1 = W + min(0, dc)
    if dst_r1 > dst_r0 and dst_c1 > dst_c0:
        out[dst_r0:dst_r1, dst_c0:dst_c1] = mask[src_r0:src_r1, src_c0:src_c1]
    return out


def estimate_tree_heights(
    tree_mask: np.ndarray,
    pixel_size_m: float,
    min_component_pixels: int = 50,
) -> tuple[np.ndarray, dict[int, float]]:
    """Estimate per-tree-cluster height from canopy area using an allometric formula.

    For each connected component of the tree mask:
        crown_area_m² = n_pixels × pixel_size_m²
        crown_radius_m = sqrt(area / π)
        tree_height_m  = crown_diameter × 0.7   (allometric: Hn ≈ 0.7 × 2r)

    Parameters
    ----------
    tree_mask : np.ndarray
        Bool (H, W) — True where pixels are classified as trees (class 1).
    pixel_size_m : float
        Metres per pixel (derived from tile bbox and image dimensions).
    min_component_pixels : int
        Components smaller than this are skipped (noise).

    Returns
    -------
    labeled : np.ndarray
        Integer (H, W) array of component labels (same as scipy.ndimage.label output).
    heights : dict[int, float]
        Mapping of label → estimated tree_height_m. Labels not present were
        below min_component_pixels.
    """
    labeled, n = cc_label(tree_mask, structure=_8CONN)
    heights: dict[int, float] = {}
    px_area = pixel_size_m ** 2

    for k in range(1, n + 1):
        n_pixels = int((labeled == k).sum())
        if n_pixels < min_component_pixels:
            continue
        crown_area_m2 = n_pixels * px_area
        crown_radius_m = math.sqrt(crown_area_m2 / math.pi)
        tree_height_m = 2.0 * crown_radius_m * 0.7
        heights[k] = tree_height_m

    return labeled, heights


def cast_tree_shadows(
    seg_map: np.ndarray,
    bbox: dict,
    dt_utc: dt.datetime,
    min_elevation_deg: float = 5.0,
    max_shadow_factor: float = 5.0,
    min_component_pixels: int = 50,
) -> np.ndarray:
    """Compute where tree canopies cast shadows given a sun position.

    Parameters
    ----------
    seg_map : np.ndarray
        uint8 (H, W) segmentation map: 0=other, 1=tree, 2=road, 3=building.
    bbox : dict
        WGS84 tile bounding box {west, east, south, north} — same dict as
        returned by tiles_for_area().
    dt_utc : datetime.datetime
        Timezone-aware UTC datetime for solar position calculation.
    min_elevation_deg : float
        Sun elevation floor. Below this (incl. nighttime), returns an all-False mask.
    max_shadow_factor : float
        Cap shadow length at this multiple of crown radius to avoid extreme
        shadows at very low sun angles.
    min_component_pixels : int
        Tree clusters smaller than this many pixels are ignored.

    Returns
    -------
    np.ndarray
        Bool (H, W) — True where a tree shadow falls. Source tree pixels are
        excluded (the tree itself is still green in the overlay).
    """
    H, W = seg_map.shape
    pixel_size_m = _pixel_size_m(bbox, (H, W))

    lat, lon = _tile_center(bbox)
    azimuth_deg, elevation_deg = sun_position(lat, lon, dt_utc)

    if elevation_deg < min_elevation_deg:
        return np.zeros((H, W), dtype=bool)

    elevation_rad = math.radians(elevation_deg)
    shadow_az_rad = math.radians((azimuth_deg + 180.0) % 360.0)

    labeled, heights = estimate_tree_heights(
        seg_map == 1, pixel_size_m, min_component_pixels
    )

    shadow_mask = np.zeros((H, W), dtype=bool)

    for k, tree_height_m in heights.items():
        crown_radius_m = tree_height_m / 1.4  # inverse of allometric (diameter×0.7)
        shadow_length_m = min(
            tree_height_m / math.tan(elevation_rad),
            max_shadow_factor * crown_radius_m,
        )
        # Image convention: row 0 is north (top), col 0 is west (left)
        dx_px = shadow_length_m * math.sin(shadow_az_rad) / pixel_size_m
        dy_px = -shadow_length_m * math.cos(shadow_az_rad) / pixel_size_m

        comp_mask = labeled == k
        shifted = _shift_mask(comp_mask, int(round(dy_px)), int(round(dx_px)))
        shadow_mask |= shifted

    # Source tree pixels are not shadow — they stay green in the overlay
    shadow_mask &= ~(seg_map == 1)
    return shadow_mask
