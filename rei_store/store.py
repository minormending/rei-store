    def get_categories(self) -> List[Category]:
        url: str = f"{self.BASE_URL}/categories"
        resp: Response = self.session.get(url)

        matches: List[Tuple[str, str]] = re.findall('<h2>\s*<a href="(/c/[^"]*)"[^>]*>\s*([^<]*?)\s*</a>\s*</h2>', resp.text)
        for match in matches:
            yield Category(name=match[1].strip(), slug=match[0])