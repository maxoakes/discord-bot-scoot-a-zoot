import requests
import json

class Call:

    def get_dict(endpoint: str) -> dict:
        response = requests.get(endpoint)
        return response.json()
    
    def clean_response(response: requests.Response):
        if response.headers.get('content-type').find('application/json') > -1:
            return json.loads(response.json())
        elif response.headers.get('content-type').find('text/html') > -1:
            return response.text
        else:
            return f"Unknown API response: `{response.headers.get('content-type')}`"
    
    # all the assorted API calls
    # https://api.mcsrvstat.us/
    def minecraft_server(addr: str):
        param = 'localhost' if addr == '' else addr
        response = Call.get_dict(f'https://api.mcsrvstat.us/2/{param}')
        print(response.items())
        return response