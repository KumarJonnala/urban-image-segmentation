# Urban Shadow Analysis, Magdeburg

Urban satellite image segmentation and shadow modelling for shaded routing

---

## Phases

1. **Satellite imagery acquisition** — DOP20 orthophotos (Sachsen-Anhalt WMS)
2. **Urban segmentation** — Multi-class: buildings, roads, trees (VARI/DeepForest/SegFormer-B5/DeepLab)
3. **Shadow modelling** — Tree shadows via sun position + height estimation

---

## Usage

**Download orthophotos and segment:**
```bash
python pipeline.py all --vegetation-model vari
```

**Cast tree shadows for a specific datetime:**
```bash
python pipeline.py shadow --datetime-utc "2026-05-21T11:00:00" --area ovgu_bbox
```

**See all options:**
```bash
python pipeline.py --help
```

Interactive exploration: open `test_notebooks/shadow_analysis.ipynb` in Jupyter.

---

## Project structure

```
urban-shadow-analysis/
├── test_notebooks/         # exploratory Jupyter notebooks
├── src/
│   ├── config.py           # geographic areas, WMS settings
│   ├── data_preprocessing/ # orthophoto fetching + tiling
│   ├── segmentation/       # multi-class segmentation (OSM, vegetation models)
│   └── shadow/             # shadow modelling
├── data/                   # orthophotos, segmentations, shadows
├── pipeline.py             # CLI: download / segment / shadow / compare / all
├── requirements.txt
└── README.md
```

---

## Reference

> Lindberg, F. et al. — *Modelling sunlight and shading distribution on 3D Trees and Buildings*

---