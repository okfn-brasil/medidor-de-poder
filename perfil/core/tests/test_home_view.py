from json import loads
from django.shortcuts import resolve_url


def test_home_has_a_success_message(client):
    response = client.get(resolve_url("home"))
    assert 200 == response.status_code

    data = loads(response.content.decode("utf-8"))
    assert data["message"] == "API do Perfil Politico está online."
