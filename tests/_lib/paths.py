"""Locations of the project artefacts under test, plus rar extraction."""

import os
import shutil
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- the dashboard pipeline ----------------------------------------------------
DASHBOARD_DIR = os.path.join(REPO_ROOT, "dashboard")
DATA_JSON = os.path.join(DASHBOARD_DIR, "data.json")
BTL_JSON = os.path.join(DASHBOARD_DIR, "btl.json")
TEMPLATE_HTML = os.path.join(DASHBOARD_DIR, "template.html")
INDEX_HTML = os.path.join(DASHBOARD_DIR, "index.html")
ARTIFACT_HTML = os.path.join(DASHBOARD_DIR, "artifact.html")
BUILD_DATA_PY = os.path.join(DASHBOARD_DIR, "build_data.py")
BUILD_BTL_PY = os.path.join(DASHBOARD_DIR, "build_btl.py")
BUILD_PY = os.path.join(DASHBOARD_DIR, "build.py")

# --- Eshkol matching -----------------------------------------------------------
ESHKOL_DIR = os.path.join(REPO_ROOT, "eshkol-matching")
ESHKOL_MAPPING_XLSX = os.path.join(ESHKOL_DIR, "eshkol_mapping.xlsx")
ESHKOL_SKILL_MD = os.path.join(ESHKOL_DIR, "SKILL.md")
ESHKOL_MATCHER_PY = os.path.join(ESHKOL_DIR, "eshkol_matcher.py")

# --- CBS source workbooks the pipeline reads ----------------------------------
SRC_WORKBOOKS = {
    "anaf_2024": "עיבוד לפי ענף ורשות בני דורמבט.xlsx",
    "anaf_2022": "עיבוד לפי ענף ורשות 2022.xlsx",
    "anaf_by_auth": "ענף כלכלי ורשות 1גליל מזרחי.xlsx",
    "dictionary": "dicAnaf4SfarotMaster 2.xlsx",
    "btl_table8": "שכר ממוצע לחודש עבודה של כלל העובדים, לפי מחוז ונפה, 2022-2016.xlsx",
}

RELEVANT_TABLES_RAR = os.path.join(REPO_ROOT, "relevant_tables.rar")
_CACHE_DIR = os.path.join(REPO_ROOT, ".test-cache")
BTL_TABLES_DIR = os.path.join(_CACHE_DIR, "relevant_tables")


def source_workbook(key):
    return os.path.join(REPO_ROOT, SRC_WORKBOOKS[key])


def extraction_tool():
    """The rar extractor to use, or None.

    p7zip 16.x cannot read RAR5 — it silently writes empty files — so bsdtar is
    the only extractor accepted here.
    """
    return shutil.which("bsdtar")


def btl_tables_dir():
    """Extract (once) and return the BTL tables directory, or None if unavailable.

    Eight of the 180 workbooks have filenames longer than the 255-byte limit most
    filesystems impose, so the bulk extraction drops them. They are pulled out
    individually under short names — harmless, because btl_read.py indexes tables
    by the sheet name and the title in cell A1, never by filename.
    """
    marker = os.path.join(BTL_TABLES_DIR, ".extracted")
    if os.path.exists(marker):
        return BTL_TABLES_DIR
    tool = extraction_tool()
    if not os.path.exists(RELEVANT_TABLES_RAR) or tool is None:
        return None
    os.makedirs(_CACHE_DIR, exist_ok=True)
    subprocess.run([tool, "-xf", RELEVANT_TABLES_RAR, "-C", _CACHE_DIR], capture_output=True)
    if not os.path.isdir(BTL_TABLES_DIR):
        return None

    listing = subprocess.run(
        [tool, "-tf", RELEVANT_TABLES_RAR], capture_output=True, text=True
    ).stdout.splitlines()
    on_disk = {name for name in os.listdir(BTL_TABLES_DIR) if name.endswith(".xlsx")}
    too_long = [
        member
        for member in listing
        if member.endswith(".xlsx") and os.path.basename(member) not in on_disk
    ]
    for index, member in enumerate(too_long):
        target = os.path.join(BTL_TABLES_DIR, "longname_%d.xlsx" % index)
        with open(target, "wb") as handle:
            subprocess.run([tool, "-xOf", RELEVANT_TABLES_RAR, member], stdout=handle)
        if os.path.getsize(target) == 0:
            os.remove(target)

    open(marker, "w").close()
    return BTL_TABLES_DIR
