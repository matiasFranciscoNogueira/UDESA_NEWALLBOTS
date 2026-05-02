
## Arquitectura multi-contenedor (desarrollo avanzado)

Para un setup con un contenedor **writer** (genera DB) y otro **reader** (dashboard):
1. Crear un `docker-compose.yml` con servicios separados
2. Usar un volumen compartido para `data/database.sqlite`
3. El writer importa Excel → sqlite una vez al iniciar
4. El reader (este código) lee continuamente de la DB

Esto será necesario para la arquitectura final en la VM con múltiples escritores/lectores.
