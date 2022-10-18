import json
import logging
import re
from typing import Any, Dict, Iterable, List, Tuple
from requests import Response, Session

from rei_store.bazaar_request import BazaarRequest, ReviewsRequest

from .models import Category, trim_model


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

        script_tag: str = '<script type="application/json" id="modelData">'
        start_idx: int = resp.text.index(script_tag)
        if start_idx < 0:
            raise StopIteration

        end_idx: int = resp.text.index('</script>', start_idx)
        raw: str = resp.text[start_idx + len(script_tag):end_idx].strip()
        
        data: Dict[str, Any] = json.loads(raw)
        parent_categories: List[Dict[str, Any]] = data.get("pageData", {}).get("allCategories", [])
        for parent_category in parent_categories:
            child_categories: List[Dict[str, Any]] = parent_category.get("childrenCategories", [])
            for category in child_categories:
                yield Category(name=category.get("name"), slug=category.get("canonical"))

    def get_products(self, category: Category) -> List[Dict[str, Any]]:
        url: str = f"{category.url()}?json=true&pagesize=5000"
        headers: Dict[str, str] = {
            "accept-language": "en-US,en;q=0.9",
            "accept": "text/html",
            "Accept-Encoding": "gzip, deflate, br",
        }
        response: Response = self.session.get(url, headers=headers)
        resp: Dict[str, Any] = response.json()

        search: Dict[str, Any] = resp.get("searchResults", {})
        if not search:
            logging.error(f"Failed to get products for category {category.name}")
            return []

        total_results: int = search.get("query", {}).get("totalResults")
        if not total_results:
            logging.warn(
                f"Unable to determine total results count for category request."
            )
        elif total_results > 5000:
            logging.warning("Unable to get all products for category!")

        return search.get("results")

    def get_reviews(
        self, product_id: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        def get_pages(page_start: int, page_end: int, limit: int) -> Dict[str, Any]:
            queries: List[ReviewsRequest] = [
                ReviewsRequest.by_product_id(
                    product_id, limit, offset=(page - 1) * limit
                )
                for page in range(page_start, page_end + 1)
            ]
            request: BazaarRequest = BazaarRequest(queries=queries)
            resp: Response = self.session.get(request.url())
            return resp.json()

        reviews: List[Dict[str, Any]] = []
        authors: Dict[str, Dict[str, Any]] = {}
        limit: int = 100
        page: int = 1
        page_batch: int = 4
        while True:
            resp: Dict[str, Any] = get_pages(page, page + page_batch - 1, limit)
            batched_results: Dict[str, Any] = resp.get("BatchedResults", {})
            if not batched_results:
                logging.error(f"Failed to get reviews for page {page}")
                break

            review_count: int = 0
            queries: List[Dict[str, Any]] = batched_results.values()
            print("len of queries", len(queries))
            for query in queries:
                batch_reviews: List[Dict[str, Any]] = query.get("Results", [])
                print("got", len(batch_reviews), "reviews for batch")
                review_count += len(batch_reviews)
                reviews.extend(batch_reviews)

                batch_authors: Dict[str, Dict[str, Any]] = query.get(
                    "Includes", {}
                ).get("Authors", {})
                print("got", len(batch_authors), "authors for batch")
                for author_id, author in batch_authors.items():
                    authors[author_id] = author

            if review_count < (page_batch * limit):
                break
            page += page_batch

        return trim_model(reviews), trim_model(authors)

    def get_reviews_by_author(
        self, product_id: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        def get_pages(page_start: int, page_end: int, limit: int) -> Dict[str, Any]:
            queries: List[ReviewsRequest] = [
                ReviewsRequest.by_author_id(
                    product_id, limit, offset=(page - 1) * limit
                )
                for page in range(page_start, page_end + 1)
            ]
            request: BazaarRequest = BazaarRequest(queries=queries)
            resp: Response = self.session.get(request.url())
            return resp.json()

        reviews: List[Dict[str, Any]] = []
        products: Dict[str, Dict[str, Any]] = {}
        limit: int = 100
        page: int = 1
        page_batch: int = 4
        while True:
            resp: Dict[str, Any] = get_pages(page, page + page_batch - 1, limit)
            batched_results: Dict[str, Any] = resp.get("BatchedResults", {})
            if not batched_results:
                logging.error(f"Failed to get reviews for page {page}")
                break

            review_count: int = 0
            queries: List[Dict[str, Any]] = batched_results.values()
            for query in queries:
                batch_reviews: List[Dict[str, Any]] = query.get("Results", [])
                review_count += len(batch_reviews)
                reviews.extend(batch_reviews)

                batch_products: Dict[str, Dict[str, Any]] = query.get(
                    "Includes", {}
                ).get("Products", {})
                for product_id, product in batch_products.items():
                    products[product_id] = product

            if review_count < (page_batch * limit):
                break
            page += page_batch

        return trim_model(reviews), trim_model(products)
