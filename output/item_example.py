import requests

data = {
    "name": "Example Item",
    "description": "This is an example item"
}

response = requests.post("http://localhost:5000/items", json=data)

if response.status_code == 201:
    print("Item created successfully")
else:
    print("Error creating item: ", response.text)
