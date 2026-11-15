# Detail Manager - User Guide (draft)

Notes collected as we build. To be written up properly for release 0.3.

## What the computer needs (current prototype)
Until the standalone program exists (planned for 0.3), each computer that runs
Detail Manager needs:

- Windows 10 or 11
- **Python 3.12 or newer**, installed from python.org with the default options
  (these include the `py` launcher, `pip` and Tkinter, all of which are used)
- **PyMuPDF** (a Python add-on that makes the full thumbnails). `SETUP_THIS_COMPUTER.bat`
  installs it; by hand: `py -m pip install pymupdf`
- SketchUp and LayOut 2025
- A web browser
- The detail library reachable at its normal path (Z: for the company library)

To check a computer: run `VERIFY_THIS_COMPUTER.bat`, or type `py --version` in
Command Prompt.

**After 0.3:** the standalone program brings its own Python, so staff computers
will need none of the Python items above.

## For whoever maintains the program (not staff)
Running the regression tests needs only Python itself (no PyMuPDF):

    cd /d C:\sketchup_dev\detail_manager
    py -m unittest discover -s tests
