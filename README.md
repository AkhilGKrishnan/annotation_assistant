# Annotation assistant

## Description

Simple html interface to automatize MTAAC annotation-related operations. Heavly relies on [MPAT](https://github.com/cdli-gh/morphology-pre-annotation-tool) for its core operations.
MPAT, its dictionary, and annotated data are updated on start and before each operation.

## Requires:
- Git
- Python 3.6
- Jinja2
- Eel
- PyGithub

## Installation (Windows):
1. Install [Git](https://www.atlassian.com/git/tutorials/install-git) ([Windows](https://github.com/git-for-windows/git/releases/download/v2.17.0.windows.1/Git-2.17.0-64-bit.exe)).
2. Install [Python 3.6](https://www.python.org/downloads/release/python-365/) ([Windows](https://www.python.org/ftp/python/3.6.5/python-3.6.5-amd64.exe)).
3. In Command Prompt / Powershell: Go to a desired location (`cd <PATH>`) and clone this repo with `git clone https://github.com/cdli-gh/annotation_assistant.git`
4. In Command Prompt / Powershell (continue): Go to the `scr` directory in the cloned repo (`cd scr`) and install remaining dependecies with `pip install -r dependencies.txt`.

## Running (Windows):
1. Windows explorer: Simply double click on `main.py` in `annotation_assistant/scr/`.
2. Alternatively, in Command Prompt / Powershell:\
`python main.py` (when in `scr` directory) OR `python <PATH TO REPO>/annotation_assistant/scr/main.py` (any).
3. Alternatively, open `main.py` with Python IDLE, then run it (F5 or in menu).

## Warnings and notes:
- The window might freeze when running scripts in the background. Just wait for them to finish.
- Logs for each session are stored in `annotation_assistant/scr/console.log`.
- Your Github credentials are stored locally if you choose to save them.

## Operations, short summary:

### Select new text:
1. Select random text to annotate.
2. Create a local copy of the `.conll` file.
3. Preannotate `.conll` file with MPAT.
4. Update `progress.json`.
5. Push changes to repo.

### Convert and upload text:
1. Run MPAT with `-f` switch to correct the file format, removing extra columns adding underscores in empty cells.
2. Move `.conll` file to ready files directory (`to_dict`).
3. Update `progress.json`.
4. Push changes to repo.
