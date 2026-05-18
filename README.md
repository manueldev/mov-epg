# mov-epg

Automated EPG (Electronic Program Guide) generator in XMLTV format.

## How it works

* **`generate_epg.py`** builds an XMLTV-compatible XML file and saves it as
  the gzip-compressed `epg.xml.gz`.
* A **GitHub Actions workflow** (`.github/workflows/generate_epg.yml`) runs
  the script automatically every two days and commits the refreshed
  `epg.xml.gz` back to the repository.

## Running locally

```bash
python generate_epg.py
```

This creates (or overwrites) `epg.xml.gz` in the current directory.

## Customising channel/programme data

Edit the `CHANNELS` and `PROGRAMMES` lists near the top of `generate_epg.py`
to add your own channels and schedule entries.