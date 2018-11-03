# Annotation assistant

## Description

Simple html interface to automatize MTAAC annotation-related operations. Heavly relies on [MPAT](https://github.com/cdli-gh/morphology-pre-annotation-tool) for its core operations.
MPAT, its dictionary, and annotated data are updated on start and before each operation.

## Requires:
- Git
- Python 3.6 or higher
- [Visual C++](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads) 2014 or higher
- Jinja2
- [Eel](https://github.com/ChrisKnott/Eel/) (modified)
- PyGithub

## Installation:
1. Install [Git](https://www.atlassian.com/git/tutorials/install-git) ([Windows](https://github.com/git-for-windows/git/releases/download/v2.17.0.windows.1/Git-2.17.0-64-bit.exe), [Mac](https://sourceforge.net/projects/git-osx-installer/files/), [Linux](https://www.atlassian.com/git/tutorials/install-git#linux)).
2. On Windows, install [Visual C++](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads) 2014 or higher.
3. Install [Python 3.6](https://www.python.org/downloads/release/python-365/) ([Windows](https://www.python.org/ftp/python/3.6.5/python-3.6.5-amd64.exe), [Mac](https://www.python.org/downloads/mac-osx/), [Linux](https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa)).
4. In Command Prompt / Powershell (Windows) / Bash terminal (Mac, Linux): Go to a desired location (`cd <PATH>`) and clone this repo with `git clone https://github.com/cdli-gh/annotation_assistant.git`
5. In Command Prompt / Powershell (Windows) / Bash terminal (Mac, Linux) (continue): Go to the `scr` directory in the cloned repo (`cd scr`) and install remaining dependecies with `pip install -r dependencies.txt`.

## Running:
1. (Windows explorer:) Double click on `main.py` in `annotation_assistant/scr/`.
2. Alternatively, in Command Prompt / Powershell (Windows) / Bash terminal (Mac, Linux):\
`python main.py` (when in `scr` directory) OR `python <PATH TO REPO>/annotation_assistant/scr/main.py` (any).
3. Alternatively, open `main.py` with Python IDLE, then run it (F5 or in menu).

## Warnings and notes:
- Logs for each session are stored in `annotation_assistant/scr/console.log`.
- commit 3c56b97: The files are now checked and corrected within the script each time `to_dict ` is updated and when a new annotated text is uploaded. (This happens before running MPAT with `-f` and in fact does the same, but better). Performs the following:   
    * CSV > TSV.
    * ENSI > UTF-8.
    * Add underscores ('_') to empty columns.
    * Remove extra annotation suggestions.
    * Clear last three columns (`HEAD`, `DEPREL`, `MISC`).

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
