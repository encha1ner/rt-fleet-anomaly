import requests
import json
url='https://router.project-osrm.org/route/v1/driving/80.9467,26.8467;80.3319,26.4499?overview=full&geometries=geojson'
resp=requests.get(url)
print(f"STATUS = {resp.status_code}")
data=resp.json()
temp=data["routes"][0]["geometry"]["coordinates"]
required_data=[[lat,long] for long,lat in temp]
print(required_data)

with open ("routes.json","w") as f:
    json.dump(required_data,f,indent=4)







