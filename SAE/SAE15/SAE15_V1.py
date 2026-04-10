from md_to_html import convert2
import time
import requests

# https://www.openstreetmap.org/api/0.6/node/1996209696

#api_url = "https://www.openstreetmap.org/api/0.6/node/1947604611.json"
#response = requests.get(api_url)
# a = help(response)
# b = response.status_code
# c = response.text
#donnees = response.json()
#element = donnees.get("elements")[0]
#json_data = element.get("tags").get("name"),element.get("lat"),element.get("lon")

'''
def telecharger(l,d):
    g = requests.get(l)
    r = g.text
    with open(d,"w") as doc:
        page = doc.write(r)
    return page

def get_node_name(id):
    api_url = f"https://www.openstreetmap.org/api/0.6/node/{id}.json"
    response = requests.get(api_url)
    donnees = response.json()
    try:
        element = donnees.get("elements")[0]
        json_data = element.get("tags").get("name")
    except:
        json_data = "SANS NOM"
    return json_data
'''



def evaluation(ville):
    ville = ville.title()
    total = 0
    nb_bus = 0
    nb_tram = 0
    nb_metro = 0
    d = {}

    # First Request (Bus stops)
    api_url = "https://overpass-api.de/api/interpreter"
    request = f"""
    [out:json][timeout:60];
    area["name"="{ville}"]["boundary"="administrative"]->.searchArea;
    node["highway"="bus_stop"](area.searchArea);
    out count;
    """
    
    data = None
    for attempt in range(5):
        print(f"Tentative de connexion à l'API (Bus)... {attempt + 1}/5")
        response = requests.get("https://overpass-api.de/api/interpreter", params={'data': request})
        try:
            data = response.json()
            break # Success
        except requests.exceptions.JSONDecodeError:
            print(f"Echec (Status {response.status_code})... Retente dans 2 sec")
            time.sleep(2)
            
    if data is None:
        print("Abandon après 5 tentatives.")
        return "Erreur API - Serveur indisponible"

    nb_bus = int(data.get("elements")[0].get("tags").get("total"))
    
    # Second Request (Tram stops)
    request = f"""
    [out:json][timeout:60];
    area["name"="{ville}"]["boundary"="administrative"]->.searchArea;
    node["railway"="tram_stop"](area.searchArea);
    out count;
    """
    
    data = None
    for attempt in range(5):
        print(f"Tentative de connexion à l'API (Tram)... {attempt + 1}/5")
        response = requests.get("https://overpass-api.de/api/interpreter", params={'data': request})
        try:
            data = response.json()
            break # Success
        except requests.exceptions.JSONDecodeError:
            print(f"Echec (Status {response.status_code})... Retente dans 2 sec")
            time.sleep(2)

    if data is None:
        print("Abandon après 5 tentatives.")
        return "Erreur API - Serveur indisponible"
        
    nb_tram = int(data.get("elements")[0].get("tags").get("total"))

    # Third Request (Metro stops)
    request = f"""
    [out:json][timeout:60];
    area["name"="{ville}"]["boundary"="administrative"]->.searchArea;
    node["station"="subway"](area.searchArea);
    out count;
    """
    
    data = None
    for attempt in range(5):
        print(f"Tentative de connexion à l'API (Metro)... {attempt + 1}/5")
        response = requests.get("https://overpass-api.de/api/interpreter", params={'data': request})
        try:
            data = response.json()
            break # Success
        except requests.exceptions.JSONDecodeError:
            print(f"Echec (Status {response.status_code})... Retente dans 2 sec")
            time.sleep(2)

    if data is None:
        print("Abandon après 5 tentatives.")
        return "Erreur API - Serveur indisponible"
        
    nb_metro = int(data.get("elements")[0].get("tags").get("total"))
    total = nb_bus + nb_tram + nb_metro

    wp_api_url = "https://fr.wikipedia.org/w/api.php"
    wp_params = {
        "action": "query",
        "prop": "pageprops",
        "titles": ville,
        "format": "json",
        "redirects": 1
    }
    
    headers = {"User-Agent": "CityDataScript/1.0 (contact@example.org)"}
    
    wp_res = requests.get(wp_api_url, params=wp_params, headers=headers).json()
    pages = wp_res.get("query", {}).get("pages", {})
    
    qid = None
    for pid in pages:
        if "pageprops" in pages[pid]:
            qid = pages[pid]["pageprops"].get("wikibase_item")

    sparql_url = "https://query.wikidata.org/sparql"
    query = f"""
    SELECT?superficie WHERE {{
        wd:{qid} wdt:P2046?superficie.
    }}
    """
    sparql_res = requests.get(
        sparql_url, 
        params={'query': query, 'format': 'json'}, 
        headers=headers
    ).json()
    
    results = sparql_res.get("results", {}).get("bindings",)
    superficie = float(results[0].get("superficie").get("value"))
    scores = total / superficie
    
    d['total'] = total
    d['nb_bus'] = nb_bus
    d['nb_tram'] = nb_tram
    d['nb_metro'] = nb_metro

    if scores > 50:
        d['etat'] = "très bien desservie"
    elif scores <= 50 and scores > 25:
        d['etat'] = "bien desservie"
    elif scores <= 25 and scores > 15:
        d['etat'] = "moyennement desservie"
    elif scores <= 15 and scores > 0:
        d['etat'] = "mal desservie"
    else:
        d['etat'] = "pas desservie"
    
    txt = ""
    txt += f"# -- Statistiques concernant {ville} --  \n\n\n"
    txt += f" - **Au niveau des transport en commun, cette ville est {d['etat']}.**  \n\n"
    txt += f" - **Au total, cette ville a {d['total']} arrêts.**  \n\n"
    txt += f" - **Parmis ces arrêts, il y a {d['nb_bus']} arrêts de bus.**  \n\n"
    txt += f" - **Parmis ces arrêts, il y a {d['nb_tram']} arrêts de tram.**  \n\n"
    if d['nb_metro'] > 0:
        txt += f" - **Parmis ces arrêts, il y a {d['nb_metro']} arrêts de métro.**  \n\n"
    else:
        txt += f" - **Parmis ces arrêts, il n'y a pas d'arrêts de métro.**  \n\n"
    try:
        with open('file2.md','r') as f:
            text = f.read()
        texte = text + txt
    except:
        pass
    with open('file2.md','w') as f:
        f.write(texte)
    convert2()


# print(telecharger('https://www.openstreetmap.org/api/0.6/node/3649697385',"fichier.html"))
#print(get_node_name(1947604611))
#print(node_to_md(12534300884))

villes_a_tester = ["Caen", "Le Mans", "Paris", "Rennes", "Bordeaux", "Strasbourg", "Nantes"]
reset = ''
with open('file2.md','w') as f:
    f.write(reset)

for v in villes_a_tester:
    print(f"\n--- Evaluation de {v} ---")
    print(evaluation(v))
    
'''
https://overpass-api.de/api/interpreter?data=[out:json][timeout:25];
    area["wikipedia"="fr:Caen"]->.searchArea;
    nwr["highway"="bus_stop"](area.searchArea);
    out geom;.json

'''
