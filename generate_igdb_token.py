import os

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["IGDB_CLIENT_ID"]
CLIENT_SECRET = os.environ["IGDB_CLIENT_SECRET"]
TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def generate_access_token(client_id: str, client_secret: str) -> dict:
    """Solicita un access_token para la API de IGDB usando Client Credentials."""
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    response = requests.post(TOKEN_URL, params=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def main() -> None:
    try:
        token_data = generate_access_token(CLIENT_ID, CLIENT_SECRET)
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")
        token_type = token_data.get("token_type")

        print("\nToken generado correctamente:")
        print(f"access_token: {access_token}")
        print(f"token_type: {token_type}")
        print(f"expires_in: {expires_in} segundos")
        print("\nCopia este access_token en IGDBRandomizer.py")
    except requests.HTTPError as error:
        print("Error HTTP al generar el token.")
        print(f"Detalle: {error}")
        if error.response is not None:
            print(f"Respuesta API: {error.response.text}")
    except requests.RequestException as error:
        print("Error de conexion al generar el token.")
        print(f"Detalle: {error}")


if __name__ == "__main__":
    main()
