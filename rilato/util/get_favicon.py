from gettext import gettext as _
from PIL import Image
from os.path import isfile
from os import remove, replace
from rilato.util.create_full_url import create_full_url
from rilato.util.download_manager import download_raw
from rilato.util.paths import CACHE_PATH
from rilato.util.sha import shasum
from rilato.util.html_parser import Html

# Create a simple MIME type detector that doesn't rely on python-magic
import mimetypes


class SimpleMimeDetector:
    def from_file(self, file_path):
        # Initialize mimetypes if not already done
        if not mimetypes.inited:
            mimetypes.init()

        # Get MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(file_path)

        # If we couldn't determine the MIME type, try a simple check for SVG
        if not mime_type:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(1000)  # Read first 1000 chars
                    if "<svg" in content:
                        return "image/svg+xml"
            except:  # noqa E722
                pass

            # Default to a generic type if we can't determine it
            return "application/octet-stream"

        return mime_type


# Use our simple MIME detector instead of python-magic
mime = SimpleMimeDetector()


def get_favicon(link: str, favicon_path: str, direct: bool = False):
    """
    If `link` is the direct url to download the favicon, pass `direct=True`
    """

    favicon_path_orig = favicon_path + ".original"

    if direct:
        download_raw(link, favicon_path_orig)
    else:
        try:
            page_dest = str(CACHE_PATH.joinpath(shasum(link) + ".html"))
            if not isfile(page_dest):
                download_raw(link, page_dest)
            sd_html = Html(page_dest)
            url = sd_html.icon_url
            if not url:
                return
        except Exception:
            return
        p = url
        if "?" in p:
            p = p.split("?")[0]
        target = create_full_url(link, url)
        try:
            download_raw(target, favicon_path_orig)
        except Exception:
            try:
                download_raw(target, favicon_path_orig)
            except Exception:
                print(_("Error downloading favicon for `{0}`").format(link))
                return
    if mime.from_file(favicon_path_orig) == "image/svg+xml":
        replace(favicon_path_orig, favicon_path)
        return
    toconv = Image.open(favicon_path_orig)
    toconv.convert(mode="RGBA")
    toconv.save(favicon_path, format="PNG")
    toconv.close()
    remove(favicon_path_orig)
