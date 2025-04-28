class Composer:
    def __init__(self,nom,prenom,naissance,mort,influences = []):
        self.nom = nom
        self.prenom = prenom
        self.naissance = naissance
        self.mort = mort
        self.influences = influences

class Oeuvre:
    def __init__(self,titre,compositeur,genre,date,filename = None):
        self.titre = titre
        self.compositeur = compositeur
        self.genre = genre
        self.date = date
        self.filename = filename