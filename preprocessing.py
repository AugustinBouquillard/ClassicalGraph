import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import os
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
import seaborn as sns
from sklearn.decomposition import PCA
from collections import Counter
import umap.umap_ as umap
import plotly.express as px

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

li_notes = ['time','A','A#','B','C','C#','D','D#','E','F','F#','G','G#']

dico_composer = {
    "Johann Sebastian Bach": "Baroque",
    "Ludwig Van Beethoven": "Classical",
    "Alexander Borodin": "Romantic",
    "Johannes Brahms": "Romantic",
    "Antonn Dvorak": "Romantic",
    "Edvard Grieg": "Romantic",
    "Joseph Haydn": "Classical",
    "Felix Mendelssohn": "Romantic",
    "Wolfgang Amadeus Mozart": "Classical",
    "Nikolai Rimsky" : "Romantic",
    "Franz Schubert": "Romantic",
    "Bedich Smetana": "Romantic",
    "Joseph Suk": "Romantic",
    "Pyotr Ilyich Tchaikovsky": "Romantic",
}


class BulkPreprocessing:
    def __init__(self, picklefile, picklefile2, audio_dir = "audiofiles\csv", audio_dir2 = "audiofiles\csv", loudness_resolution = 50, overlap = 0.5, N = 3):
        self.loudness_resolution = loudness_resolution
        self.overlap = overlap
        self.audio_dir = audio_dir # Dossier par défaut avec classement des fichiers par sous-dossiers
        self.audio_dir2 = audio_dir2 # Dossier sans sous-dossiers
        self.N = N
        self.picklefile = picklefile
        self.picklefile2 = picklefile2
    
    @staticmethod
    def verbose(message,verb,importance = 0):
        """
        Print the message if verbose is set to True.
        """
        if verb>importance:
            print(message)
    
    @staticmethod
    def get_composer_audio_dir(filename):
        """Renvoie le compositeur à partir du nom de fichier"""
        composer = filename.split('-')[0]
        BulkPreprocessing.verbose(f"Compositeur extrait : {composer}", 0, 0)
        composer = ''.join([' ' + char if char.isupper() else char for char in composer]).strip()
        return composer

    @staticmethod
    def get_data_audio_dir2(filename):
        try:
            date = int(filename[:4])
            composer = filename[5:].split('-')[0]
            if len(composer.split()) > 1:
                composer = 'Unknown'
        except:
            date = -1
            composer = "Unknown"
        return composer, date
        
    
    @staticmethod
    def get_dataframes(chroma_f, verb=0):
        """Renvoie un dictionaire sous la forme titre : dataframe des chroma features"""
        li_notes = ['time','A','A#','B','C','C#','D','D#','E','F','F#','G','G#']
        df = pd.DataFrame(chroma_f.T, columns=li_notes[1:])
        while (df.tail(1).values == 0).all():
            df = df.iloc[:-1]
        return df

    @staticmethod
    def quantize(dataframe, loudness_resolution, verb):
        """Quantifie les valeurs de chroma features entre 0 et loudness_resolution"""
        dataframe = dataframe.to_numpy()
        dataframe/= np.max(dataframe)
        dataframe = np.ceil(dataframe * loudness_resolution)
        BulkPreprocessing.verbose(f"Tableau quantifié : {dataframe}", verb, 0)
        return dataframe
    
    @staticmethod
    def get_frames(dataframe,N,overlap, verb):
        """Découpe le dataframe en 2**N frames avec une proportion overlap de recoupement"""
        step = int((1-overlap)*len(dataframe)/2**N)
        frames = []
        for i in range(2**N):
            frames.append(dataframe[i*step:(i+1)*step,:])
        BulkPreprocessing.verbose(f"Nouvelles frames : {frames}", verb, 0)
        return frames
    
    @staticmethod
    def histogram(frame,loudness_resolution,verb, affiche = False):
        """Renvoie l'histogramme de la frame"""
        step = frame.shape[0]
        histogram = np.zeros((loudness_resolution+1, 12))
        for i in range(step):
            for j in range(12):
                loudness_level = int(frame[i, j])
                for k in range(loudness_level+1):
                    histogram[k, j] += 1
        histogram /= np.max(histogram)
        if affiche:
            plt.figure(figsize=(5,10))
            sns.heatmap(histogram, cmap='coolwarm', cbar=True, xticklabels=li_notes[1:], yticklabels=np.arange(loudness_resolution+1))
            plt.title('Histogramme de la frame')
            plt.xlabel('Chroma Features')
            plt.ylabel('Loudness Level')
            plt.show()
        return histogram
    
    @staticmethod
    def dico_hist(dico,loudness_resolution=50,N=3,overlap=0.5,verb=0):
        res = {}
        for titre, chroma in dico.items():
            dataframes = BulkPreprocessing.get_dataframes(chroma, verb)
            data = BulkPreprocessing.quantize(dataframes, loudness_resolution, verb)
            frames = BulkPreprocessing.get_frames(data, N, overlap, verb)
            histograms = []
            for frame in frames:
                histograms.append(BulkPreprocessing.histogram(frame, loudness_resolution, verb))
            res[titre] = histograms
        BulkPreprocessing.verbose(f"Dictionnaire d'histogrammes : {res}", verb, 0)
        return res
    
    def pickle_dump_audio_dir(self):
        chroma_dict = {}
        grouping_dict = {}
        for racine, sous_dossiers, _ in os.walk(self.audio_dir):
            for sous_dossier in sous_dossiers:
                sous_dossier_path = os.path.join(racine, sous_dossier)
                for filename in os.listdir(sous_dossier_path):
                    if filename.endswith(".csv"):
                        file_path = os.path.join(sous_dossier_path, filename)
                        df_csv = pd.read_csv(file_path)
                        df_csv = df_csv.iloc[:, 1:]
                        cols = df_csv.columns[1:]
                        #print(df_csv.head())
                        while (df_csv[cols].iloc[0] == 0).all():
                            df_csv = df_csv.iloc[1:].reset_index(drop=True)
                        while (df_csv[cols].iloc[-1] == 0).all():
                            df_csv = df_csv.iloc[:-1].reset_index(drop=True)
                        chroma = df_csv.iloc[:, 1:].values.T
                        #print(f"Tableau de {filename} : {df_csv.head()}")
                        #print(f"Matrice de {filename} : {chroma}")
                        chroma_dict[filename] = chroma
                        grouping_dict[filename] = sous_dossier
        dico = BulkPreprocessing.dico_hist(chroma_dict, loudness_resolution=self.loudness_resolution, N=self.N, overlap=self.overlap, verb=0)
        with open(self.picklefile, "wb") as f:
            pickle.dump((dico,grouping_dict), f)

    def pickle_dump_audio_dir2(self):
        chroma_dict = {}
        print(f"Traitement des fichiers dans le dossier : {self.audio_dir2}")
        for filename in os.listdir(self.audio_dir2):
            print(f"Traitement du fichier : {filename}")
            if filename.endswith(".csv"):
                file_path = os.path.join(self.audio_dir2, filename)
                df_csv = pd.read_csv(file_path)
                df_csv = df_csv.iloc[:, 1:]
                cols = df_csv.columns[1:]
                #print(df_csv.head())
                while (df_csv[cols].iloc[0] == 0).all():
                    df_csv = df_csv.iloc[1:].reset_index(drop=True)
                while (df_csv[cols].iloc[-1] == 0).all():
                    df_csv = df_csv.iloc[:-1].reset_index(drop=True)
                chroma = df_csv.iloc[:, 1:].values.T
                #print(f"Tableau de {filename} : {df_csv.head()}")
                #print(f"Matrice de {filename} : {chroma}")
                chroma_dict[filename] = chroma
        dico = BulkPreprocessing.dico_hist(chroma_dict, loudness_resolution=self.loudness_resolution, N=self.N, overlap=self.overlap, verb=0)
        with open(self.picklefile2, "wb") as f:
            pickle.dump(dico, f)
    
    def pickle_dump_classicalsde(self):
        chroma_dict = {}
        grouping_dict = {}
        compo_dict = {}
        for sous_dossier in [d for d in os.listdir(self.audio_dir) if os.path.isdir(os.path.join(self.audio_dir, d))]:
            sous_dossier_path = os.path.join(self.audio_dir, sous_dossier)
            composer_list = sous_dossier.split(',')
            composer = f"{composer_list[1]} {composer_list[0]} ({composer_list[2]} - {composer_list[3]})"
            print(f"Compositeur : {composer}")
            for sous_sous_dossier in [d2 for d2 in os.listdir(sous_dossier_path) if os.path.isdir(os.path.join(sous_dossier_path, d2))]:
                sous_sous_path = os.path.join(sous_dossier_path, sous_sous_dossier)
                for filename in os.listdir(sous_sous_path):
                    if filename.endswith('.csv'):
                        file_path = os.path.join(sous_sous_path, filename)
                        try:
                            df_csv = pd.read_csv(file_path)
                            df_csv = df_csv.iloc[:, 1:]
                            cols = df_csv.columns[1:]
                            while (df_csv[cols].iloc[0] == 0).all():
                                df_csv = df_csv.iloc[1:].reset_index(drop=True)
                            while (df_csv[cols].iloc[-1] == 0).all():
                                df_csv = df_csv.iloc[:-1].reset_index(drop=True)
                            chroma = df_csv.iloc[:, 1:].values.T
                            chroma_dict[file_path] = chroma
                            print(f"Traitement du fichier : {file_path}")
                            print(f"Informations : {sous_dossier}, {sous_sous_dossier}")
                            grouping_dict[file_path] = (sous_dossier, sous_sous_dossier)
                            compo_dict[file_path] = composer
                        except:
                            print(f"Erreur lors du traitement du fichier : {file_path}")
                            continue
        dico = BulkPreprocessing.dico_hist(chroma_dict, loudness_resolution=self.loudness_resolution, N=self.N, overlap=self.overlap, verb=0)
        with open(self.picklefile, "wb") as f:
            pickle.dump((dico, grouping_dict, compo_dict), f)

    
    def test2(self):
        with open(self.picklefile, "rb") as f:
            dico_cross_era_sup, grouping_dict, compo_dict = pickle.load(f)
        print(dico_cross_era_sup.keys())
        X = []
        etiquettes = []
        y = []
        groupe = []
        for file, histograms in dico_cross_era_sup.items():
            composer = compo_dict[file]
            etiquettes.append(file)
            matrice = np.vstack(histograms)
            X.append(matrice.flatten())
            y.append(composer)
            groupe.append(grouping_dict[file][1])

        X = np.array(X)
        print(f"Shape de X : {X.shape}")
        print(f"Shape de y : {len(y)}")
        print(f"Nombre de compositeurs : {len(set(y))}")
        print(f"Shape de groupe : {len(groupe)}")
        print("Comptage des classes :", pd.Series(y).value_counts())
        print(f"X : {X}")
        X_scaled = StandardScaler().fit_transform(X)
        y = np.array(y)
        periodes = np.array(groupe)
        morceaux = np.array(etiquettes)

        compteur = Counter(y)
        indices_a_garder = [i for i, label in enumerate(y) if compteur[label] > 1]

        X2 = X_scaled[indices_a_garder]
        y2 = y[indices_a_garder]
        groupe = [groupe[i] for i in indices_a_garder]
        etiquettes = [etiquettes[i] for i in indices_a_garder]

        reducer = LDA(n_components=3)
        reducer.fit(X2,y2)
        X_lda = reducer.transform(X_scaled)
        print(f"X_lda : {X_lda}")

        df_lda = pd.DataFrame(X_lda, columns=['LD1', 'LD2', 'LD3'])
        df_lda['composer'] = y
        df_lda['morceau'] = morceaux
        df_lda['groupe'] = periodes

        fig = px.scatter_3d(
            df_lda,
            x='LD1', y='LD2', z='LD3',
            color='composer',
            hover_data={'morceau': True, 'composer': True, 'groupe': True},
            title='Projection LDA 3D des morceaux par compositeur'
        )
        fig.update_traces(marker=dict(size=4, opacity=0.8))
        fig.update_traces(marker=dict(size=4))
        buttons = [
            dict(label='Tout masquer',
                method='restyle',
                args=['visible', ['legendonly'] * len(fig.data)]),
            
            dict(label='Tout afficher',
                method='restyle',
                args=['visible', [True] * len(fig.data)])
        ]

        fig.update_layout(
            updatemenus=[dict(type='buttons', showactive=True, buttons=buttons)]
        )
        fig.show()

        def test(self):
            with open(self.picklefile, "rb") as f:
                dico_cross_era_sup, grouping_dict = pickle.load(f)
            X = []
            etiquettes = []
            y = []
            groupe = []
            for file, histograms in dico_cross_era_sup.items():
                composer = BulkPreprocessing.get_composer_audio_dir(file)
                etiquettes.append(file)
                matrice = np.vstack(histograms)
                X.append(matrice.flatten())
                y.append(composer)
                groupe.append(grouping_dict[file])

            # with open(self.picklefile2, "rb") as f:
            #     dico_cross_era_2 = pickle.load(f)
            # for file, histograms in dico_cross_era_2.items():
            #     composer, date = BulkPreprocessing.get_data_audio_dir2(file)
            #     etiquettes.append(file)
            #     matrice = np.vstack(histograms)
            #     X.append(matrice.flatten())
            #     y.append(composer)
            #     groupe.append(date)

            X = np.array(X)
            print(f"Shape de X : {X.shape}")
            print(f"Shape de y : {len(y)}")
            print(f"Nombre de compositeurs : {len(set(y))}")
            print(f"Shape de groupe : {len(groupe)}")
            print("Comptage des classes :", pd.Series(y).value_counts())
            print(f"X : {X}")
            X_scaled = StandardScaler().fit_transform(X)
            y = np.array(y)
            periodes = np.array(groupe)
            morceaux = np.array(etiquettes)

            reducer = LDA(n_components=3, random_state=42)
            X_lda = reducer.fit_transform(X_scaled)
            print(f"X_lda : {X_lda}")

            df_lda = pd.DataFrame(X_lda, columns=['LD1', 'LD2', 'LD3'])
            df_lda['composer'] = y
            df_lda['morceau'] = morceaux
            df_lda['groupe'] = periodes

            fig = px.scatter_3d(
                df_lda,
                x='LD1', y='LD2', z='LD3',
                color='composer',
                hover_data={'morceau': True, 'composer': True, 'groupe': True},
                title='Projection LDA 3D des morceaux par compositeur'
            )
            fig.update_traces(marker=dict(size=4, opacity=0.8))
            fig.update_traces(marker=dict(size=4))
            buttons = [
                dict(label='Tout masquer',
                    method='restyle',
                    args=['visible', ['legendonly'] * len(fig.data)]),
                
                dict(label='Tout afficher',
                    method='restyle',
                    args=['visible', [True] * len(fig.data)])
            ]

            fig.update_layout(
                updatemenus=[dict(type='buttons', showactive=True, buttons=buttons)]
            )
            fig.show()
    
if __name__ == "__main__":
    picklefile = "data_classicalsde.pkl"
    picklefile2 = "data_musicmasterpieces.pkl"
    audio_dir = "audiofiles/classicalsde_csv"
    audio_dir2 = "audiofiles/100ClassicalMusicMasterpieces_csv"
    loudness_resolution = 60
    overlap = 0.5
    N = 4

    bulk_preprocessing = BulkPreprocessing(picklefile, picklefile2, audio_dir, audio_dir2, loudness_resolution, overlap, N)
    
    #bulk_preprocessing.pickle_dump_audio_dir()
    #bulk_preprocessing.pickle_dump_audio_dir2()
    bulk_preprocessing.pickle_dump_classicalsde()
    
    bulk_preprocessing.test2()

    
