# EPU Dashboard

## Instalación y ejecución

### Opción 1: Ejecución local (recomendada para desarrollo)

1. **Instalar Poetry** (si no lo tenes)
   ```
   pip install poetry
   ```
   **Para Linux se aconseja**:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```
   ### O seguir las instrucciones oficiales: https://python-poetry.org/docs/#installation.

2. **Instalar dependencias y activar el entorno virtual**
Pararse en el directorio del proyecto y correr:
```
poetry install --no-root
poetry shell
```

3. **Configurar para ejecución local**
Abrir el archivo src/main.py y asegurarse de que la variable esté así:
```
FROM_DOCKER = False
```

4. **Ejecutar la aplicación**

```
poetry run python src/main.py
```
La dashboard estará disponible en: http://localhost:8050
### Opción 2: Ejecución con Docker (recomendada para producción/VM)

Requiere tener Docker instalado y en ejecución.

#### 2.1 Preparar la base de datos (primera vez)
Antes de ejecutar Docker, asegúrate de que la base de datos sqlite existe:
```bash
poetry run python3 scripts/import_excel_to_sqlite.py
```
Esto genera `data/database.sqlite` a partir del Excel.

#### 2.2 Construir la imagen
```bash
docker build -t epu-dashboard .
```

#### 2.3 Ejecutar el contenedor
```bash
docker run -d --name epu-dashboard -p 8050:8050 --restart unless-stopped -v "$(pwd)/data:/app/data" epu-dashboard
```

La aplicación estará accesible en: http://localhost:8050

**Nota:** El flag `-v "$(pwd)/data:/app/data"` monta la carpeta `data/` local en el contenedor, permitiendo que:
- El contenedor lea `data/database.sqlite` (generado localmente)
- Cambios en la DB se reflejen sin necesidad de reconstruir la imagen

## Comandos útiles de Docker
```bash
# Detener el contenedor
docker stop epu-dashboard

# Iniciar nuevamente
docker start epu-dashboard

# Ver logs en tiempo real
docker logs -f epu-dashboard

# Eliminar contenedor e imagen (si necesitas reconstruir)
docker stop epu-dashboard
docker rm epu-dashboard
docker rmi epu-dashboard
```
