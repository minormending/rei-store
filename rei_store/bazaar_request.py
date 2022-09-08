from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class BazaarFilter:
    field: str
    value: Any

    def expression(self) -> str:
        return f"{self.field}:eq:{self.value}"


@dataclass(kw_only=True)
class BazaarQuery:
    resource: str
    filters: List[BazaarFilter] = None
    filtered_stats: str = None
    sort: str = None
    stats: str = None
    include: List[str] = None
    limit: int = 100
    offset: int = 0

    def qs(self, num: int) -> List[str]:
        options: List[str] = [
            f"resource.q{num}={self.resource}",
            f"limit.q{num}={self.limit}",
            f"offset.q{num}={self.offset}",
        ]
        if self.filters:
            for bf in self.filters:
                print(bf)
                options.append(f"filter.q{num}={bf.expression()}")
        if self.filtered_stats:
            options.append(f"filteredstats.q{num}={self.filtered_stats}")
        if self.sort:
            options.append(f"sort.q{num}={self.sort}")
        if self.stats:
            options.append(f"stats.q{num}={self.stats}")
        if self.include:
            options.append(f"include.q{num}={','.join(self.include)}")

        return options


@dataclass(kw_only=True)
class ReviewsRequest(BazaarQuery):
    resource: str = "reviews"
    stats: str = "reviews"
    filtered_stats: str = "reviews"
    include: List[str] = field(
        default_factory=lambda: ["authors", "products", "comments"]
    )

    @classmethod
    def by_product_id(
        cls, product_id: str, limit: int, offset: int
    ) -> "ReviewsRequest":
        filters = [BazaarFilter("productid", product_id)]
        return ReviewsRequest(filters=filters, limit=limit, offset=offset)

    @classmethod
    def by_author_id(cls, author_id: str, limit: int, offset: int) -> "ReviewsRequest":
        filters = [BazaarFilter("authorid", author_id)]
        return ReviewsRequest(filters=filters, limit=limit, offset=offset)


@dataclass(kw_only=True)
class BazaarRequest:
    _url: str = "https://api.bazaarvoice.com/data/batch.json?"

    queries: List[BazaarQuery]

    def url(self) -> str:
        qs: List[str] = [
            "passkey=thvpbov9ywkkl4nkhbeq0wm1i",
            "apiversion=5.5",
        ]

        for idx, query in enumerate(self.queries):
            qs.extend(query.qs(num=idx))

        return self._url + "&".join(qs)
