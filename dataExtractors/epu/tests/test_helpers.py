"""Unit tests for EPU-ARG helper modules."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make src importable without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from Helpers.analisys_helpers import process_tone, get_counts, get_epu_by_media_and_resample_from_daily
from Helpers.epu_categories_type import EPUCategoriesType
from Helpers.gdelt_request_helpers import (
    concat_raw_with_updated_dfs,
    get_sql,
    set_epu_files_names,
)


# ---------------------------------------------------------------------------
# process_tone
# ---------------------------------------------------------------------------

class TestProcessTone:
    def test_valid_tone_string(self):
        result = process_tone("-1.5,2.3,3.1,0.8,4.2,1.0,")
        assert isinstance(result, list)
        assert result[0] == pytest.approx(-1.5)
        assert result[1] == pytest.approx(2.3)

    def test_nan_input_returns_nan(self):
        result = process_tone(float("nan"))
        assert result is np.nan

    def test_non_string_input_returns_nan(self):
        result = process_tone(None)
        assert result is np.nan

    def test_no_comma_returns_nan_list(self):
        # split(',') returns length-1 list → triggers the < 2 guard
        result = process_tone("-1.5")
        assert result == [np.nan] * 6

    def test_empty_string_returns_nan_list(self):
        # split(',') on "" returns [""], length 1 → [nan]*6
        result = process_tone("")
        assert result == [np.nan] * 6


# ---------------------------------------------------------------------------
# EPUCategoriesType enum
# ---------------------------------------------------------------------------

class TestEPUCategoriesType:
    def test_all_values(self):
        values = {e.value for e in EPUCategoriesType}
        assert values == {"none", "trade", "fiscal", "monetary_policy", "currency_crisis"}

    def test_none_member(self):
        assert EPUCategoriesType.NONE.value == "none"

    def test_trade_member(self):
        assert EPUCategoriesType.TRADE.value == "trade"

    def test_enum_count(self):
        assert len(EPUCategoriesType) == 5


# ---------------------------------------------------------------------------
# concat_raw_with_updated_dfs
# ---------------------------------------------------------------------------

def _make_df(dates, medio="clarin", matches=10, total=100, tono="-1.5,2.0,3.0,0.5,4.0,1.0,"):
    idx = pd.to_datetime(dates)
    return pd.DataFrame({
        "medio": medio,
        "matches": matches,
        "total": total,
        "tono": tono,
    }, index=idx)


class TestConcatRawWithUpdatedDfs:
    def test_empty_new_returns_raw(self):
        raw = _make_df(["2023-01-01", "2023-01-02"])
        new = pd.DataFrame()
        result = concat_raw_with_updated_dfs(raw, new)
        assert len(result) == 2

    def test_concat_sorts_by_date(self):
        raw = _make_df(["2023-01-03"])
        new = _make_df(["2023-01-01"])
        result = concat_raw_with_updated_dfs(raw, new)
        assert result.index[0] < result.index[1]

    def test_concat_preserves_all_rows(self):
        raw = _make_df(["2023-01-01", "2023-01-02"])
        new = _make_df(["2023-01-03", "2023-01-04"])
        result = concat_raw_with_updated_dfs(raw, new)
        assert len(result) == 4


# ---------------------------------------------------------------------------
# set_epu_files_names
# ---------------------------------------------------------------------------

class TestSetEpuFilesNames:
    def test_main_category_filename(self):
        name, _ = set_epu_files_names(
            "key_words_gdelt_maped_jp.json",
            ["clarin.com"],
            Path("/project"),
            "Argentina",
            is_sub_category=False,
        )
        assert name == "epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv"

    def test_subcategory_goes_into_subcategories_folder(self):
        _, store_dir = set_epu_files_names(
            "key_words_gdelt_maped_jp_trade.json",
            ["clarin.com"],
            Path("/project"),
            "Argentina",
            is_sub_category=True,
        )
        assert "subcategories" in str(store_dir)

    def test_main_category_does_not_include_subcategories_folder(self):
        _, store_dir = set_epu_files_names(
            "key_words_gdelt_maped_jp.json",
            ["clarin.com"],
            Path("/project"),
            "Argentina",
            is_sub_category=False,
        )
        assert "subcategories" not in str(store_dir)

    def test_non_default_country_adds_countries_folder(self):
        _, store_dir = set_epu_files_names(
            "key_words.json",
            ["lemonde.fr"],
            Path("/project"),
            "France",
            is_sub_category=False,
        )
        assert "countries" in str(store_dir)


# ---------------------------------------------------------------------------
# get_sql
# ---------------------------------------------------------------------------

class TestGetSql:
    KW_MAIN = {
        "E": ["EPU_ECONOMY"],
        "P": ["EPU_POLICY"],
        "U": ["EPU_UNCERTAINTY"],
    }
    KW_SUB = {
        "E": ["EPU_ECONOMY"],
        "P": ["EPU_POLICY"],
        "U": ["EPU_UNCERTAINTY"],
        "S": ["ECON_TRADE"],
    }
    MEDIA = ["clarin.com", "lanacion.com.ar"]
    import datetime as _dt
    FIRST = _dt.date(2023, 1, 1)
    LAST = _dt.date(2023, 1, 31)

    def test_returns_string(self):
        sql = get_sql(self.FIRST, self.LAST, self.KW_MAIN, self.MEDIA)
        assert isinstance(sql, str)

    def test_contains_date_range(self):
        sql = get_sql(self.FIRST, self.LAST, self.KW_MAIN, self.MEDIA)
        assert "2023-01-01" in sql
        assert "2023-01-31" in sql

    def test_main_sql_does_not_contain_s_pattern(self):
        sql = get_sql(self.FIRST, self.LAST, self.KW_MAIN, self.MEDIA)
        assert "ECON_TRADE" not in sql

    def test_subcategory_sql_contains_s_pattern(self):
        sql = get_sql(self.FIRST, self.LAST, self.KW_SUB, self.MEDIA)
        assert "ECON_TRADE" in sql

    def test_contains_all_epu_keyword_groups(self):
        sql = get_sql(self.FIRST, self.LAST, self.KW_MAIN, self.MEDIA)
        assert "EPU_ECONOMY" in sql
        assert "EPU_POLICY" in sql
        assert "EPU_UNCERTAINTY" in sql

    def test_contains_media_outlet(self):
        sql = get_sql(self.FIRST, self.LAST, self.KW_MAIN, self.MEDIA)
        assert "clarin" in sql.lower()


# ---------------------------------------------------------------------------
# get_counts
# ---------------------------------------------------------------------------

class TestGetCounts:
    def _sample_df(self):
        dates = pd.date_range("2023-01-01", periods=60, freq="D")
        rng = np.random.default_rng(42)
        medios = ["clarin", "lanacion"] * 30
        return pd.DataFrame({
            "medio": medios,
            "matches": rng.integers(1, 20, size=60),
            "total": rng.integers(50, 200, size=60),
            "tono": "-1.5,2.0,3.0,0.5,4.0,1.0,",
        }, index=dates)

    def test_returns_dataframe(self):
        df = self._sample_df()
        result = get_counts(df)
        assert isinstance(result, pd.DataFrame)

    def test_has_epu_std_column(self):
        df = self._sample_df()
        result = get_counts(df)
        assert "epu_std" in result.columns

    def test_monthly_frequency(self):
        df = self._sample_df()
        # "M" for to_period() — "ME" is resampling-only in this pandas version
        result = get_counts(df, freq="M")
        # date_range("2023-01-01", periods=60) spans Jan, Feb, and 1 day of March → 3 periods
        assert len(result) == 3
