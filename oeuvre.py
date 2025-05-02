from composer import Composer

class Oeuvre:
    def __init__(self,titre=None,compositeur=None,genre=None,date=None,category = None):
        self.titre = titre
        self.compositeur = compositeur
        self.genre = genre
        self.date = date
        self.category = category
        self.filename = None
        self.matrix = None

    def pp(self):
        return f"""
        Titre : {self.titre}
        Compositeur : {self.compositeur}
        Genre : {self.genre}
        Catégorie : {self.category}
        Fichier d'origine : {self.filename}
        """
    
    def __str__(self):
        return f"{self.compositeur} - {self.titre} - {self.genre}"