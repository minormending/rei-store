
from dataclasses import dataclass


@dataclass
class Category:
    name: str
    slug: str

    def url(self) -> str:
        return f"https://www.rei.com{self.slug}"