" Various utility functions used in the example XRD analysis "

# imports
import pathlib


def get_raw_file_name(xrd_file_path_or_bytesio):
    """Returns the raw file name from the header of the given XRD file

    Args:
        xrd_file_path_or_bytesio (str, pathlib.Path, or io.BytesIO): The path to an XRD
            file with its original raw file name in the second field of the second line
            (or BytesIO object of the same)

    Returns:
        The raw file name from the header of the file as a string
    """
    if isinstance(xrd_file_path_or_bytesio, pathlib.Path) or isinstance(
        xrd_file_path_or_bytesio, str
    ):
        with open(xrd_file_path_or_bytesio, "r") as fp:
            _ = fp.readline()
            line_2 = fp.readline()
    elif hasattr(xrd_file_path_or_bytesio, "readline"):
        _ = xrd_file_path_or_bytesio.readline()
        line_2 = xrd_file_path_or_bytesio.readline().decode()
    else:
        errmsg = (
            f"ERROR: expected path or readable for {xrd_file_path_or_bytesio} "
            f" but got {type(xrd_file_path_or_bytesio)} instead!"
        )
        raise ValueError(errmsg)
    raw_file_name = line_2.split(",")[-1]
    return raw_file_name


def get_angle_interval_size(xrd_angles_column):
    """Given the "angle" column of an XRD dataframe, return the size of the steps between
    each measurement

    Args:
        xrd_angles_column (pandas.core.series.Series): The angular measurement column
            from an XRD csv file dataframe

    Returns:
        The spacing between each of the angle measurements as a float (one decimal place
        less precise than the original data, to account for rounding errors)

    Raises:
        ValueError: If more than one step size is found between datapoints in the column
    """
    interval_size = None
    angle_precisions = xrd_angles_column.apply(
        lambda x: len(str(x).split(".")[1]) if "." in str(x) else 0
    )
    max_precision = max(angle_precisions)
    step_sizes = xrd_angles_column.diff().dropna().round(max_precision - 1)
    if step_sizes.nunique() == 1:
        interval_size = step_sizes.iloc[0]
    else:
        raise ValueError(
            f"Angles are not all evenly spaced! Found intervals: {step_sizes.unique()}"
        )
    return interval_size
