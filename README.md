<h2 align='center'>PyQt6 | Shot Builder</h2>
<img width="932" height="759" alt="image" src="https://github.com/user-attachments/assets/fd0c0017-e5c0-4d2e-8d7f-488dc4fecb79" />


# PyQt6 Shot Builder

Tools for build shot from mastershot.

A lightweight PyQt6 desktop app to help break down a master shot into individual shots, manage shot metadata, and export shot lists for downstream tools in your pipeline.

> Status: early development

---

## Features

- Create and manage shot lists derived from a master shot
- Set frame/timecode In/Out ranges per shot
- Configure shot naming templates (e.g., `project_ep101_sq01_sh0010`)
- Import shot lists (CSV)
- Simple, fast PyQt6 UI

---

## Requirements

- Python 3.11 (recommended)
- PyQt6

Additional dependencies (if any) are listed in `requirements.txt`.

---

## Installation

```bash
# 1) Clone
git clone https://github.com/MrYapikZ/PyQt6-Shot-Builder.git
cd PyQt6-Shot-Builder

# 2) (Optional) Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3) Install dependencies
# Install PyQt6:
pip install PyQt6 PyQt6-tools
```

---

## Quick Start

```bash
# Run the application (adjust the entry point to match the repo's main script)
python run.py
```

---

## Usage

1. Set Blender Program Path: Configure the path to your Blender installation.
2. Set CSV File: Provide the CSV file containing episode, sequence, shot, start frame, and end frame.
3. Set Master Shot File: Select the master shot file to be used as a template.
4. Select Shot to Generate: Choose the specific shot you want to generate.
5. Generate Shot: Create the selected shot based on the CSV data.

---

## CSV Format
This format is used to document episode, sequence, shot, and frame range information in production.

| EPISODE | SEQUENCE | SHOT | FRAME IN | FRAME OUT |
|-----------|-----------|-----------|-----------|-----------|
| EP999 | SQ03 | SH0010 | 101 | 210 |

- EPISODE: Episode ID (e.g., EP999)
- SEQUENCE: Sequence ID (e.g., SQ03)
- SHOT: Shot ID (e.g., SH0010)
- FRAME IN: Start frame (e.g., 101)
- FRAME OUT: End frame (e.g., 210)

---

## Project Structure

A typical layout might look like:
```
PyQt6-Shot-Builder/
├─ run.py
├─ README.md
├─ LICENSE
└─ app
  ├─ data
  ├─ modules
  ├─ services
  ├─ ui
  └─ main.py
```

Your repository structure may vary; update paths accordingly.

---

## Development

- Code style: follow standard Python style (PEP 8).
- Virtual envs are recommended.
- If tests exist:
  ```bash
  pytest -q
  ```

---


## Troubleshooting

- PyQt6 plugin errors on launch:
  - Ensure the virtual environment is active and PyQt6 is installed: `pip show PyQt6`
- High-DPI scaling issues:
  - Try setting `QT_SCALE_FACTOR=1` or `QT_AUTO_SCREEN_SCALE_FACTOR=1`

---

## License

MIT License. See [LICENSE](./LICENSE) for details.

---

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/).
