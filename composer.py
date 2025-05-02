from bs4 import BeautifulSoup
import requests
import re
import networkx as nx
import spacy
import numpy as np
import time
import pickle
import json
from ipysigma import Sigma

class Composer:
    def __init__(self,ID,nom=None,prenom=None,naissance=None,mort=None,desc=None,influences = []):
        self.id = ID
        self.name = nom
        self.firstname = prenom
        self.birth = naissance
        self.death = mort
        self.description = desc
        self.influences = influences

    def set_attributes(self,lg="en"):
        entity_id = self.id
        #Dictionnaire des propriétés souhaitées
        dico_props = {"pays" : "P27",
              "nom" : "P735",
              "prenom" : "P734",
              "date de naissance" : "P569",
              "date de mort" : "P570",
              "genre" : "P136",
              "influences" : "P737",
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
                if name == "prenom" :
                    self.firstname = properties[prop]
            return proprietes
        #return properties
        else:
            print(f"Erreur lors de la récupération des propriétés : {response.status_code}")
            return None


def find_id(name):
    """Récupère l'id d'un compositeur à partir de son nom"""
    url = f"https://www.wikidata.org/w/index.php?search={name[0]}+{name[1]}&title=Special%3ASearch&ns0=1&ns120=1"
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
        print(f"Erreur sur le nom {name[0]} {name[1]}")
        return None



class Oeuvre:
    def __init__(self,titre,compositeur,genre,date,filename = None):
        self.titre = titre
        self.compositeur = compositeur
        self.genre = genre
        self.date = date
        self.filename = filename
