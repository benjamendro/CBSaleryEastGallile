"""Loaders for the dashboard's processed data and published pages, and a sandbox
in which the build pipeline can be re-run without touching the working tree.
"""

import json
import os
import re
import shutil
import subprocess
import sys

from . import paths

DATA_MARKER = '"__DATA__"'
LOGO_MARKER = "__LOGO__"


def load_data():
    """dashboard/data.json — part A (CBS 2024), as the dashboard receives it."""
    with open(paths.DATA_JSON, encoding="utf-8") as handle:
        return json.load(handle)


def load_btl():
    """dashboard/btl.json — part B (National Insurance 2016–2024)."""
    with open(paths.BTL_JSON, encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def embedded_payload(html):
    """Return the JSON object build.py injected into a published page.

    The payload is data.json with btl.json added under 'btl2', serialised with
    no whitespace, so it is located by its opening key and matched by scanning
    for the balancing brace.
    """
    start = html.find('const DATA=') if 'const DATA=' in html else html.find('DATA =')
    brace = html.find("{", start)
    if start == -1 or brace == -1:
        raise AssertionError("no injected DATA object found in the page")
    depth, in_string, escaped = 0, False, False
    for index in range(brace, len(html)):
        char = html[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[brace:index + 1])
    raise AssertionError("the injected DATA object is not balanced")


def make_sandbox(destination):
    """Copy everything the pipeline reads into `destination` and return the path.

    The build scripts resolve every path from their own __file__, so a copied
    tree rebuilds exactly as the real one does — and a test that rebuilds can
    never corrupt the checkout.
    """
    os.makedirs(destination, exist_ok=True)
    for folder in ("dashboard", "scripts", "eshkol-matching"):
        shutil.copytree(
            os.path.join(paths.REPO_ROOT, folder),
            os.path.join(destination, folder),
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    assets = os.path.join(destination, "design", "assets")
    os.makedirs(assets, exist_ok=True)
    shutil.copy2(
        os.path.join(paths.REPO_ROOT, "design", "assets", "logo.jpg"),
        os.path.join(assets, "logo.jpg"),
    )
    for key in paths.SRC_WORKBOOKS:
        source = paths.source_workbook(key)
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(destination, os.path.basename(source)))
    return destination


def run_build(script, sandbox, env_extra=None):
    """Run one pipeline script inside the sandbox and return the CompletedProcess."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, os.path.join(sandbox, "dashboard", script)],
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )


NUMBER_RE = re.compile(r"(?<![\w.#-])\d{3,}(?:\.\d+)?(?![\w%])")


def template_without_code_constants(html):
    """The template's markup with SVG geometry and CSS stripped, for number scans.

    Chart code legitimately contains geometry (viewBox sizes, pixel offsets,
    durations). What must never appear is a *figure* — a workers count, a wage,
    a percentage — written into the markup instead of read from DATA.
    """
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    return html
