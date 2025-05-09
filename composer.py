from bs4 import BeautifulSoup
import requests
import re
import networkx as nx
import spacy
import numpy as np
import time
import pickle
import json
#from ipysigma import Sigma

class Composer:
    def __init__(self,ID="Q36834",nomcomplet=None,nom=None,prenom=None,naissance=None,mort=None,desc=None,pays=None, influences = set()):
        if ID=="Q36834":
            if prenom is not None and nom is not None:
                self.id=find_id((prenom,nom))
            elif nomcomplet is not None :
                self.id=find_id(nomcomplet)
            elif nom is not None :
                self.id=find_id(nom)
            else:
                self.id=ID
        else:
            self.id = ID
        self.name = nomcomplet
        self.familyname = nom
        self.firstname = prenom
        self.birth = naissance
        self.death = mort
        self.description = desc
        self.country = pays
        self.influences = influences

    """
    def __str__(self):
        if self.name is not None:
            return self.name
        elif self.firstname is not None and self.familyname is not None :
            return self.firstname+self.familyname
        elif self.familyname is not None :
            return self.familyname
        else :
            return self.id
    """

    def __repr__(self):
        if self.name is not None:
            return self.name
        elif self.firstname is not None and self.familyname is not None :
            return self.firstname+self.familyname
        elif self.familyname is not None :
            return self.familyname
        else :
            return self.id

    def set_attributes(self,lg="en"):
        entity_id = self.id
        #Dictionnaire des propriétés souhaitées
        dico_props = {"pays" : "P27",
              "nom" : "P734",
              "prenom" : "P735",
              "date de naissance" : "P569",
              "date de mort" : "P570",
              "genre" : "P136",
              "influencé par" : "P737",
              "inverse property label item" : "Q65932995", #il reste à comprendre comment s'en servir
              "oeuvres":"P800",
              "religion" : "P140",
              "étudiant de" : "P1066",
              "professeur de": "P802",
              "écoles" : "P69",
              "domaines" : "P101",
              "institut" : "P108",
              "début de carrière" : "P2031",
              "langues" : "P1412",
              "lieux de vie" : "P551",
              "mouvement" : "P135",
              "métiers" : "P106"}
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={entity_id}"
        response = requests.get(url)
        properties = {"id" : entity_id}
        if response.status_code == 200:
            data = response.json()
            data2 = data['entities'][entity_id]
            if 'labels' in data2 and lg in data2['labels']:
                name = data2['labels'][lg]['value']
            elif 'labels' in data2 and 'en' in data2['labels']:
                name = data2['labels']['en']['value']
            else:
                name = entity_id
            properties["nom"] = name
            self.name = name
            if 'descriptions' in data2 and lg in data2['descriptions']:
                desc = data2['descriptions'][lg]['value']
            elif 'descriptions' in data2 and 'en' in data2['descriptions']:
                desc = data2['descriptions']['en']['value']
            else:
                desc = entity_id
            properties["description"] = desc
            self.description = desc
            claims = data['entities'][entity_id]['claims']
            for prop in claims:
                if prop.startswith("P"):
                    if dico_props is None or prop in dico_props.values():
                        if len(claims[prop]) > 0:
                            properties[prop] = []
                            for item in claims[prop]:
                                if 'mainsnak' in item and 'datavalue' in item['mainsnak']:
                                    value = item['mainsnak']['datavalue']
                                    if value['type'] == 'wikibase-entityid':
                                        properties[prop].append(value['value']['id'])
                                    elif value['type'] == 'string':
                                        properties[prop].append(value['value'])
                                    elif value['type'] == 'time':
                                        properties[prop].append(value['value']['time'])
                                    elif value['type'] == 'quantity':
                                        properties[prop].append(value['value']['amount'])
                                    elif value['type'] == 'globe-coordinate':
                                        properties[prop].append((value['value']['latitude'], value['value']['longitude']))
                                    else:
                                        properties[prop].append(value['value'])
        #if dico_props is not None:
            proprietes = {"id" : entity_id, "nom complet" : name, "description" : desc}
            for name, prop in dico_props.items():
                if prop in properties:
                    proprietes[name] = properties[prop]
                    if name == "date de naissance" :
                        self.birth = properties[prop]
                    if name == "date de mort" :
                        self.death = properties[prop]
                    if name == "nom" :
                        self.familyname = properties[prop]
                    if name == "prenom" :
                        self.firstname = properties[prop]
            return proprietes
        #return properties
        else:
            print(f"Erreur lors de la récupération des propriétés : {response.status_code}")
            return None

