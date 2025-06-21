from urllib.parse import urlparse


def create_full_url(link: str, path: str) -> str:
    # already full
    if path.startswith("https://") or path.startswith("http://"):
        return path
    # absolute
    if path.startswith("/"):
        parsed = urlparse(link)
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    # relative
    return link + ("" if link.endswith("/") else "/") + path
