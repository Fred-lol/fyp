"""Learned ridge-regression strategy ranking; JSON artifacts never execute code."""
import json
from functools import lru_cache
from pathlib import Path
import numpy as np

MODEL_PATH = Path(__file__).with_name("strategy_model.json")
FEATURES = ["count", "floor_ratio", "volume_ratio", "weight_ratio", "mean_length_ratio", "mean_width_ratio", "mean_height_ratio", "footprint_variation"]

def features(lorry, boxes):
    dims = np.asarray([[b["length"], b["width"], b["height"]] for b in boxes], dtype=float)
    truck = np.asarray([lorry["internal_length"], lorry["internal_width"], lorry["internal_height"]], dtype=float)
    areas = dims[:,0]*dims[:,1]
    return np.asarray([len(boxes)/50, areas.sum()/(truck[0]*truck[1]), np.prod(dims,axis=1).sum()/np.prod(truck), sum(float(b["loaded_weight"]) for b in boxes)/float(lorry["max_weight"]), *np.mean(dims/truck,axis=0), areas.std()/max(areas.mean(),1e-9)])

@lru_cache(maxsize=1)
def load_model():
    data=json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    if data["version"] != 1 or data["features"] != FEATURES:
        raise ValueError("Incompatible strategy model")
    return data

def rank_strategies(lorry, boxes, strategies):
    try:
        model=load_model()
        if model["strategies"] != [list(s) for s in strategies]:
            raise ValueError("Strategy model does not match optimizer")
        x=(features(lorry,boxes)-np.asarray(model["mean"]))/np.asarray(model["scale"])
        scores=np.r_[1.,x] @ np.asarray(model["coefficients"])
        if scores.shape != (len(strategies),) or not np.isfinite(scores).all():
            raise ValueError("Invalid predictions")
        ranked=sorted(range(len(strategies)),key=lambda i:(float(scores[i]),i))
        return [strategies[i] for i in ranked], True
    except (OSError, ValueError, KeyError, TypeError):
        return list(strategies), False
