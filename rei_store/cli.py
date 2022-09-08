import argparse

from rei_store import REIStore
from rei_store.models import Category


def main() -> None:
    store = REIStore()
    categories: Category = list(store.get_categories())
    for c in categories:
        print(c.__dict__)

    cat = categories[0]
    products = store.get_products(cat)
    for p in products:
        print(p)
        break

    product = products[0]
    reviews = store.get_reviews(product["prodId"])


if __name__ == "__main__":
    main()
