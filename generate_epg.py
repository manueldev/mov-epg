#!/usr/bin/env python3
"""
generate_epg.py - Generates an XMLTV-format EPG (Electronic Program Guide)
and saves it as a gzip-compressed file (epg.xml.gz).

Add or modify channel/programme data below to customise the output.
"""

import gzip
import os
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from xml.dom import minidom

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_FILE = "epg.xml.gz"

# Each channel entry:  { "id": str, "display_name": str, "icon": str|None }
CHANNELS = [
    {"id": "channel1.mov", "display_name": "Channel 1", "icon": None},
    {"id": "channel2.mov", "display_name": "Channel 2", "icon": None},
]

# Each programme entry:
# {
#   "channel": str,          # must match a channel id above
#   "start":   str,          # XMLTV datetime  "YYYYMMDDHHmmss +0000"
#   "stop":    str,
#   "title":   str,
#   "desc":    str|None,
# }
PROGRAMMES = [
    {
        "channel": "channel1.mov",
        "start": "20260101080000 +0000",
        "stop":  "20260101090000 +0000",
        "title": "Morning Show",
        "desc":  "Your daily morning programme.",
    },
    {
        "channel": "channel1.mov",
        "start": "20260101090000 +0000",
        "stop":  "20260101100000 +0000",
        "title": "News at 9",
        "desc":  "Latest news headlines.",
    },
    {
        "channel": "channel2.mov",
        "start": "20260101080000 +0000",
        "stop":  "20260101100000 +0000",
        "title": "Weekend Movie",
        "desc":  "Feature film.",
    },
]

# ---------------------------------------------------------------------------
# Build XML tree
# ---------------------------------------------------------------------------


def build_xmltv() -> ET.Element:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S %z")
    root = ET.Element(
        "tv",
        attrib={
            "date": now,
            "source-info-name": "mov-epg",
            "generator-info-name": "generate_epg.py",
        },
    )

    for ch in CHANNELS:
        channel_el = ET.SubElement(root, "channel", id=ch["id"])
        display = ET.SubElement(channel_el, "display-name")
        display.text = ch["display_name"]
        if ch.get("icon"):
            ET.SubElement(channel_el, "icon", src=ch["icon"])

    for prog in PROGRAMMES:
        prog_el = ET.SubElement(
            root,
            "programme",
            attrib={
                "start":   prog["start"],
                "stop":    prog["stop"],
                "channel": prog["channel"],
            },
        )
        title_el = ET.SubElement(prog_el, "title", lang="en")
        title_el.text = prog["title"]
        if prog.get("desc"):
            desc_el = ET.SubElement(prog_el, "desc", lang="en")
            desc_el.text = prog["desc"]

    return root


def prettify(element: ET.Element) -> bytes:
    """Return a pretty-printed XML byte string with declaration."""
    rough = ET.tostring(element, encoding="unicode")
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ", encoding="UTF-8")


# ---------------------------------------------------------------------------
# Write gzip output
# ---------------------------------------------------------------------------


def generate(output_path: str = OUTPUT_FILE) -> None:
    root = build_xmltv()
    xml_bytes = prettify(root)
    with gzip.open(output_path, "wb") as fh:
        fh.write(xml_bytes)
    size = os.path.getsize(output_path)
    print(f"Generated {output_path} ({size} bytes compressed)")


if __name__ == "__main__":
    generate()
