import requests


class Session:
    def __init__(self):
        self.session = requests.Session()

    def login(self, username, password):
        login_url = "https://www.dl.ndl.go.jp/soushinLoginInput"
        payload = {
            "userId": username,
            "password": password,
        }
        response = self.session.post(url=login_url, data=payload)
        if response.status_code != 200:
            raise Exception("login failed")

    def get(self, url, params=None):
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            raise Exception("get failed")
        return response.content
