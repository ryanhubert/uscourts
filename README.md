# uscourts

A toolkit for working with U.S. court data in text formats.

To use, download and place package directory in either (1) the working directory for projects that use the package or (2) in your local `site-packages` directory (or another directory in your `PYTHONPATH`).

Note: in `python`, you may point to the package anywhere on your computer, such as `mydir`, if you `sys.path.append(mydir)`.

## Available packages

[`uscourts.judges`](/judges)

Tools for working with data on federal (Article III) judges.

- downloads and saves the Federal Judicial Center's biography of federal judges
- reshapes data for efficient use in other python tasks
- provides a tool to identify occurrences of judge names in unstructured text

Planned improvements:

- Tool to generate an easy-to-use `csv` file containing key information about judges' work histories, education, and nominations
- Add federal magistrate and Article IV judges
