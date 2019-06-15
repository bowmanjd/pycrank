#!/usr/bin/env python3

__version__ = "0.1.0"

import argparse
from collections import namedtuple
import functools
import json
from pathlib import Path

from paka import cmark

Page = namedtuple("Page", ["html", "conf"])


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


def content_files(directory):
    p = Path(directory)
    files = (f for f in p.glob("**/*") if f.suffix in (".html", ".md"))
    return files


def generate_one(inputfile, **kwargs):
    with inputfile.open() as f:
        content = f.read()

    frontmatter, body = content.split("\n}\n\n", 1)
    pageconf = json.loads(frontmatter + "}")
    conf = {**kwargs, **pageconf}
    output = body.format(**conf)
    if inputfile.suffix == ".md":
        html = cmark.to_html(output)
    else:
        html = output.strip()
    if not conf.get("no_header_footer"):
        headerfile = conf.get("header")
        footerfile = conf.get("footer")
    page = Page(html, conf)
    return page


def generate(files, **kwargs):
    for inputfile in files:
        yield generate_one(inputfile, **kwargs)


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
    write(args.out, generate(content_files(args.src), **conf))
