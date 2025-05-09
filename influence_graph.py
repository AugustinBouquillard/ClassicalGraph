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
from composer import *


def get_person_entities(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    L=[]
    for ent in doc.ents:
        if ent.label_=='PERSON':
            #print(ent.text, ent.start_char, ent.end_char, ent.label_)
            L.append(ent.text)
    #print(L)
    return L

def get_wikipedia_page_text(name,language="en"):
    url = f"https://{language}.wikipedia.org/w/index.php?search={name}"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    text=soup.get_text()
    if language =="en" and (name+" - Wikipedia" in text or name.split(" ")[-1]+" - Wikipedia" in text):
        return get_wikipedia_page_text(name+" (composer)")
    elif language=="fr" and (name+" - Wikipédia" in text or name.split(" ")[-1]+" - Wikipédia" in text):
        return get_wikipedia_page_text(name+" (compositeur)")
    return text

def composer_filter_by_dict(list_of_names, dico):
    """filtre les noms qui sont ceux de compositeurs à partir d'un dictionnaire de compositeurs, évite d'avoir à rechercher dans wikidata à chaque fois donc plus rapide mais moins robuste, à compléter peut-être avec le TD qui utilisait des Trie"""
    list_of_names = list(filter(lambda x: x.strip() in dico, list_of_names))
    return list_of_names

#composer_filter_by_dict(["Richard Wagner","Bach","Mozart"],{"Richard Wagner":(1813,1883),"Johann Sebastian Bach":(1685,1750)})

def composer_filter(list_of_names):
    compo_dico={}
    for n in list_of_names:
        c_id = find_id(n)
        if c_id is not None and c_id not in compo_dico:
            c = is_composer(c_id,n)
            #print(is_composer(n))
            if c is not None :
                compo_dico[c_id]=c
                print(n,"is a composer")
    return compo_dico


def find_compositional_influences(name,fr=False):#problème : l'algo saute souvent Beethoven, y compris chez Wagner
    content = get_wikipedia_page_text(name)
    if fr:
        content+=get_wikipedia_page_text(name,"fr")
    persons = get_person_entities(content)
    return(composer_filter(persons))

def build_list_of_influences(enum_of_composers,french=False):
    list_of_influ_dict=[]
    for composer in enum_of_composers:
        list_of_influ_dict.append(find_compositional_influences(composer,fr=french))
    return list_of_influ_dict


def orienting_with_dates(list_of_dico,compo_dico={}):
    """completing the influences of all encountered compsoers; orienting the influence relations when no doubt exists because of birth-death dates"""

    for dico in list_of_dico:
        cpt=0
        b=False #boolean equal to True iff we have access the the birth date of the first composer
        d=False #boolean equal to True iff we have access the the death date of the first composer
        for c in dico.values():

            if c.id not in compo_dico :
                compo_dico[c.id]=c

            if cpt==0: #the first element of each dictionary is the one whose wikipedia page was used to retrieve all the others present in the current dictionary
                compo = compo_dico[c.id]
                birth_date_compo = compo.birth
                death_date_compo = compo.death
                if birth_date_compo is not None :
                    print("db:"+str(c.birth))
                    b = True

                if death_date_compo is not None :
                    print("dd:"+str(c.death))
                    d = True

                cpt+=1

            else :
                birth_date = c.birth
                death_date = c.death

                if d and birth_date is not None:
                    if birth_date > death_date_compo-20:#if compo died at most 2O years after the birth of c then we assume only compo could influence c and not the other way around
                        compo_dico[compo.id].influences.add(c)
                    elif b and death_date is not None:
                        if death_date < birth_date_compo+20:#if the current composer c died at most 20 years after the birth of compo we assume compo could not influence c and that only c influenced compo
                            compo_dico[c.id].influences.add(compo)
                    else:
                        compo_dico[compo.id].influences.add(c)
                        compo_dico[c.id].influences.add(c)

                elif b and death_date is not None:
                        if death_date < birth_date_compo+20:#if the current composer c died at most 20 years after the birth of compo we assume compo could not influence c and that only c influenced compo
                            compo_dico[c.id].influences.add(compo)
                        #elif d and birth_date is not None:
                        #    if birth_date > death_date_compo-20:#if compo died at most 2O years after the birth of c then we assume only compo could influence c and not the other way around
                        #        compo_dico[compo.id].influences.add(c)
                        else:
                            compo_dico[compo.id].influences.add(c)
                            compo_dico[c.id].influences.add(c)

                else:#we cannot say anything for sure since they were contemporary so by default we assume they influenced each other
                    compo_dico[compo.id].influences.add(c)
                    compo_dico[c.id].influences.add(compo)


    return compo_dico


def build_graph_from_dict(compo_dico,G=nx.DiGraph()):
    for compo in compo_dico.values():
        for c in compo.influences:
            G.add_edge(compo,c)
    # save graph object to file
    pickle.dump(G, open(str(next(iter(compo_dico.keys())))+".pickle", 'wb'))
    return G

def graph_of_influences(list_of_compo_names,fr=True):
    list_of_influ_dicts=build_list_of_influences(list_of_compo_names,fr)#put false if you're only interested in the english wiki
    compo_dico = orienting_with_dates(list_of_influ_dicts)
    return build_graph_from_dict(compo_dico)


G1=graph_of_influences(["Paul Le Flem"])
G2=graph_of_influences(["César Franck","Henri Duparc","Jean Cras","Charles-Marie Widor","Louis Vierne","Alexandre Guilmant","Marcel Dupré","Eugène Gigout","Jehan Alain","Charles Tournemire","Gabriel Dupont","Déodat de Séverac","Vincent d'Indy","Albert Roussel","Olivier Messiaen","Pierre Boulez", "Naji Hakim","Edgar Varèse", "Tristan Murail","Iannis Xenakis","Gérard Grisey","Claude Debussy","Maurice Ravel","Gabriel Fauré","Reynaldo Hahn","Gustave Samazeuilh","Paul Ladmirault","Paul Le Flem","Philippe Hersant","Maurice Duruflé","Thierry Escaich","Yves Castagnet","Eric Lebrun","Jean-Philippe Rameau","Louis Couperin","Claude Balbastre","Arthur Honegger","George Auric","Francis Poulenc","Germaine Taillefer","Darius Milhaud","Louis Durey","Guy Ropartz","Henri Rabaud","Sylvio Lazzari","Louis Aubert","Charles Munch","Hector Berlioz","André Caplet","André Jolivet","André Messager","Yves Baudrier","Erik Satie","Jules Massenet","Charles Gounod","Georges Bizet","Ernest Chausson","Jacques Offenbach","Étienne Nicolas Méhul","André Grétry","François-Joseph Gossec","Jean-François Lesueur","Adolphe Adam","François-Adrien Boieldieu","Léon Boëllmann","Camille Saint-Saëns","Florent Schmitt","Charles-Valentin Alkan","Ambroise Thomas","Alexandre-Pierre-François Boëly"],True)
#G=graph_of_influences(["Jean Perrin"])
#nx.draw(G, with_labels=True)#, labels = nx.get_node_attributes(graph, 'nom complet'))
