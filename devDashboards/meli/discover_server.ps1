# discover_server.ps1 - Inventario de la infraestructura del dashboard MELI.
# Solo LEE (docker ps/inspect, nginx -T, API local de ngrok). No cambia nada.
#
# Uso en el server (PowerShell):
#   cd <carpeta con este archivo>
#   powershell -ExecutionPolicy Bypass -File .\discover_server.ps1 > discovery.txt
#   # y pasar discovery.txt para armar los comandos exactos de deploy.

$ErrorActionPreference = "Continue"

function Section($t) { ""; "=" * 78; "== $t"; "=" * 78 }

Section "Host"
$PSVersionTable.PSVersion.ToString()
[System.Environment]::OSVersion.VersionString
"Usuario: $env:USERNAME   Carpeta actual: $(Get-Location)"

Section "Docker"
docker version --format "cliente={{.Client.Version}} server={{.Server.Version}} os={{.Server.Os}}"
docker compose version

Section "Contenedores (todos)"
docker ps -a --format "table {{.Names}}`t{{.Image}}`t{{.Status}}`t{{.Ports}}"

Section "Imagenes"
docker images --format "table {{.Repository}}`t{{.Tag}}`t{{.ID}}`t{{.CreatedAt}}`t{{.Size}}"

Section "Proyectos docker compose"
docker compose ls -a

Section "Redes docker"
docker network ls

Section "Detalle por contenedor (imagen, comando, puertos, mounts, redes, labels de compose)"
$ids = docker ps -a -q
foreach ($id in $ids) {
    docker inspect $id --format '
--- {{.Name}} ---
  image      : {{.Config.Image}}
  cmd        : {{json .Config.Cmd}}
  workdir    : {{.Config.WorkingDir}}
  restart    : {{.HostConfig.RestartPolicy.Name}}
  ports      : {{json .HostConfig.PortBindings}}
  mounts     : {{json .Mounts}}
  networks   : {{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}
  compose    : project={{index .Config.Labels "com.docker.compose.project"}} service={{index .Config.Labels "com.docker.compose.service"}}
  compose dir: {{index .Config.Labels "com.docker.compose.project.working_dir"}}
  compose cfg: {{index .Config.Labels "com.docker.compose.project.config_files"}}'
}

Section "nginx: configuracion efectiva (solo directivas de ruteo)"
$nginxNames = docker ps --format "{{.Names}} {{.Image}}" | Where-Object { $_ -match "nginx" } | ForEach-Object { ($_ -split " ")[0] }
if (-not $nginxNames) { "No se encontro un contenedor con imagen nginx. Buscar nginx instalado en el host (nginx -T) o en la config de ngrok." }
foreach ($n in $nginxNames) {
    "--- contenedor nginx: $n ---"
    docker exec $n nginx -T | Select-String -Pattern "server_name|listen|location|proxy_pass|upstream|rewrite|alias|root |try_files|return|include"
}

Section "ngrok"
"Procesos ngrok en el host:"
Get-Process ngrok -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path | Format-Table -AutoSize
"Contenedores ngrok:"
docker ps -a --format "{{.Names}} {{.Image}} {{.Status}}" | Where-Object { $_ -match "ngrok" }
"Tuneles activos (API local 4040):"
try {
    $t = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
    $t.tunnels | Select-Object name, public_url, @{ n = "addr"; e = { $_.config.addr } } | Format-Table -AutoSize
} catch { "  (la API 4040 no responde en el host: ngrok corre en contenedor o con otra config)" }
"Config de ngrok en el perfil del usuario:"
$cfgs = @("$env:LOCALAPPDATA\ngrok\ngrok.yml", "$env:USERPROFILE\.ngrok2\ngrok.yml", "$env:APPDATA\ngrok\ngrok.yml")
foreach ($c in $cfgs) { if (Test-Path $c) { "  $c"; Get-Content $c | Where-Object { $_ -notmatch "authtoken" } } }

Section "Servicios y tareas programadas relacionadas"
Get-Service | Where-Object { $_.Name -match "ngrok|docker|nginx" } | Select-Object Name, Status, StartType | Format-Table -AutoSize
Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -match "ngrok|docker|meli|nginx" } | Select-Object TaskName, State | Format-Table -AutoSize

Section "Archivos de infraestructura cercanos (compose / nginx / ngrok) - hasta 4 niveles desde la carpeta padre"
$root = Split-Path -Parent (Get-Location)
Get-ChildItem -Path $root -Recurse -Depth 4 -ErrorAction SilentlyContinue -Include docker-compose.yml, docker-compose.yaml, compose.yml, compose.yaml, nginx.conf, default.conf, ngrok.yml, *.ps1, *.sh, *.bat |
    Where-Object { $_.FullName -notmatch "\\node_modules\\|\\.venv\\|\\older\\" } |
    Select-Object FullName, LastWriteTime | Format-Table -AutoSize

""
"FIN. Pegar este archivo completo para armar los comandos exactos de deploy."
