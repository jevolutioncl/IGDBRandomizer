import requests
import random
import webbrowser

# Configuración
url = 'https://api.igdb.com/v4/games'
client_id = 'AQUÍ PON TU CLIENT_ID DE IGDB'
client_secret = 'AQUÍ PON TU CLIENT_SECRET DE IGDB'
access_token = 'AQUÍ PON TU ACCESS_TOKEN DE IGDB'
random_games_file = 'AQUÍ PON EL NOMBRE DE TU ARCHIVO .TXT DONDE GUARDARÁS EL VIDEOJUEGO ALEATORIO ELEGIDO'

# Obtener lista de juegos aleatorios
headers = {
    'Client-ID': client_id,
    'Authorization': f'Bearer {access_token}',
}

data = '''
fields name, platforms.name, first_release_date, total_rating;
where platforms != null;
sort random;
limit 10;
'''

response = requests.post(url, headers=headers, data=data)
games = response.json()

# Leer el archivo de juegos aleatorios ya seleccionados
with open(random_games_file, 'r') as f:
    games_list = f.read().splitlines()

# Verificar que hay juegos en la lista
if len(games) == 0:
    print('No se encontraron juegos que cumplan con los criterios de búsqueda.')
else:
    # Elegir un juego aleatorio que no esté en la lista de juegos ya seleccionados
    game = None
    while game is None:
        game = random.choice(games)
        game_name = game.get('name', 'Nombre no disponible')
        game_platform = game.get('platforms', [{'name': 'Plataforma no disponible'}])[0].get('name')
        game_release_date = game.get('first_release_date', 'Año de lanzamiento no disponible')
        game_rating = game.get('total_rating', 'Valoración no disponible')
        game_slug = game.get('slug', 'Slug no disponible')
        if game_name in games_list:
            game = None

    with open(random_games_file, 'a') as f:
        f.write(f'{len(games_list) + 1}. {game_name} ({game_platform}, {game_release_date}, {game_rating})\n')

    print(f'Se ha elegido el juego "{game_name}" con slug "{game_slug}" aleatoriamente.')
    
    # Buscar gameplay en YouTube
    search_term = f'{game_name} gameplay'
    webbrowser.open(f'https://www.youtube.com/results?search_query={search_term}')

    # Buscar trailer en YouTube
    search_term = f'{game_name} trailer'
    webbrowser.open(f'https://www.youtube.com/results?search_query={search_term}')

    # Buscar analisis en YouTube
    search_term = f'{game_name} analisis'
    webbrowser.open(f'https://www.youtube.com/results?search_query={search_term}')

    # Buscar videojuego en Google
    search_term = f'{game_name}'
    webbrowser.open(f'https://www.google.com/search?q={search_term}')
