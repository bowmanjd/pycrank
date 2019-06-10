#!/usr/bin/env python3

__version__ = "0.1.0"

import argparse
from collections import namedtuple
import functools
import json
from pathlib import Path
import shutil

from paka import cmark

Page = namedtuple("Page", ["html", "conf"])


@functools.lru_cache()
def get_config(filename):
    p = Path(filename)
    try:
        with p.open() as f:
            conf = json.load(f)
    except FileNotFoundError:
        conf = {"baseURL": "", "title": ""}
    return conf


def redirect_content(self, url, title="This page"):
    content = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{title} has moved</title>\n"
        f'  <meta http-equiv="refresh" content="0; URL={url}">\n'
        f'  <link rel="canonical" href="{url}">\n'
        "</head>\n"
        "<body>\n"
        "  <p>\n"
        f"    <strong>{title}</strong>\n"
        f'    has moved to <a href="{url}">{url}</a>\n'
        "  </p>\n"
        "</body>\n"
        "</html>\n"
    )
    return content


def content_files(directory):
    p = Path(directory)
    files = (f for f in p.glob("**/*") if f.suffix in (".html", ".md"))
    return files


def generate(files, siteconf={}):
    for inputfile in files:
        with inputfile.open() as f:
            content = f.read()

        frontmatter, body = content.split("}\n\n", 1)
        pageconf = json.loads(frontmatter + "}")
        conf = {**siteconf, **pageconf}
        output = body.format(**conf)
        html = cmark.to_html(output)
        page = Page(html, conf)
        yield page


def write(outdir, generated):
    shutil.rmtree(outdir)
    for page in generated:
        path = pathlib.Path(outdir, *page.conf["categories"], page.conf["slug"])
        path.mkdir(parents=True, exist_ok=True)
        with (path / "index.html").open("w") as f:
            f.write(page.html)


def run():
    parser = argparse.ArgumentParser(description="A simple static site generator")
    parser.add_argument("src", help="Source directory containing markdown files")
    parser.add_argument("out", help="Output directory for html files and structure")
    args = parser.parse_args()
    write(args.out, generate(content_files(args.src)))
