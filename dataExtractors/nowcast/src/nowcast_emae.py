import pandas as pd
import numpy as np
from sklearn.decomposition import PCA

from fetchers import Fetchers

def build_panel(start='2020-01-01'):
    dfs = [Fetchers.fetch_cammesa(start),
           Fetchers.fetch_sube(),
           Fetchers.fetch_bcra("base_monetaria"),
           Fetchers.fetch_ccl(start),
           Fetchers.fetch_soybeans()]
    panel = pd.concat(dfs, axis=1).sort_index()
    return panel.loc[panel.index >= pd.to_datetime(start)]

def compute_factor(df):
    g = df.pct_change().dropna()
    z = (g - g.mean()) / g.std()
    z['factor'] = PCA(n_components=1).fit_transform(z).ravel()
    return z['factor']

def nowcast_emae(start='2020-01-01'):
    panel = build_panel(start)
    factor_d = compute_factor(panel)
    factor_m = factor_d.resample('M').mean()

    emae = Fetchers.fetch_emae().loc[factor_m.index]
    y = emae.pct_change().dropna()
    x = factor_m.loc[y.index]

    beta = np.polyfit(x, y, 1)             # bridge lineal
    cur_month = factor_d.last('1M').mean()
    return beta[0]*cur_month + beta[1], panel

if __name__ == "__main__":
    now, df = nowcast_emae("2020-01-01")
    print(f"Nowcast EMAE mes en curso: {now:.2%}")
    print(df.tail())
