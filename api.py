import requests
import urllib
import pickle
import os

# Using Windows VK client APP_ID/TOKEN
APP_ID = "3697615"
APP_TOKEN = "AlVXZFMUqyrnABp8ncuU"
APP_SCOPE = "friends,groups,messages,video,wall,offline,docs"


class VKApi:

    def __init__(self, username, password, version=None):
        self.version = version

        if os.path.exists('vk_api.dat'):
            data = pickle.load(open('vk_api.dat'))
            self.access_token = data['ACCESS_TOKEN']
        else:
            self.access_token = self.auth(username, password)

            pickle.dump({
                'ACCESS_TOKEN': self.access_token,
            }, open('vk_api.dat', 'w'))

    def auth(self, login, password):
        out = requests.get("https://oauth.vk.com/token?" + urllib.urlencode({
            "grant_type": "password",
            "client_id": APP_ID,
            "client_secret": APP_TOKEN,
            "username": login,
            "password": password,
            "scope": APP_SCOPE
        })).json()

        if "access_token" not in out:
            print out
        return out["access_token"]

    def upload_video(self, upload_url, source_file):
        if os.path.exists(source_file) and os.path.isfile(source_file):
            with open(source_file, 'rb') as source_fd:
                return requests.post(upload_url, files={
                    'video_file': source_fd
                }, verify=False).json()

        return None

    def call(self, method, **call_params):
        params = {'access_token': self.access_token}
        params.update(call_params)
        params.update({'v': self.version} if self.version else {})

        request_params = "&".join(["%s=%s" % (str(key), urllib.quote(str(params[key]))) for key in params.keys()])
        request_url = "https://api.vk.com/method/" + method + "?" + request_params

        resp = requests.get(request_url, headers={
            'Content-Type': 'text/html; charset=UTF-8'
        }).json()

        if "error" in resp:
            raise Exception("[ERROR] " + str(resp))
        else:
            return resp["response"]
