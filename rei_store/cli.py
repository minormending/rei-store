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


if __name__ == "__main__":
    main()
