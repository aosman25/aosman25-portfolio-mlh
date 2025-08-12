import requests
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
fake = Faker()

api_url = "http://localhost:5000/api/timeline_post"

for i in range(100):
    post = {
        "name": fake.name(),
        "email": fake.email(),
        "content": fake.sentence(nb_words=12)
    }

    response = requests.post(api_url, data=post)
    if response.status_code == 200:
        print(f"Posted {i+1}: {post['name']}")
    else:
        print(f"Failed {i+1}: {response.status_code} - {response.text}")