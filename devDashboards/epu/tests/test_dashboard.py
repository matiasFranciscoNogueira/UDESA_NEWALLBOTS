"""Tests for the Dash callback in src/main.py.

We monkeypatch RESULTS_DB to point at a temporary SQLite so the callback
can run without the real data file being present.
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import write_table


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EPU_COLUMNS = ["fecha", "Trade", "Monetary Policy", "Fiscal", "Currency crises", "EPU UdeSA"]


def _make_data_df(n=12) -> pd.DataFrame:
    dates = pd.date_range("2022-01-31", periods=n, freq="ME").strftime("%Y-%m-%d")
    import numpy as np
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "fecha": dates,
        "Trade": rng.uniform(50, 200, n),
        "Monetary Policy": rng.uniform(50, 200, n),
        "Fiscal": rng.uniform(50, 200, n),
        "Currency crises": rng.uniform(50, 200, n),
        "EPU UdeSA": rng.uniform(50, 200, n),
    })


def _make_benchmark_df(n=12) -> pd.DataFrame:
    dates = pd.date_range("2022-01-31", periods=n, freq="ME").strftime("%Y-%m-%d")
    import numpy as np
    rng = np.random.default_rng(1)
    return pd.DataFrame({
        "fecha": dates,
        "EPU_ARG_local": rng.uniform(50, 200, n),
    })


@pytest.fixture
def populated_db(tmp_path):
    db = tmp_path / "database.sqlite"
    write_table(_make_data_df(), "data", db_path=db)
    write_table(_make_benchmark_df(), "benchmark", db_path=db)
    return db


# ---------------------------------------------------------------------------
# update_graph callback
# ---------------------------------------------------------------------------

class TestUpdateGraph:
    def test_returns_figure(self, populated_db, monkeypatch):
        import src.main as main_module
        monkeypatch.setattr(main_module, "RESULTS_DB", populated_db)
        fig = main_module.update_graph(0)
        assert isinstance(fig, go.Figure)

    def test_figure_has_traces(self, populated_db, monkeypatch):
        import src.main as main_module
        monkeypatch.setattr(main_module, "RESULTS_DB", populated_db)
        fig = main_module.update_graph(0)
        assert len(fig.data) > 0

    def test_figure_has_one_trace_per_epu_column_plus_benchmark(self, populated_db, monkeypatch):
        import src.main as main_module
        monkeypatch.setattr(main_module, "RESULTS_DB", populated_db)
        fig = main_module.update_graph(0)
        # 5 EPU columns + 1 Ghirelli benchmark trace
        assert len(fig.data) == 6

    def test_benchmark_trace_is_dashed(self, populated_db, monkeypatch):
        import src.main as main_module
        monkeypatch.setattr(main_module, "RESULTS_DB", populated_db)
        fig = main_module.update_graph(0)
        benchmark_trace = fig.data[-1]
        assert benchmark_trace.line.dash == "dash"

    def test_callback_is_stable_across_intervals(self, populated_db, monkeypatch):
        """Calling with different n_intervals values should produce the same figure shape."""
        import src.main as main_module
        monkeypatch.setattr(main_module, "RESULTS_DB", populated_db)
        fig0 = main_module.update_graph(0)
        fig5 = main_module.update_graph(5)
        assert len(fig0.data) == len(fig5.data)
