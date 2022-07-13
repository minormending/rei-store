import argparse

from rei_store import REIStore


def main() -> None:
    store = REIStore()
    for c in store.get_categories():
        print(c.__dict__)


if __name__ == "__main__":
    main()
