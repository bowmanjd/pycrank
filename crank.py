#!/usr/bin/env python3

__version__ = "0.1.0"

import argparse
from collections import namedtuple
import functools
import json
from pathlib import Path

from paka import cmark

Page = namedtuple("Page", ["content", "conf"])


def rmdir(path):
    directory = Path(path)
    try:
        for item in directory.iterdir():
            if item.is_dir():
                rmdir(item)
            else:
                item.unlink()
        directory.rmdir()
    except FileNotFoundError:
        pass


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


def content_filenames(directory):
    p = Path(directory)
    files = p.glob("**/*")
    return files


def content_from_file(filename):
    path = Path(filename)
    if path.is_file():
        with path.open() as f:
            content = f.read()
    else:
        content = ""
    return content


def parse_md(page):
    html = cmark.to_html(page.content)
    output = Page(html, page.conf)
    return output


def parse(page):
    parts = page.content.split("\n}\n\n", 1)
    body = parts[-1]
    try:
        frontmatter = parts[-2]
        pageconf = json.loads(frontmatter + "}")
    except IndexError:
        pageconf = {}
    conf = {**page.conf, **pageconf}
    content = body.format(**conf).strip()
    # if not conf.get("no_header_footer"):
    output = Page(content, conf)
    return output


def header_footer(page):
    headerfile = page.conf.get("header", "")
    footerfile = page.conf.get("footer", "")
    header = content_from_file(headerfile)
    footer = content_from_file(footerfile)


def generate_all(files, **kwargs):
    for inputfile in files:
        if inputfile.suffix in (".html", ".md"):
            yield generate(inputfile, **kwargs)


def write(outdir, generated):
    rmdir(outdir)
    for page in generated:
        path = Path(outdir, *page.conf["categories"], page.conf["slug"])
        path.mkdir(parents=True, exist_ok=True)
        with (path / "index.html").open("w") as f:
            f.write(page.html)


def run():
    parser = argparse.ArgumentParser(description="A simple static site generator")
    parser.add_argument(
        "-v", "--version", action="version", version=f"{__name__} {__version__}"
    )
    parser.add_argument("src", help="Source directory containing markdown files")
    parser.add_argument("out", help="Output directory for html files and structure")
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file, in JSON (default: config.json from the source directory)",
    )
    args = parser.parse_args()
    if args.config:
        cfile = Path(args.config)
    else:
        cfile = Path(args.out, "config.json")
    conf = get_config(cfile)
    write(args.out, generate_all(content_filenames(args.src), **conf))
