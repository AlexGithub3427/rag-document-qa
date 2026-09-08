import json
from typing import Any


def custom_serializer(obj: Any) -> str:
    def default(o):
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json")
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
    return json.dumps(obj, default=default)
