import requests
import random

# Configuración
url = 'https://api.igdb.com/v4/games'
client_id = 'INSERTA TU CLIENT_ID DE LA API DE IGDB'
client_secret = 'INSERTA TU CLIENT_SECRET DE LA API DE IGDB'
access_token = 'INSERTA TU ACCESS_TOKEN DE LA API DE IGDB'
random_games_file = 'INSERTA EL NOMBRE DE TU .TXT DONDE GUARDARÁS TUS JUEGOS ALEATORIOS, EJEMPLO: randomgames.txt'
random.seed()

# Obtener total de juegos en IGDB
headers = {
    'Client-ID': client_id,
    'Authorization': f'Bearer {access_token}',
}

data = 'fields id; limit 1;'
response = requests.post(url, headers=headers, data=data)
total_games = response.json()[0]['id']

# Leer el archivo de juegos aleatorios ya seleccionados
with open(random_games_file, 'r') as f:
    games_list = f.read().splitlines()

# Verificar que hay juegos suficientes en la lista
if len(games_list) == total_games:
    print('Se han seleccionado todos los juegos disponibles en IGDB.')
elif len(games_list) >= total_games - 50:
    print('Solo quedan 50 o menos juegos disponibles en IGDB.')
else:
    # Elegir cinco juegos aleatorios que no estén en la lista de juegos ya seleccionados
    games = []
    while len(games) < 50:
        random_game_id = random.randint(1, total_games)
        if str(random_game_id) in games_list:
            continue
        data = f'''
        fields name, platforms.name, first_release_date, total_rating, slug;
        where id = {random_game_id} & platforms != null;
        '''
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200 and len(response.json()) > 0:
            game = response.json()[0]
            game_name = game.get('name', 'Nombre no disponible')
            game_platform = game.get('platforms', [{'name': 'Plataforma no disponible'}])[0].get('name')
            game_release_date = game.get('first_release_date', 'Año de lanzamiento no disponible')
            game_rating = game.get('total_rating', 'Valoración no disponible')
            game_slug = game.get('slug', 'Slug no disponible')
            games.append((random_game_id, game_name, game_platform, game_release_date, game_rating, game_slug))
            
    with open(random_games_file, 'a') as f:
        for game in games:
            game_info = f'{game[0]}. {game[1]} ({game[2]}, {game[3]}, {game[4]}, {game[5]})\n'
            f.write(game_info)

    print('Se han elegido los siguientes juegos aleatorios:')
    for i, game in enumerate(games):
        print(f'{i+1}. {game[1]}')

input("Presione enter para salir...")
