import logging
import re
from typing import Any, Dict, Iterable, List, Tuple
from requests import Response, Session

from rei_store.bazaar_request import BazaarRequest, ReviewsRequest

from .models import Category


class REIStore:
    BASE_URL: str = "https://www.rei.com"

    def __init__(self) -> None:
        self.session: Session = Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
        }
        self.session.proxies = {"http": "127.0.0.1:8888", "https": "127.0.0.1:8888"}
        self.session.verify = False

    def get_categories(self) -> Iterable[Category]:
        url: str = f"{self.BASE_URL}/categories"
        headers: Dict[str, str] = {
            "accept-language": "en-US,en;q=0.9",
            "accept": "text/html",
            "Accept-Encoding": "gzip, deflate, br",
        }
        resp: Response = self.session.get(url, headers=headers)

        matches: List[Tuple[str, str]] = re.findall(
            '<h2>\s*<a href="(/c/[^"]*)"[^>]*>\s*([^<]*?)\s*</a>\s*</h2>', resp.text
        )
        for match in matches:
            yield Category(name=match[1].strip(), slug=match[0])

    def get_products(self, category: Category) -> List[Dict[str, Any]]:
        def get_page(page: int, limit: int) -> Dict[str, Any]:
            url: str = f"{category.url()}?json=true&pagesize={limit}"
            headers: Dict[str, str] = {
                "accept-language": "en-US,en;q=0.9",
                "accept": "text/html",
                "Accept-Encoding": "gzip, deflate, br",
            }
            resp: Response = self.session.get(url, headers=headers)
            return resp.json()

        results: List[Dict[str, Any]] = []
        limit: int = 5000
        page: int = 1
        while True:
            resp: Dict[str, Any] = get_page(page, limit)
            search: Dict[str, Any] = resp.get("searchResults", {})
            if not search:
                logging.error(f"Failed to get products for category {category.name} page {page}")
                break

            products: List[Dict, Any] = search.get("results")
            results.extend(products)

            total_results: int = search.get("query", {}).get("totalResults")
            if not total_results:
                logging.warn(f"Unable to determine total results count for category request, stopping after page {page}")
                break
            if total_results <= (page * limit):
                break
            page += 1

        return results

    def get_reviews(self, product_id: str) -> None:
        def get_page(page_start: int, page_end: int, limit: int) -> Dict[str, Any]:
            queries: List[ReviewsRequest] = [
                ReviewsRequest.by_product_id(product_id, limit, (i - 1) * limit)
                for i in range(page_start, page_end + 1)
            ]
            request: BazaarRequest = BazaarRequest(queries=queries)
            resp: Response = self.session.get(request.url())
            return resp.json()

        results: List[Dict[str, Any]] = []
        limit: int = 100
        page: int = 1
        page_batch: int = 4
        while True:
            resp: Dict[str, Any] = get_page(page, page + page_batch - 1, limit)
            batched_results: Dict[str, Any] = resp.get("BatchedResults", {})
            if not batched_results:
                logging.error(f"Failed to get page {page}")
                break

            count = 0
            queries = batched_results.values()
            for query in queries:
                r = query.get("Results", [])
                count += len(r)
                results.extend(r)

            if count <= (page_batch * limit):
                break
            page += page_batch

        return results
