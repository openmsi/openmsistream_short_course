" Data-crunching functions for the example XRD analysis "

# imports
import numpy as np
import scipy
import lmfit
from utils import get_angle_interval_size

# The minimum distance between peaks (in intervals)
MIN_N_INTERVAL_SEPARATION = 5
# Scaling factor for the std dev in the prominence requirement in the find_peaks function
PROMINENCE_SCALE_FACTOR = 0.8
# The window length for the find_peaks call (in intervals)
WINDOW_LENGTH = 50
# Peaks will not be found below this angle
MIN_ANGLE = 10
# Minimum size (in intervals) of a segment around a particular peak or set of peaks
NEIGHBORHOOD_INTERVALS = 100


def get_peak_segments(xrd_df):
    """Return a list of dictionaries representing segments of the XRD data containing
    one or more peaks.

    Args:
        xrd_df (pandas.DataFrame): The dataframe of the entire XRD dataset with "angle"
            and "count" columns

    Returns:
        A list of segment dictionaries. Each dictionary in the list includes a "min"
            angle, a "max" angle, a list of "peak_angles" where peaks were found,
            and a list of "peak_counts" giving the heights of those peaks
    """
    # Get the distance between each datapoint in the dataframe
    interval_size = get_angle_interval_size(xrd_df["angle"])
    neighborhood_size = NEIGHBORHOOD_INTERVALS * interval_size
    # run peak finding in the counts data
    peaks, _ = scipy.signal.find_peaks(
        xrd_df["counts"],
        # prominence=np.std(xrd_df["counts"]),
        prominence=PROMINENCE_SCALE_FACTOR * np.std(xrd_df["counts"]),
        wlen=WINDOW_LENGTH,
        distance=MIN_N_INTERVAL_SEPARATION,
    )
    peak_angles = xrd_df["angle"].iloc[peaks]
    peak_counts = xrd_df["counts"].iloc[peaks]
    # Create the list of peak segment dictionaries
    peak_segments = []
    peak_angles_done = set()
    for peak_angle, peak_count in zip(peak_angles, peak_counts):
        if peak_angle < MIN_ANGLE or peak_angle in peak_angles_done:
            continue
        # Iteratively add peaks to the segment until a discrete neighborhood with some
        # number of peaks is found
        last_peaks_in_seg = []
        peaks_in_seg = [(peak_angle, peak_count)]
        while peaks_in_seg != last_peaks_in_seg:
            seg_min_angle = min(p[0] for p in peaks_in_seg) - 0.5 * neighborhood_size
            seg_max_angle = max(p[0] for p in peaks_in_seg) + 0.5 * neighborhood_size
            last_peaks_in_seg = peaks_in_seg
            peaks_in_seg = [
                (p_a, p_c)
                for p_a, p_c in zip(peak_angles, peak_counts)
                if p_a >= seg_min_angle - 0.5 * neighborhood_size
                and p_a <= seg_max_angle + 0.5 * neighborhood_size
                and p_a >= MIN_ANGLE
            ]
        for p_a, p_c in peaks_in_seg:
            peak_angles_done.add(p_a)
        # Filter out any smaller peaks too close to larger peaks
        filtered_peaks = []
        for p_a, p_c in peaks_in_seg:
            nearby_peaks_counts = [
                p_c_other
                for p_a_other, p_c_other in peaks_in_seg
                if abs(p_a - p_a_other) < MIN_N_INTERVAL_SEPARATION * interval_size
                and p_a_other != p_a
            ]
            if len(nearby_peaks_counts) < 1 or p_c == max([p_c, *nearby_peaks_counts]):
                filtered_peaks.append((p_a, p_c))
        # Add a new entry to the list
        peaks_in_seg = filtered_peaks
        seg_min_angle = min(p[0] for p in peaks_in_seg) - 0.5 * neighborhood_size
        seg_max_angle = max(p[0] for p in peaks_in_seg) + 0.5 * neighborhood_size
        peak_segments.append(
            {
                "min": seg_min_angle,
                "max": seg_max_angle,
                "peak_angles": [p[0] for p in peaks_in_seg],
                "peak_counts": [p[1] for p in peaks_in_seg],
            }
        )
    return peak_segments


