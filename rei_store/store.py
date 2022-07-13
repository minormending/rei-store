import re
from typing import Iterable, List, Tuple
from requests import Response, Session

from .models import Category


class REIStore:
    BASE_URL: str = "https://www.rei.com"

    def __init__(self) -> None:
        self.session: Session = Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
            "accept-language": "en-US,en;q=0.9",
            "accept": "text/html",
            "Accept-Encoding": "gzip, deflate, br",
        }

    def get_categories(self) -> Iterable[Category]:
        url: str = f"{self.BASE_URL}/categories"
        resp: Response = self.session.get(url)

        matches: List[Tuple[str, str]] = re.findall(
            '<h2>\s*<a href="(/c/[^"]*)"[^>]*>\s*([^<]*?)\s*</a>\s*</h2>', resp.text
        )
        for match in matches:
            yield Category(name=match[1].strip(), slug=match[0])
