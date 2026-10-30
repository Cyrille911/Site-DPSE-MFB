import os

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def _data_file(name):
    """Chemin d'un fichier de données (nom exact, sensible à la casse sous Linux)."""
    return os.path.join(DATA_DIR, name)


def _lister_tableaux(file_path):
    """Liste des feuilles d'un classeur : [{'id': n, 'name': titre}]."""
    tableaux = []
    for i, sheet_name in enumerate(pd.ExcelFile(file_path).sheet_names, 1):
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        if not df.empty:
            table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {i}"
            tableaux.append({'id': i, 'name': table_name})
    return tableaux


def _tableau_id(request, file_path):
    """Numéro de tableau demandé, validé par rapport au nombre de feuilles."""
    try:
        tableau_id = int(request.GET.get('tableau_id', ''))
    except ValueError:
        raise ValueError("Paramètre 'tableau_id' manquant ou invalide.")
    nb_feuilles = len(pd.ExcelFile(file_path).sheet_names)
    if not 1 <= tableau_id <= nb_feuilles:
        raise ValueError(f"Tableau {tableau_id} introuvable ({nb_feuilles} tableaux disponibles).")
    return tableau_id


def _valeur_json(valeur):
    """Convertit les valeurs pandas (NaN, numpy) en valeurs sérialisables en JSON."""
    if pd.isna(valeur):
        return None
    return valeur.item() if hasattr(valeur, 'item') else valeur


def dashboard_TOFE(request):
    df_feuille1 = pd.read_excel(_data_file('TOFE.xlsx'), sheet_name=0)

    def ligne(categorie, colonnes):
        return df_feuille1.loc[df_feuille1['Catégorie'] == categorie, colonnes].values[0]

    def evolution(actuel, precedent):
        return ((actuel - precedent) / precedent) * 100 if precedent != 0 else 0

    # KPI : valeur 2023 et évolution par rapport à 2022
    recettes_2023, recettes_2022 = ligne('RECETTES', 2023), ligne('RECETTES', 2022)
    solde_2023, solde_2022 = ligne('SOLDE BUDGETAIRE GLOBAL', 2023), ligne('SOLDE BUDGETAIRE GLOBAL', 2022)
    financement_net_2023, financement_net_2022 = ligne('FINANCEMENT NET', 2023), ligne('FINANCEMENT NET', 2022)
    financement_ext_2023, financement_ext_2022 = ligne('Financement extérieur', 2023), ligne('Financement extérieur', 2022)

    years = [2018, 2019, 2020, 2021, 2022, 2023]

    # Données pour les graphiques et le tableau
    all_data = {}
    for _, row in df_feuille1.iterrows():
        categorie = row['Catégorie']
        if pd.notna(categorie):
            all_data[categorie] = [_valeur_json(v) for v in row[years].tolist()]

    context = {
        'recettes_2023': recettes_2023,
        'evol_recettes': evolution(recettes_2023, recettes_2022),
        'solde_2023': solde_2023,
        'evol_solde': evolution(solde_2023, solde_2022),
        'financement_net_2023': financement_net_2023,
        'evol_financement_net': evolution(financement_net_2023, financement_net_2022),
        'financement_ext_2023': financement_ext_2023,
        'evol_financement_ext': evolution(financement_ext_2023, financement_ext_2022),
        'chart_labels': years,
        'chart_recettes': ligne('RECETTES', years).tolist(),
        'chart_solde': ligne('SOLDE BUDGETAIRE GLOBAL', years).tolist(),
        'chart_financement_net': ligne('FINANCEMENT NET', years).tolist(),
        'chart_financement_ext': ligne('Financement extérieur', years).tolist(),
        'all_data': all_data,
        'table_data': df_feuille1.fillna('').to_dict(orient='records'),
        'years': years,
    }
    return render(request, 'stats/dashboard_TOFE.html', context)


# Vue pour le dashboard des douanes
def douanes_dashboard(request):
    context = {'tableaux': _lister_tableaux(_data_file('douanes.xlsx'))}
    return render(request, 'stats/douanes_dashboard.html', context)


# Vue AJAX pour récupérer les données d'un tableau des douanes
def get_tableau_data(request):
    file_path = _data_file('douanes.xlsx')
    try:
        tableau_id = _tableau_id(request, file_path)
        df = pd.read_excel(file_path, sheet_name=tableau_id - 1, header=None)
        if df.empty or len(df) < 2:
            return JsonResponse({'error': f"Le tableau {tableau_id} ne contient pas de données."}, status=404)

        table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {tableau_id}"
        headers = df.iloc[1].tolist()
        if isinstance(headers[-1], str):
            headers[1:-2] = list(map(int, headers[1:-2]))
        else:
            headers[1:] = list(map(int, headers[1:]))
        table_data = df.iloc[2:].reset_index(drop=True)
        table_data.columns = headers

        years = [2019, 2020, 2021, 2022, 2023]
        existing_years = [year for year in years if year in table_data.columns]
        first_col_name = table_data.columns[0]
        all_data = {}
        for _, row in table_data.iterrows():
            if pd.notna(row[first_col_name]) and isinstance(row[first_col_name], str):
                all_data[row[first_col_name].strip()] = [_valeur_json(v) for v in row[existing_years].tolist()]
        table_data_list = [
            [_valeur_json(row[first_col_name])] + [_valeur_json(row.get(year, '')) for year in existing_years]
            for _, row in table_data.iterrows()
        ]

        return JsonResponse({
            'id': tableau_id,
            'name': table_name,
            'all_data': all_data,
            'table_data': table_data_list,
            'years': existing_years,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# Vue pour le dashboard des financements
def financements_dashboard(request):
    context = {'tableaux': _lister_tableaux(_data_file('financements.xlsx'))}
    return render(request, 'stats/financements_dashboard.html', context)


# Vue AJAX pour récupérer les données d'un tableau des financements
def get_financements_data(request):
    file_path = _data_file('financements.xlsx')
    try:
        tableau_id = _tableau_id(request, file_path)
        # Lire le fichier avec dtype=str pour éviter les conversions en float
        df = pd.read_excel(file_path, sheet_name=tableau_id - 1, header=None, dtype=str)
        if df.empty or len(df) < 2:
            return JsonResponse({'error': f"Le tableau {tableau_id} ne contient pas de données."}, status=404)

        table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {tableau_id}"
        # Nettoyer les en-têtes : supprimer le suffixe .0 des nombres
        headers = [str(h)[:-2] if str(h).endswith('.0') else str(h) for h in df.iloc[1].tolist()]
        # Toutes les colonnes après la première sont des "années"
        existing_years = headers[1:]

        table_data = df.iloc[2:].reset_index(drop=True)
        table_data.columns = headers
        first_col_name = table_data.columns[0]

        all_data = {}
        for _, row in table_data.iterrows():
            if pd.notna(row[first_col_name]) and isinstance(row[first_col_name], str):
                all_data[row[first_col_name].strip()] = [_valeur_json(v) for v in row[existing_years].tolist()]
        table_data_list = [
            [_valeur_json(row[first_col_name])] + [_valeur_json(row.get(year, '')) for year in existing_years]
            for _, row in table_data.iterrows()
        ]

        return JsonResponse({
            'id': tableau_id,
            'name': table_name,
            'all_data': all_data,
            'table_data': table_data_list,
            'years': existing_years,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
