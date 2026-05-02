from io import StringIO
import pandas as pd
import requests


class Fetchers:
    
    @staticmethod
    def fetch_cammesa(start='2020-01-01'):
        url = ("https://cammesaweb.cammesa.com/despacho/nvst/descarga_consumo"
            f"?fechaDesde={start}&tipo=diario&formato=csv")
        r = requests.get(url, timeout=30); r.raise_for_status()
        cam = pd.read_csv(StringIO(r.text), sep=';', decimal=',')
        cam['fecha'] = pd.to_datetime(cam['FECHA'])
        return (cam.groupby('fecha')['CONSUMO TOTAL GWh']
                .sum().rename('gwh').to_frame())

    @staticmethod
    def fetch_sube():
        api = ("https://datos.transporte.gob.ar/api/3/action/package_show"
            "?id=sube-cantidad-de-transacciones-usos-por-fecha")
        resources = requests.get(api, timeout=30).json()['result']['resources']
        csv_urls = [r['url'] for r in resources if r['format'].lower() == 'csv']
        frames = []
        for url in csv_urls:
            df = pd.read_csv(url)
            df['fecha'] = pd.to_datetime(df['fecha'])
            frames.append(df[['fecha', 'cantidad_transacciones']])
        sube = (pd.concat(frames)
                .groupby('fecha')['cantidad_transacciones']
                .sum().rename('viajes_sube')
                .to_frame()
                .sort_index())
        return sube

    @staticmethod
    def fetch_bcra(series="base_monetaria"):
        token = "TU_TOKEN_BCRA"  # sacalo gratis en estadisticasbcra.com
        url = f"https://api.estadisticasbcra.com/{series}"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        r.raise_for_status()
        s = pd.read_json(StringIO(r.text))
        s['d'] = pd.to_datetime(s['d'])
        return s.set_index('d').rename(columns={'v': series})

    @staticmethod
    def fetch_ccl(start='2020-01-01'):
        adr = yf.download('GGAL', start=start, progress=False)['Adj Close'] # type: ignore
        loc = yf.download('GGAL.BA', start=start, progress=False)['Adj Close'] # type: ignore
        return (adr * 10 / loc).rename('ccl_ggal').to_frame()
    
    @staticmethod
    def fetch_soybeans():
        url = "https://stooq.com/q/d/l/?s=zs=F&i=d"
        soy = pd.read_csv(url)
        soy['Date'] = pd.to_datetime(soy['Date'])
        return soy.set_index('Date')['Close'].rename('soy_usd').to_frame()

    @staticmethod
    def fetch_emae():
        url = ("https://infra.datos.gob.ar/catalog/indec/dataset/62/"
            "download/serie_tiempo/62.4_0.csv")
        emae = pd.read_csv(url)
        emae['fecha'] = pd.to_datetime(emae['indice_tiempo'])
        return emae.set_index('fecha')['valor'].rename('emae')
    
    @staticmethod
    def fetch_mobility_report():

        url = "https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv"
        df = pd.read_csv(url)

        arg = df[(df["country_region"] == "Argentina") & (df["sub_region_1"].isna())]
        arg["date"] = pd.to_datetime(arg["date"])

        return arg.set_index("date")