# The minimum peak height
MIN_PEAK_HEIGHT = 10
# Peaks cannot have sigma wider than this scale factor times the segment length
MAX_SIGMA_SCALE_FACTOR = 0.7
# Minimum peak sigma
MIN_SIGMA = 0.02


def get_segment_peak_fit(xrd_df, peak_seg):
    """Return the result of a model fit to a given segment of XRD data. The model is
    made up of some linear background combined with a number of pseudo-Voigt
    distributions, one for each peak originally found in the segment. Fitting is
    performed using the "lmfit" package.

    Args:
        xrd_df (pandas.DataFrame): The dataframe of the XRD dataset with "angle"
            and "count" columns (can be an entire dataset or truncated to the
            segment of interest)
        peak_seg (dict): The "peak segment" dictionary (from get_peak_segments) to fit
            the model to

    Returns:
        The result of the fit to the data (as a lmfit.model.ModelResult object)
    """
    # Truncate the dataframe to be within the angles of the segment
    seg_df = xrd_df[
        ((xrd_df["angle"] >= peak_seg["min"]) & (xrd_df["angle"] <= peak_seg["max"]))
    ]
    # Start the Model with some linear background
    model = lmfit.models.LinearModel(prefix="linear_")
    make_params_kwargs = {
        "linear_slope": -0.01,
        "linear_intercept": 0,
    }
    # Add a pseudo-Voigt for each peak in the segment
    for i_p, (seg_peak_angle, seg_peak_counts) in enumerate(
        zip(peak_seg["peak_angles"], peak_seg["peak_counts"])
    ):
        model += lmfit.models.PseudoVoigtModel(prefix=f"voigt_{i_p}_")
        make_params_kwargs[f"voigt_{i_p}_amplitude"] = seg_peak_counts
        make_params_kwargs[f"voigt_{i_p}_center"] = seg_peak_angle
        make_params_kwargs[f"voigt_{i_p}_sigma"] = 0.05
        make_params_kwargs[f"voigt_{i_p}_gamma"] = 1
    # Make the parameters object and perform the fit
    params = model.make_params(**make_params_kwargs)
    result = model.fit(seg_df["counts"], params, x=seg_df["angle"])
    # Iteratively filter out invalid peak components
    last_valid_components = None
    valid_components = []
    while last_valid_components is None or valid_components != last_valid_components:
        last_valid_components = valid_components
        for component in result.model.components:
            # keep the linear background no matter what
            if not component.prefix.startswith("voigt"):
                valid_components.append(component)
                continue
            height_value = result.params[f"{component.prefix}height"].value
            center_value = result.params[f"{component.prefix}center"].value
            sigma_value = result.params[f"{component.prefix}sigma"].value
            is_valid = True
            # filter out anything within 1 sigma of another, taller peak
            for other_component in result.model.components:
                if (
                    not other_component.prefix.startswith("voigt")
                ) or other_component == component:
                    continue
                if (
                    abs(
                        center_value
                        - result.params[f"{other_component.prefix}center"].value
                    )
                    / sigma_value
                    < 1
                    and height_value
                    < result.params[f"{other_component.prefix}height"].value
                ):
                    is_valid = False
            # make some requirements about the height, center location, and sigma
            if (
                height_value < MIN_PEAK_HEIGHT
                or center_value < peak_seg["min"]
                or center_value > peak_seg["max"]
                or sigma_value
                > MAX_SIGMA_SCALE_FACTOR
                * (np.max(seg_df["angle"]) - np.min(seg_df["angle"]))
                or sigma_value < MIN_SIGMA
            ):
                is_valid = False
            if is_valid:
                valid_components.append(component)
        new_model = valid_components[0]
        for comp in valid_components[1:]:
            new_model = new_model + comp
        result = new_model.fit(seg_df["counts"], params, x=seg_df["angle"])
    return result
