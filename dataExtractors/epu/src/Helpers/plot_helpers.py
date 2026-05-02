from matplotlib import pyplot as plt
import matplotlib.dates as mdates

def plot_epu_interactive(benchmark, region, dfs_monthly, renorm, dfs, span):
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=False)

    # Primer gráfico
    axes[0].plot(benchmark.index, benchmark[region], alpha=0.7, linestyle='--')
    axes[0].plot(dfs_monthly.index, dfs_monthly.values, label=f"Argentina renormalizado a {renorm}", linewidth=2)
    axes[0].set_title("EPU Argentina vs Benchmarks (GDELT)")
    axes[0].grid(True)
    axes[0].legend([*region, "BBD", "Ghirelli"], loc='upper left')

    # Eje X primer gráfico: ticks cada 6 meses
    axes[0].xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(axes[0].get_xticklabels(), rotation=45, ha='right')

    # Segundo gráfico
    axes[1].plot(dfs.index, dfs.ewm(span).mean(), label="media móvil exponencial", linewidth=2)
    axes[1].set_title("EPU Argentina daily (GDELT)")
    axes[1].legend()
    axes[1].grid(True)

    # Eje X segundo gráfico: ticks cada año para mayor limpieza
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(axes[1].get_xticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.show()

    return fig