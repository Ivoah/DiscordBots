import re
import json
import requests

url = 'https://theportalwiki.com/wiki/List_of_Fact_Sphere_facts'

reg = re.compile(r'<a href="(?:https://i1\.theportalwiki\.net/img/[a-z0-9]/[a-z0-9]{2}/(.*?\.wav))".*?>(.*?)</a>')

facts = {}
for match in reg.finditer(requests.get(url).text):
    wav = match.group(1)
    fact = match.group(2).replace('<b>', '').replace('</b>', '')
    facts[fact] = wav

with open('facts.json', 'w') as f:
    json.dump(facts, f)
