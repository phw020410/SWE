def test_root(environment):
    client, _, _ = environment
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "Hello, FastAPI!"}


def test_item_crud(environment):
    client, _, _ = environment
    res = client.post("/items", json={"name": "Pen", "price": 1.5})
    assert res.status_code == 201
    item_id = res.json()["id"]

    assert client.get(f"/items/{item_id}").json()["name"] == "Pen"

    res = client.patch(f"/items/{item_id}", json={"price": 2.0})
    assert res.json()["price"] == 2.0

    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404


def test_invalid_price(environment):
    client, _, _ = environment
    res = client.post("/items", json={"name": "Bad", "price": -1})
    assert res.status_code == 422
