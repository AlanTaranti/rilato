from pathlib import Path
from typing import Optional, Union
import traceback


def bytes_to_unicode(b: bytes, enc: Optional[str] = None) -> str:
    if enc is not None:
        enc = enc.lower().strip()
        if enc == "utf-8":
            return b.decode()
        return b.decode(enc).encode("utf-8").decode()
    return b.decode().encode("utf-8").decode()


def to_unicode(path: Union[Path, str]):
    try:
        if isinstance(path, str):
            path = Path(path)
        if not path.is_file():
            print(f"Error: path {path} is not a file")
            return
    except Exception:
        print(f"Error converting string {path} to Path")
        traceback.print_exc()
        return
    try:
        head = ""
        with open(path, "rb") as fd:
            while not head:
                head = fd.readline().decode().strip()
        if "encoding=" not in head:
            return
        enc = head[head.index("encoding=") + 9 :]
        quote = {'"': '"', "'": "'"}.get(enc[0], "")
        if quote:
            enc = enc[1:]
            enc = enc[: enc.index(quote)]
        else:
            ends = []
            for candidate in " ?>":
                if candidate in enc:
                    ends.append(enc.index(candidate))
            if len(ends) > 0:
                enc = enc[: min(ends)]
        enc = enc.lower()
        if enc == "utf-8":
            return
        with open(path, "rb") as fd:
            encfeed = fd.read()
        unicodefeed = encfeed.decode(encoding=enc).encode("utf-8")
        with open(path, "wb") as fd:
            fd.write(unicodefeed)
    except Exception:
        print(f"Error converting encoding to unicode for file {path}")
        traceback.print_exc()
