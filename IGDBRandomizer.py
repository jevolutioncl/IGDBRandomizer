import datetime
import os
import random
import re
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv

load_dotenv()

# Configuracion
GAMES_URL = "https://api.igdb.com/v4/games"
COUNT_URL = "https://api.igdb.com/v4/games/count"
PLATFORMS_URL = "https://api.igdb.com/v4/platforms"
CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
ACCESS_TOKEN = os.environ["IGDB_ACCESS_TOKEN"]
RANDOM_GAMES_FILE = "games.txt"
REQUEST_TIMEOUT = 20
API_PAGE_SIZE = 200
MAX_WORKERS = 6


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    })
    return session


def parse_existing_ids(file_path: str) -> set[int]:
    """Lee el archivo historico y extrae IDs del formato '<id>. Nombre (...)'."""
    if not os.path.exists(file_path):
        return set()

    ids = set()
    encodings_to_try = ("utf-8", "cp1252", "latin-1")

    for encoding in encodings_to_try:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                for line in file:
                    match = re.match(r"^\s*(\d+)\.", line)
                    if match:
                        ids.add(int(match.group(1)))
            return ids
        except UnicodeDecodeError:
            ids.clear()
            continue

    return ids


def get_total_games(session: requests.Session, where_clause: str) -> int:
    response = session.post(
        COUNT_URL,
        data=f"{where_clause};",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict) or "count" not in payload:
        raise ValueError("Respuesta inesperada al consultar el total de juegos.")

    return int(payload["count"])


def format_release_date(timestamp: int | None) -> str:
    if not isinstance(timestamp, int):
        return "Fecha no disponible"
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).strftime("%Y-%m-%d")


