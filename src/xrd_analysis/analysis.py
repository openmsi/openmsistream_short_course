" Data-crunching functions for the example XRD analysis "

# imports
import numpy as np
import scipy
import lmfit
from utils import get_angle_interval_size

# The minimum distance between peaks (in intervals)
MIN_N_INTERVAL_SEPARATION = 5
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
        prominence=np.std(xrd_df["counts"]),
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
        make_params_kwargs[f"voigt_{i_p}_sigma"] = 0.1 * (
            np.max(seg_df["angle"]) - np.min(seg_df["angle"])
        )
        make_params_kwargs[f"voigt_{i_p}_gamma"] = 1
    # Make the parameters object and perform the fit
    params = model.make_params(**make_params_kwargs)
    # for i_p in range(len(peak_seg["peak_angles"])):
    #     params[f"voigt_{i_p}_amplitude"].min = 0
    #     params[f"voigt_{i_p}_center"].min = np.min(seg_df["angle"])
    #     params[f"voigt_{i_p}_center"].max = np.max(seg_df["angle"])
    result = model.fit(seg_df["counts"], params, x=seg_df["angle"])
    return result
