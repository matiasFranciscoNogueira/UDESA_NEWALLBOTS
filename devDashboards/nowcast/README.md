#### Build docker 

```bash
docker build -t nowcast-dashboard .
```

#### Ejecutar el contenedor
```bash
docker run -d --name nowcast-dashboard -p 8060:8060 --restart unless-stopped -v "$(pwd)/data:/app/data" nowcast-dashboard
```

#### tunnel ngrok

ngrok http 8060