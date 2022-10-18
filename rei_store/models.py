from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Category:
    name: str
    slug: str

    def url(self) -> str:
        return f"https://www.rei.com{self.slug}"


def trim_model(model: Any) -> Any:
    if isinstance(model, list):
        output: List[Any] = []
        for value in model:
            cleaned_value = trim_model(value)
            if cleaned_value:
                output.append(cleaned_value)
        return output
    elif isinstance(model, dict):
        output: Dict[str, Any] = {}
        for key, value in model.items():
            cleaned_value = trim_model(value)
            if cleaned_value:
                output[key] = cleaned_value
        return output
    else:
        return model
