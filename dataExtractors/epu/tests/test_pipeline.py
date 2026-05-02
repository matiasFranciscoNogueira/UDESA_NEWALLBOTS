"""Integration / pipeline tests for the EPU monthly calculation.

These tests exercise the full EPU computation path without touching BigQuery
or the filesystem. They build synthetic DataFrames that mimic the raw CSV
produced by epu_historical_GDELT_big_query.py and verify that the final
index behaves as expected.

NOTE — known production bug (process_tone_monthly=True path):
    get_epu_and_resample_from_daily_selector() passes 6 arguments to the
    private __get_epu_and_resample_from_daily_montlhy_tone_process() which
    only accepts 5. Tests for this path are marked xfail.
    The production workflow uses process_tone_monthly=False (the daily-tone
    path), so this bug has no current impact on results.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from Helpers.analisys_helpers import (
    get_epu_and_resample_from_daily_selector,
    get_epu_by_media_and_resample_from_daily,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TONE_STR = "-1.5,2.0,3.0,0.5,4.0,1.0,"
MEDIOS = ["clarin", "lanacion", "infobae"]


def _build_raw_df(
    start="2022-01-01",
    periods=365,
    medios=None,
    seed=0,
) -> pd.DataFrame:
    """Build a synthetic raw daily DataFrame with the same shape as the real CSVs."""
    if medios is None:
        medios = MEDIOS

    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=periods, freq="D")

    rows = []
    for date in dates:
        for medio in medios:
            rows.append({
                "fecha": date,
                "medio": medio,
                "matches": int(rng.integers(1, 30)),
                "total": int(rng.integers(50, 300)),
                "tono": TONE_STR,
            })

    df = pd.DataFrame(rows).set_index("fecha")
    return df


# ---------------------------------------------------------------------------
# Production path: process_tone_monthly=False (daily-tone path)
# ---------------------------------------------------------------------------

class TestEpuDailyTonePath:
    """Tests for the active production path (process_tone_monthly=False)."""

    def test_returns_dataframe(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=False)
        assert isinstance(result, pd.DataFrame)

    def test_has_epu_udesa_column(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=False)
        assert "EPU UdeSA" in result.columns

    def test_has_proportion_columns(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=False)
        assert "positive_proportion" in result.columns
        assert "negative_proportion" in result.columns
        assert "neutral_proportion" in result.columns

    def test_monthly_rows_match_input_months(self):
        df = _build_raw_df(start="2022-01-01", periods=365)
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=False)
        assert len(result) == 12

    def test_epu_index_is_positive(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=False)
        assert (result["EPU UdeSA"] >= 0).all()

    def test_index_is_datetime(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=False)
        assert isinstance(result.index, pd.DatetimeIndex)


# ---------------------------------------------------------------------------
# Monthly tone path (process_tone_monthly=True) — currently broken
# Bug: selector passes 6 args to internal function that accepts only 5.
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known bug: get_epu_and_resample_from_daily_selector passes 6 args "
        "to __get_epu_and_resample_from_daily_montlhy_tone_process which "
        "only accepts 5. Fix by removing the extra process_tone_monthly arg "
        "from the internal call at analisys_helpers.py:7."
    ),
)
class TestEpuMonthlyTonePathKnownBug:
    """These tests document the expected behaviour once the bug is fixed."""

    def test_returns_dataframe(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=True)
        assert isinstance(result, pd.DataFrame)

    def test_has_epu_index_column(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=True)
        assert "epu_index" in result.columns

    def test_epu_index_mean_approx_100(self):
        df = _build_raw_df()
        result = get_epu_and_resample_from_daily_selector(df, freq="M", process_tone_monthly=True)
        assert result["epu_index"].mean() == pytest.approx(100.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Media exclusion (daily-tone path)
# ---------------------------------------------------------------------------

class TestMediaExclusion:
    def test_excluding_one_medio_still_produces_monthly_output(self):
        df = _build_raw_df(medios=MEDIOS)
        result = get_epu_and_resample_from_daily_selector(
            df, freq="M", process_tone_monthly=False, exclude_medios=["clarin"]
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_excluding_changes_index_values(self):
        """Removing a media outlet should produce a different EPU series."""
        df = _build_raw_df(medios=MEDIOS)
        result_full = get_epu_and_resample_from_daily_selector(
            df, freq="M", process_tone_monthly=False, exclude_medios=[]
        )
        result_excl = get_epu_and_resample_from_daily_selector(
            df, freq="M", process_tone_monthly=False, exclude_medios=["clarin"]
        )
        assert not result_full["EPU UdeSA"].equals(result_excl["EPU UdeSA"])


# ---------------------------------------------------------------------------
# Per-media EPU
# ---------------------------------------------------------------------------

class TestEpuByMedia:
    def test_returns_dataframe(self):
        df = _build_raw_df(medios=["clarin", "lanacion"])
        result = get_epu_by_media_and_resample_from_daily(df, freq="M")
        assert isinstance(result, pd.DataFrame)

    def test_one_column_per_medio(self):
        df = _build_raw_df(medios=["clarin", "lanacion"])
        result = get_epu_by_media_and_resample_from_daily(df, freq="M")
        assert any("clarin" in col for col in result.columns)
        assert any("lanacion" in col for col in result.columns)

    def test_each_series_mean_approx_100(self):
        df = _build_raw_df(medios=["clarin", "lanacion"])
        result = get_epu_by_media_and_resample_from_daily(df, freq="M")
        for col in result.columns:
            assert result[col].mean() == pytest.approx(100.0, rel=1e-6)
