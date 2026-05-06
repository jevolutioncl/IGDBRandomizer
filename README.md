# IGDB Randomizer

Un script en Python que utiliza la API de IGDB para seleccionar aleatoriamente videojuegos de cualquier plataforma, con filtros opcionales por año y rating.

## Requisitos

- Python 3.10 o superior
- Una cuenta en [Twitch Developer Console](https://dev.twitch.tv/console) para obtener las credenciales de la API de IGDB

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/jevolutioncl/IGDBRandomizer.git
   cd IGDBRandomizer
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Crea el archivo `.env` a partir de la plantilla:
   ```bash
   cp .env.example .env
   ```

4. Edita `.env` con tus credenciales de IGDB:
   ```
   IGDB_CLIENT_ID=tu_client_id
   IGDB_ACCESS_TOKEN=tu_access_token
   IGDB_CLIENT_SECRET=tu_client_secret
   ```

## Obtener credenciales

1. Accede a [dev.twitch.tv/console](https://dev.twitch.tv/console) e inicia sesión con tu cuenta de Twitch.
2. Crea una nueva aplicación y copia el **Client ID** y el **Client Secret**.
3. Ejecuta el script auxiliar para generar un Access Token:
   ```bash
   python generate_igdb_token.py
   ```
4. Copia el `access_token` generado y agrégalo a tu `.env`.

## Uso

```bash
python IGDBRandomizer.py
```

El script te pedirá:

1. **Plataforma** — escribe el nombre (ej: `PC`, `PlayStation 5`, `Nintendo Switch`) y selecciona de la lista.
2. **Cantidad de juegos** — cuántos juegos aleatorios quieres generar.
3. **Año de lanzamiento** *(opcional)* — filtra por año (ej: `2020`).
4. **Rating mínimo** *(opcional)* — filtra por puntuación mínima de 0 a 100.

Al finalizar, podrás seleccionar uno o varios juegos de la lista para abrir su página en IGDB directamente en el navegador. Los juegos elegidos se guardan en `games.txt`.

## Archivos

| Archivo | Descripción |
|---|---|
| `IGDBRandomizer.py` | Script principal |
| `generate_igdb_token.py` | Genera un Access Token usando Client ID y Client Secret |
| `.env.example` | Plantilla de variables de entorno (copia a `.env` y completa) |
| `requirements.txt` | Dependencias de Python |
| `games.txt` | Historial de juegos seleccionados (generado al ejecutar, no incluido en el repo) |
