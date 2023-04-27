import requests
import random
import webbrowser

# Configuración
url = 'https://api.igdb.com/v4/games'
client_id = 'INSERTA TU CLIENT_ID DE LA API DE IGDB AQUÍ'
client_secret = 'INSERTA TU CLIENT_SECRET DE LA API DE IGDB AQUÍ'
access_token = 'INSERTA TU ACCESS_TOKEN DE LA API DE IGDB AQUÍ'
random_games_file = 'INSERTA EL NOMBRE DEL ARCHIVO .TXT DONDE SE GUARDARÁN LOS JUEGOS ALEATORIOS AQUÍ'
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
    while True:
        selected_games_input = input(f'\nSeleccione uno o varios juegos de la lista (1-{len(games)}) separados por comas: ')
        selected_games_numbers = []

        # Extraer los números de los juegos seleccionados
        try:
            selected_games_numbers = [int(num.strip()) for num in selected_games_input.split(',') if num.strip().isdigit()]
        except ValueError:
            print('Por favor, ingrese números válidos separados por comas.')

        # Abrir enlaces de los juegos seleccionados
        for game_number in selected_games_numbers:
            if 1 <= game_number <= len(games):
                game_slug = games[game_number - 1][5]
                game_url = f'https://www.igdb.com/games/{game_slug}'
                webbrowser.open(game_url)
            else:
                print(f'El número {game_number} está fuera del rango de la lista.')

        user_choice = ''
        while user_choice.lower() not in ['s', 'r']:
            user_choice = input('Ingrese "r" para regresar y seleccionar otro juego, o "s" para salir: ')

        if user_choice.lower() == 's':
            break
input("Presione enter para salir...")
