import requests

url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&api_key=43f29461dbc8afc0bec3f402b8ebc56424b538cc9f628a5deb3a71baf58a94ba"

req = requests.get(url=url).json()['Data'][0]
print(req)
print(f"*bold \*{req['title']}*\n\n*italic \*{req['body']}*\n\n*bold \*Source:* [Click here to visit the article site.]({req['guid']})")