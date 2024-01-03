" Table definitions for the example XRD analysis database "

# imports
from sqlalchemy import Integer, Float, String, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class ORMBase(DeclarativeBase):
    pass


class DataSet(ORMBase):
    """A background-subtracted XRD dataset with a corresponding file"""

    __tablename__ = "datasets"

    ID = mapped_column(Integer, primary_key=True)
    file_name = mapped_column(String(500), unique=True)
    raw_file_name = mapped_column(String(500), unique=True)


class DataPoint(ORMBase):
    """A single point (angle/counts) in a background-subtracted XRD dataset"""

    __tablename__ = "datapoints"

    ID = mapped_column(Integer, primary_key=True)
    dataset_id = mapped_column(ForeignKey(f"{DataSet.__tablename__}.ID"))
    angle = mapped_column(Float)
    counts = mapped_column(Float)

    datapoint_dataset_relation = relationship(
        f"{DataSet.__name__}", foreign_keys="DataPoint.dataset_id"
    )


class DataSegment(ORMBase):
    """A segment of XRD data containing one or more candidate peaks"""

    __tablename__ = "segments"

    ID = mapped_column(Integer, primary_key=True)
    dataset_id = mapped_column(ForeignKey(f"{DataSet.__tablename__}.ID"))
    min_angle = mapped_column(Float)
    max_angle = mapped_column(Float)

    segment_dataset_relation = relationship(
        f"{DataSet.__name__}", foreign_keys="DataSegment.dataset_id"
    )


class CandidatePeak(ORMBase):
    """The location (angle) of a candidate peak determined from simple peak finding"""

    __tablename__ = "candidate_peaks"

    ID = mapped_column(Integer, primary_key=True)
    segment_id = mapped_column(ForeignKey(f"{DataSegment.__tablename__}.ID"))
    angle = mapped_column(Float)

    candidate_peak_segment_relation = relationship(
        f"{DataSegment.__name__}", foreign_keys="CandidatePeak.segment_id"
    )


class SegmentFit(ORMBase):
    """Details about the result of a fit to a segment of background-subtracted XRD data"""

    __tablename__ = "segment_fits"

    ID = mapped_column(Integer, primary_key=True)
    segment_id = mapped_column(ForeignKey(f"{DataSegment.__tablename__}.ID"))
    method = mapped_column(String(100))
    ndata = mapped_column(Integer)
    chisqr = mapped_column(Float)
    redchi = mapped_column(Float)
    rsquared = mapped_column(Float)
    nfev = mapped_column(Integer)
    aborted = mapped_column(Boolean)
    success = mapped_column(Boolean)
    message = mapped_column(String(500))

    fit_segment_relation = relationship(
        f"{DataSegment.__name__}", foreign_keys="SegmentFit.segment_id"
    )


class Background(ORMBase):
    """Parameters for a background fit in a segment of XRD data"""

    __tablename__ = "backgrounds"

    ID = mapped_column(Integer, primary_key=True)
    segment_id = mapped_column(ForeignKey(f"{DataSegment.__tablename__}.ID"))
    init_slope = mapped_column(Float)
    init_intercept = mapped_column(Float)
    fitted_slope = mapped_column(Float)
    fitted_intercept = mapped_column(Float)
    slope_stderr = mapped_column(Float)
    intercept_stderr = mapped_column(Float)

    background_segment_relation = relationship(
        f"{DataSegment.__name__}", foreign_keys="Background.segment_id"
    )


class FittedPeak(ORMBase):
    """Parameters for a pseudo-Voigt peak in a segment of XRD data"""

    __tablename__ = "fitted_peaks"

    ID = mapped_column(Integer, primary_key=True)
    segment_id = mapped_column(ForeignKey(f"{DataSegment.__tablename__}.ID"))
    init_amplitude = mapped_column(Float)
    init_center = mapped_column(Float)
    init_sigma = mapped_column(Float)
    init_fraction = mapped_column(Float)
    fitted_amplitude = mapped_column(Float)
    fitted_center = mapped_column(Float)
    fitted_sigma = mapped_column(Float)
    fitted_fwhm = mapped_column(Float)
    fitted_fraction = mapped_column(Float)
    amplitude_stderr = mapped_column(Float)
    center_stderr = mapped_column(Float)
    sigma_stderr = mapped_column(Float)
    fraction_stderr = mapped_column(Float)

    peak_segment_relation = relationship(
        f"{DataSegment.__name__}", foreign_keys="FittedPeak.segment_id"
    )