def find_id(name):
    """Récupère l'id d'un compositeur à partir de son nom"""
    if type(name)!=str:
        strbool = False
        url = f"https://www.wikidata.org/w/index.php?search={name[0]}+{name[-1]}&title=Special%3ASearch&ns0=1&ns120=1"
    else:
        strbool = True
        #name=name.replace("- Wikipedia","")
        url = f"https://www.wikidata.org/w/index.php?search={name}&title=Special%3ASearch&ns0=1&ns120=1"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    try :
        bloc = soup.find("div", class_ = "mw-search-result-heading")
        group = bloc.find("a")
        if group is None:
            return None
        else:
            return group["href"][6:]
    except:
        #print(f"Erreur sur le nom {name[0]} {name[1]}")
        #return None
        if strbool:
            print(f"Erreur sur le nom {name}")
            return None
        print(f"Erreur sur le nom {name[0]} {name[-1]}")


def is_composer(id, name=None, get_the_dates_too=True, get_the_pupils=True):
    """détermine si l'id donné est celui d'un compositeur et si oui renvoie une instance de la classe Composer avec le bon id et certains de ses ttributs"""
    sparql_endpoint = "https://query.wikidata.org/sparql"
    query = f"""
    SELECT ?prop ?bd ?dd ?ct ?pu WHERE {{
        wd:{id} wdt:P106 ?prop.
        OPTIONAL {{ wd:{id} wdt:P569 ?bd. }}
        OPTIONAL {{ wd:{id} wdt:P570 ?dd. }}
        OPTIONAL {{ wd:{id} wdt:P27 ?ct.  }}
        OPTIONAL {{ wd:{id} wdt:P802 ?pu. }}
    }}
    """
    response = requests.get(sparql_endpoint, params={'query': query, 'format': 'json'})
    #time.sleep(0.05)
    #print(response.text)
    if "Q36834\"" in response.text:
        bd=None
        dd=None
        ct=None
        influ = set()
        if get_the_dates_too:
            #print(response.text)
            #b,d = True,True
            data = response.json()
            try :
                bd=int(data["results"]["bindings"][0]["bd"]["value"].split("-")[0].strip())
            except :
                #b=False
                #bd=None
                print(f"no valid birth date for {name}")
            try :
                dd=int(data["results"]["bindings"][0]["dd"]["value"].split("-")[0].strip())
            except :
                #d=False
                #dd=None
                print(f"no valid death date for {name}")
            try :
                ct = data["results"]["bindings"][0]["ct"]["value"]
            except :
                ct = None
        if get_the_pupils :
            try :
                #pu = re.split(r'[;,\s]+', data["results"]["bindings"][0]["pu"]["value"])
                #print("trying to get the pupils")
                pu=""
                for j in range(len(data["results"]["bindings"])):
                    #print("inside the loop")
                    previouspu = pu
                    pu = data["results"]["bindings"][j]["pu"]["value"].split("entity/")[-1]
                    if previouspu != pu:
                        #print(pu)
                        c = is_composer(pu,get_the_pupils=False)
                        #print(c)
                        if c is not None :
                            influ.add(c)
                print(name,influ)
                #print(pu)
                #print(len(pu)//2)
                """for p in [pu[(i*2)+1] for i in range(len(pu)//2)]:
                    #print(p)
                    c = is_composer(p,get_the_pupils=False)
                    if c is not None :
                        influ.add(c)
                print(influ)"""
            except :
                return Composer(ID=id,nomcomplet=name,naissance=bd,mort=dd,pays=ct)

        return Composer(ID=id,nomcomplet=name,naissance=bd,mort=dd,pays=ct,influences=influ)

    else:#this guy is not a composer
        return None
#getting the wikidata ID from a given wikipedia page
#"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&redirects=1&titles=ARTICLE_NAME"
