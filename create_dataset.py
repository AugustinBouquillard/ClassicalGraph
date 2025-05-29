import subprocess
import os

errors = []

def run_sonic_annotator(input_audio_path, output_csv_path):
    sonic_annotator_dir = r"C:\Log_inst\NNLS Chroma Plugin\sonic-annotator-1.6-win32\sonic-annotator-1.6-win32"
    sonic_annotator_exe = os.path.join(sonic_annotator_dir, "sonic-annotator.exe")

    cmd = [
        sonic_annotator_exe,
        "-d", "vamp:nnls-chroma:nnls-chroma:chroma",
        "-w", "csv",
        "--csv-stdout",
        "--force",
        input_audio_path
    ]

    # Ouvrir le fichier de sortie en écriture
    with open(output_csv_path, 'w', encoding='utf-8') as outfile:
        # Exécuter la commande et rediriger la sortie standard vers le fichier CSV
        subprocess.run(cmd, cwd=sonic_annotator_dir, stdout=outfile, check=True)

def process_audio_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    audio_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(audio_extensions):
            print(f"Processing file: {filename}")
            input_audio_path = os.path.join(input_folder, filename)
            output_csv_name = os.path.splitext(filename)[0] + '.csv'
            output_csv_path = os.path.join(output_folder, output_csv_name)
            if os.path.exists(output_csv_path):
                print(f"Skipping {output_csv_name} (already exists)")
                continue
            else:
                try:
                    run_sonic_annotator(input_audio_path, output_csv_path)
                except:
                    errors.append((input_audio_path, output_csv_path))

def process_all_files(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for racine, sous_dossiers, _ in os.walk(input_folder):
        for sous_dossier in sous_dossiers:
            sous_dossier_path = os.path.join(racine, sous_dossier)
            output_sous_dossier = os.path.join(output_folder, sous_dossier)
            print(f"Processing folder: {sous_dossier_path}")
            process_audio_folder(sous_dossier_path, output_sous_dossier)

def process_all_all_files(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    audio_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
    for racine, sous_dossiers, _ in os.walk(input_folder):
            for sous_dossier in sous_dossiers:
                print(f"Processing folder: {sous_dossier}")
                input_audio_path = os.path.join(racine, sous_dossier)
                output_csv_path = os.path.join(output_folder, sous_dossier)
                print(f"Processing file: {input_audio_path}")
                print(f"Output CSV path: {output_csv_path}")
                process_all_files(input_audio_path, output_csv_path)

def process_classicalde(input_folder, output_folder):
        for racine, sous_dossiers, _ in os.walk(input_folder):
            print(f"Traitement du dossier : {racine}")
            for sous_dossier in sous_dossiers:
                print(f"Traitement du sous-dossier : {sous_dossier}")
                for racine2, sous_sous_dossiers, _ in os.walk(os.path.join(racine, sous_dossier)):
                    print(f"Traitement du sous-dossier de racine : {racine2}")
                    for sous_sous_dossier in sous_sous_dossiers:
                        print(f"Traitement du sous-sous-dossier : {sous_sous_dossier}")
                        input_path = os.path.join(racine2,sous_sous_dossier)
                        output_path = os.path.join(output_folder, sous_dossier, sous_sous_dossier)
                        print(f"Input path: {input_path}")
                        print(f"Output path: {output_path}")
                        process_audio_folder(input_path, output_path)



# if __name__ == "__main__":
#     input_audio = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\Beethoven_symphonie_8_allegro_vivace_con_brio.mp3"
#     output_csv = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\csv\coucou24.csv"
    
#     run_sonic_annotator(input_audio, output_csv)

# if __name__ == "__main__":
#     input_folder = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\MusopenCollectionAsFlac"
#     output_folder = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\MusopenCollectionAsFlac_csv"
    
#     process_all_files(input_folder, output_folder)

# if __name__ == "__main__":
#     input_folder = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\100ClassicalMusicMasterpieces"
#     output_folder = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\100ClassicalMusicMasterpieces_csv"
#     process_audio_folder(input_folder, output_folder)

if __name__ == "__main__":
    input_folder = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\classicalsde"
    output_folder = r"C:\Users\PCAJM\ClassicalGraph\audiofiles\classicalsde_csv"
    process_classicalde(input_folder, output_folder)
    print(f"Erreurs : {errors}")