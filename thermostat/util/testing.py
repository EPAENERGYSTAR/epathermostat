from pathlib import Path
import inspect


def get_data_path(f=''):
    """Return the path of a data file, these are relative to the current test
    directory. (Thanks, pydata/pandas/pandas/util/testing.py!)
    """
    # get our callers file
    _, filename, _, _, _, _ = inspect.getouterframes(inspect.currentframe())[1]
    base_dir = Path(filename).parents[0].resolve()
    return base_dir / f