def search_platforms(session: requests.Session, platform_name: str) -> list[dict]:
    escaped_name = platform_name.replace('"', '\\"')
    query = f"""
    fields id,name;
    search "{escaped_name}";
    limit 10;
    """
    response = session.post(
        PLATFORMS_URL,
        data=query,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else []


def build_where_clause(
    platform_id: int,
    release_year: int | None,
) -> str:
    filters = [f"platforms = ({platform_id})", "platforms != null"]

    if release_year is not None:
        start = int(datetime.datetime(release_year, 1, 1, tzinfo=datetime.timezone.utc).timestamp())
        end = int(datetime.datetime(release_year + 1, 1, 1, tzinfo=datetime.timezone.utc).timestamp())
        filters.append(f"first_release_date >= {start}")
        filters.append(f"first_release_date < {end}")

    return f"where {' & '.join(filters)}"


def get_games_batch(session: requests.Session, offset: int, limit: int, where_clause: str) -> list[dict]:
    query = f"""
    fields id,name,platforms.name,first_release_date,rating,total_rating,aggregated_rating,slug;
    {where_clause};
    sort id asc;
    limit {limit};
    offset {offset};
    """
    response = session.post(
        GAMES_URL,
        data=query,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else []


def pick_games(
    session: requests.Session,
    total_games: int,
    existing_ids: set[int],
    where_clause: str,
    requested_count: int,
    min_rating: float | None,
) -> list[tuple]:
    games = []
    selected_ids = set(existing_ids)
    page_limit = min(API_PAGE_SIZE, total_games)
    max_offset = max(total_games - page_limit, 0)

    # Pre-generar offsets unicos distribuidos aleatoriamente en el rango total.
    # random.sample sobre range() es eficiente: no materializa la lista completa.
    num_batches = max(requested_count * 2, MAX_WORKERS * 2)
    num_batches = min(num_batches, max_offset + 1) if max_offset > 0 else 1
    unique_offsets = random.sample(range(max_offset + 1), num_batches) if max_offset > 0 else [0]

    # Procesar en oleadas paralelas hasta tener suficientes juegos.
    offset_queue = list(unique_offsets)
    while len(games) < requested_count and offset_queue:
        wave = offset_queue[:MAX_WORKERS]
        offset_queue = offset_queue[MAX_WORKERS:]

        with ThreadPoolExecutor(max_workers=len(wave)) as executor:
            futures = {
                executor.submit(get_games_batch, session, offset, page_limit, where_clause): offset
                for offset in wave
            }

            for future in as_completed(futures):
                if len(games) >= requested_count:
                    break
                try:
                    game_batch = future.result()
                except requests.RequestException:
                    continue

                if not game_batch:
                    continue

                random.shuffle(game_batch)
                for game in game_batch:
                    if len(games) >= requested_count:
                        break

                    game_id = game.get("id")
                    if not isinstance(game_id, int) or game_id in selected_ids:
                        continue

                    platforms = game.get("platforms") or []
                    platform_name = (
                        platforms[0].get("name", "Plataforma no disponible")
                        if platforms and isinstance(platforms[0], dict)
                        else "Plataforma no disponible"
                    )
                    release_date = format_release_date(game.get("first_release_date"))
                    rating = game.get("total_rating")
                    if not isinstance(rating, (int, float)):
                        rating = game.get("rating")
                    if min_rating is not None and (not isinstance(rating, (int, float)) or rating < min_rating):
                        continue

                    rating_text = (
                        f"{rating:.2f}" if isinstance(rating, (int, float)) else "N/D"
                    )
                    aggregated = game.get("aggregated_rating")
                    aggregated_text = (
                        f"{aggregated:.2f}" if isinstance(aggregated, (int, float)) else "N/D"
                    )
                    slug = game.get("slug", "")
                    name = game.get("name", "Nombre no disponible")

                    games.append((game_id, name, platform_name, release_date, rating_text, aggregated_text, slug))
                    selected_ids.add(game_id)

    return games


def append_games_to_file(file_path: str, games: list[tuple]) -> None:
    with open(file_path, "a", encoding="utf-8") as file:
        for game in games:
            file.write(
                f"{game[0]}. {game[1]} ({game[2]}, {game[3]}, Rating: {game[4]}, Critica: {game[5]}, {game[6]})\n"
            )


def prompt_platform_and_count(session: requests.Session) -> tuple[int, str, int] | None:
    while True:
        platform_input = input(
            "Ingrese la plataforma que desea (ej: PC, PlayStation 5, Nintendo Switch): "
        ).strip()
        if not platform_input:
            print("Debe ingresar una plataforma.")
            continue

        try:
            platform_results = search_platforms(session, platform_input)
        except requests.RequestException as error:
            print("No se pudieron consultar plataformas en IGDB.")
            print(f"Detalle: {error}")
            return None

        if not platform_results:
            print("No se encontraron plataformas con ese nombre. Intente nuevamente.")
            continue

        print("\nPlataformas encontradas:")
        for index, platform in enumerate(platform_results, start=1):
            print(f'{index}. {platform.get("name", "Sin nombre")} (ID: {platform.get("id", "N/A")})')

        selected_option = input(
            f"Seleccione una plataforma (1-{len(platform_results)}): "
        ).strip()
        if not selected_option.isdigit():
            print("Debe ingresar un numero valido.")
            continue

        selected_index = int(selected_option)
        if selected_index < 1 or selected_index > len(platform_results):
            print("La opcion seleccionada esta fuera de rango.")
            continue

        selected_platform = platform_results[selected_index - 1]
        platform_id = selected_platform.get("id")
        platform_name = selected_platform.get("name", "Plataforma")
        if not isinstance(platform_id, int):
            print("La plataforma seleccionada no tiene un ID valido.")
            continue

        break

    while True:
        count_input = input("Cuantos juegos desea generar?: ").strip()
        if not count_input.isdigit():
            print("Debe ingresar un numero entero positivo.")
            continue

        requested_count = int(count_input)
        if requested_count <= 0:
            print("La cantidad debe ser mayor a 0.")
            continue

        return platform_id, platform_name, requested_count


def prompt_optional_year() -> int | None:
    while True:
        year_input = input(
            "Filtrar por ano de lanzamiento? (ej: 2020, enter para omitir): "
        ).strip()
        if not year_input:
            return None
        if not year_input.isdigit():
            print("Debe ingresar un ano valido o dejar vacio.")
            continue
        year = int(year_input)
        if year < 1970 or year > 2100:
            print("Ingrese un ano entre 1970 y 2100.")
            continue
        return year


def prompt_optional_min_rating() -> float | None:
    while True:
        rating_input = input(
            "Filtrar por rating minimo (0-100, enter para omitir): "
        ).strip()
        if not rating_input:
            return None
        try:
            rating = float(rating_input.replace(",", "."))
        except ValueError:
            print("Debe ingresar un numero valido o dejar vacio.")
            continue

        if rating < 0 or rating > 100:
            print("El rating debe estar entre 0 y 100.")
            continue
        return rating


def prompt_user_and_open_links(games: list[tuple]) -> list[tuple]:
    """Muestra los juegos generados, abre los seleccionados y retorna los elegidos."""
    print("Se han elegido los siguientes juegos aleatorios:")
    for index, game in enumerate(games, start=1):
        print(f"{index}. {game[1]}")

    selected_games: list[tuple] = []

    while True:
        selected_games_input = input(
            f"\nSeleccione uno o varios juegos de la lista (1-{len(games)}) separados por comas: "
        )
        selected_games_numbers = []

        for token in selected_games_input.split(","):
            token = token.strip()
            if token.isdigit():
                selected_games_numbers.append(int(token))
            elif token:
                print(f'"{token}" no es un numero valido.')

        for game_number in selected_games_numbers:
            if 1 <= game_number <= len(games):
                game = games[game_number - 1]
                game_slug = game[6]
                if game_slug:
                    webbrowser.open(f"https://www.igdb.com/games/{game_slug}")
                else:
                    print(f'El juego "{game[1]}" no tiene slug disponible.')
                if game not in selected_games:
                    selected_games.append(game)
            else:
                print(f"El numero {game_number} esta fuera del rango de la lista.")

        user_choice = ""
        while user_choice.lower() not in ("s", "r"):
            user_choice = input('Ingrese "r" para regresar y seleccionar otro juego, o "s" para salir: ').strip()

        if user_choice.lower() == "s":
            break

    return selected_games


def main() -> None:
    random.seed()
    session = build_session()

    try:
        platform_selection = prompt_platform_and_count(session)
        if not platform_selection:
            input("Presione enter para salir...")
            return
        platform_id, platform_name, requested_count = platform_selection
        release_year = prompt_optional_year()
        min_rating = prompt_optional_min_rating()
        where_clause = build_where_clause(platform_id, release_year)
        total_games = get_total_games(session, where_clause)
    except requests.HTTPError as error:
        print("Error HTTP al consultar IGDB.")
        print(f"Detalle: {error}")
        if error.response is not None:
            print(f"Respuesta API: {error.response.text}")
        input("Presione enter para salir...")
        return
    except requests.RequestException as error:
        print("Error de conexion al consultar IGDB.")
        print(f"Detalle: {error}")
        input("Presione enter para salir...")
        return
    except ValueError as error:
        print(str(error))
        input("Presione enter para salir...")
        return

    existing_ids = parse_existing_ids(RANDOM_GAMES_FILE)

    if total_games <= 0:
        print("No hay juegos que cumplan con los filtros elegidos.")
        input("Presione enter para salir...")
        return

    games = pick_games(session, total_games, existing_ids, where_clause, requested_count, min_rating)
    if not games:
        print("No se pudieron obtener juegos aleatorios en este intento.")
        input("Presione enter para salir...")
        return
    if len(games) < requested_count:
        print(
            f"Solo se pudieron generar {len(games)} juegos sin repetir "
            f"con los filtros elegidos para {platform_name}."
        )

    selected_games = prompt_user_and_open_links(games)
    if selected_games:
        append_games_to_file(RANDOM_GAMES_FILE, selected_games)

    input("Presione enter para salir...")


if __name__ == "__main__":
    main()
