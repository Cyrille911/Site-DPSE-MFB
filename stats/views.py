import pandas as pd
import os
from django.shortcuts import render
from django.conf import settings

def lire_fichier_excel(nom_fichier_recherche):
    dossier_fichiers = os.path.join(settings.BASE_DIR, 'stats/data')  # Dossier où les fichiers sont déposés
    fichiers = [f for f in os.listdir(dossier_fichiers) if f.endswith('.xlsx') or f.endswith('.xls')]

    if not fichiers:
        return None, None
    
    # Recherche du fichier avec le nom précis
    fichier_trouve = None
    for fichier in fichiers:
        if nom_fichier_recherche in fichier:
            fichier_trouve = fichier
            break  # Sort de la boucle dès que le fichier est trouvé
    
    if fichier_trouve:
        fichier_path = os.path.join(dossier_fichiers, fichier_trouve)
        df = pd.read_excel(fichier_path)
        return df, fichier_trouve
    else:
        return None, None

def calculer_statistiques(df):
    stats = {}
    if df is not None:
        # Conversion en numérique et somme des valeurs (ignorer les erreurs)
        stats['total_recettes'] = pd.to_numeric(df.iloc[1, 1:], errors='coerce').sum()
        stats['total_depenses'] = pd.to_numeric(df.iloc[30, 1:], errors='coerce').sum()
        stats['solde_budgetaire'] = stats['total_recettes'] - stats['total_depenses']
    return stats

def afficher_donnees(request):
    # Définir le nom du fichier que vous recherchez
    nom_fichier_recherche = 'TOFE'  # Remplacez par le nom ou la partie du nom que vous voulez
    df, nom_fichier = lire_fichier_excel(nom_fichier_recherche)
    
    if df is None:
        return render(request, 'stats/stats.html', {'error': f"Aucun fichier Excel trouvé avec le nom '{nom_fichier_recherche}'."})
    
    stats = calculer_statistiques(df)
    donnees_html = df.to_html(classes='table table-striped', index=False)
    
    return render(request, 'stats/stats.html', {
        'nom_fichier': nom_fichier,
        'stats': stats,
        'donnees_html': donnees_html
    })
