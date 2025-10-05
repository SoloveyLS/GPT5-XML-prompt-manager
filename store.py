from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional
from models import FieldNode

DATA_PATH = Path(__file__).parent / "stored" / "data.json"


def load_state() -> Optional[List[FieldNode]]:
    if not DATA_PATH.exists():
        return None
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        return [FieldNode.from_dict(d) for d in data]
    except Exception:
        return None


def save_state(nodes: List[FieldNode]) -> None:
    payload = [n.to_dict() for n in nodes]
    DATA_PATH.parent.mkdir(exist_ok=True)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")