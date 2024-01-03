" Plotting functions for the example XRD analysis "

# imports
import pathlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def plot_peak_segments(xrd_df, peak_segments, save=None):
    """Make a plot showing a full XRD dataset with the peak locations indicated,
    colored by their segments.

    Args:
        xrd_df (pandas.DataFrame): The dataframe of the entire XRD dataset with "angle"
            and "count" columns
        peak_segments (list): The list of "peak segment" dictionaries
            (from get_peak_segments)
        save (pathlib.Path, optional): The path to a file where the plot should be
            written out. If not given, the plot will be displayed instead.
    """
    color_names = list(mcolors.TABLEAU_COLORS.keys())
    _, ax = plt.subplots(figsize=(8.0, 4.0))
    ax.plot(xrd_df["angle"], xrd_df["counts"], color="black")
    for i_seg, peak_segment in enumerate(peak_segments):
        color = color_names[i_seg % (len(color_names) - 1)]
        ax.axvline(
            peak_segment["min"], color=color, linewidth=1, ymax=0.6, linestyle="--"
        )
        ax.axvline(
            peak_segment["max"], color=color, linewidth=1, ymax=0.6, linestyle="--"
        )
        for peak_angle in peak_segment["peak_angles"]:
            ax.axvline(peak_angle, color=color, linewidth=1, ymax=0.8, alpha=0.7)
    ax.set_xlabel("angle")
    ax.set_ylabel("counts")
    if isinstance(save, pathlib.Path):
        if not save.parent.is_dir():
            save.parent.mkdir(parents=True)
        plt.savefig(save, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def plot_segment_peak_fit(seg_df, fit_result, save=None):
    """Make a plot of the fit to a particular segment of XRD data, showing the
    combined model fit as well as the background and peak components.

    Args:
        seg_df (pandas.DataFrame): The dataframe of the segment of the XRD data to plot
        fit_result (lmfit.model.ModelResult): The ModelResult object from the fit to the
            segment of XRD data
        save (pathlib.Path, optional): The path to a file where the plot should be
            written out. If not given, the plot will be displayed instead.
    """
    _, ax = plt.subplots(figsize=(8.0, 4.0))
    ax.plot(seg_df["angle"], fit_result.best_fit, label="model fit")
    ax.plot(
        seg_df["angle"],
        fit_result.eval_components()["linear_"],
        label="background",
        linestyle="--",
    )
    peak_comp_prefixes = sorted(
        [m.prefix for m in fit_result.model.components if m.prefix.startswith("voigt")]
    )
    for peak_comp_prefix in peak_comp_prefixes:
        peak_i = int(peak_comp_prefix.split("_")[1])
        label = (
            f"peak {peak_i+1} "
            f"($\\mu$ = {fit_result.params[f'{peak_comp_prefix}center'].value:.2f}, "
            f"$\\sigma$ = {fit_result.params[f'{peak_comp_prefix}sigma'].value:.2f})"
        )
        ax.plot(
            seg_df["angle"],
            fit_result.eval_components()[peak_comp_prefix],
            label=label,
            linestyle="--",
        )
    ax.plot(
        seg_df["angle"],
        seg_df["counts"],
        color="black",
        marker=".",
        linestyle="None",
        label="data",
    )
    ax.set_xlabel("angle")
    ax.set_ylabel("counts")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    if isinstance(save, pathlib.Path):
        if not save.parent.is_dir():
            save.parent.mkdir(parents=True)
        plt.savefig(save, bbox_inches="tight")
        plt.close()
    else:
        plt.show()
