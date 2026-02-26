from django.shortcuts import render
import pandas as pd
import os
import re
import json
from django.http import JsonResponse
from django.conf import settings

def dashboard_TOFE(request):
    # Chemin vers le fichier Excel (TOFE, inchangé)
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'tofe.xlsx')
    
    # Charger la première feuille
    df_feuille1 = pd.read_excel(file_path, sheet_name=0)  # Première feuille

    # KPI 1 : Recettes 2023 + Évolution
    recettes_2023 = df_feuille1.loc[df_feuille1['Catégorie'] == 'RECETTES', 2023].values[0]
    recettes_2022 = df_feuille1.loc[df_feuille1['Catégorie'] == 'RECETTES', 2022].values[0]
    evol_recettes = ((recettes_2023 - recettes_2022) / recettes_2022) * 100 if recettes_2022 != 0 else 0
    
    # KPI 2 : Solde Budgétaire Global 2023 + Évolution
    solde_2023 = df_feuille1.loc[df_feuille1['Catégorie'] == "SOLDE BUDGETAIRE GLOBAL", 2023].values[0]
    solde_2022 = df_feuille1.loc[df_feuille1['Catégorie'] == "SOLDE BUDGETAIRE GLOBAL", 2022].values[0]
    evol_solde = ((solde_2023 - solde_2022) / solde_2022) * 100 if solde_2022 != 0 else 0
    
    # KPI 3 : Financement Net 2023 + Évolution
    financement_net_2023 = df_feuille1.loc[df_feuille1['Catégorie'] == 'FINANCEMENT NET', 2023].values[0]
    financement_net_2022 = df_feuille1.loc[df_feuille1['Catégorie'] == 'FINANCEMENT NET', 2022].values[0]
    evol_financement_net = ((financement_net_2023 - financement_net_2022) / financement_net_2022) * 100 if financement_net_2022 != 0 else 0
    
    # KPI 4 : Financement Extérieur 2023 + Évolution
    financement_ext_2023 = df_feuille1.loc[df_feuille1['Catégorie'] == 'Financement extérieur', 2023].values[0]
    financement_ext_2022 = df_feuille1.loc[df_feuille1['Catégorie'] == 'Financement extérieur', 2022].values[0]
    evol_financement_ext = ((financement_ext_2023 - financement_ext_2022) / financement_ext_2022) * 100 if financement_ext_2022 != 0 else 0
    
    years = [2018, 2019, 2020, 2021, 2022, 2023]
    chart_recettes = df_feuille1.loc[df_feuille1['Catégorie'] == 'RECETTES', years].values[0].tolist()
    chart_solde = df_feuille1.loc[df_feuille1['Catégorie'] == 'SOLDE BUDGETAIRE GLOBAL', years].values[0].tolist()
    chart_financement_net = df_feuille1.loc[df_feuille1['Catégorie'] == 'FINANCEMENT NET', years].values[0].tolist()
    chart_financement_ext = df_feuille1.loc[df_feuille1['Catégorie'] == 'Financement extérieur', years].values[0].tolist()
    
    # Debug
    print("chart_recettes :", chart_recettes)
    print("chart_solde :", chart_solde)
    print("chart_financement_net :", chart_financement_net)
    print("chart_financement_ext :", chart_financement_ext)
    
    # Données pour le tableau
    all_data = {}
    for index, row in df_feuille1.iterrows():
        categorie = row['Catégorie']
        if pd.notna(categorie):  # Ignorer les lignes vides
            all_data[categorie] = row[years].tolist()

    table_data = df_feuille1.fillna('').to_dict(orient='records')
    
    context = {
        'recettes_2023': recettes_2023,
        'evol_recettes': evol_recettes,
        'solde_2023': solde_2023,
        'evol_solde': evol_solde,
        'financement_net_2023': financement_net_2023,
        'evol_financement_net': evol_financement_net,
        'financement_ext_2023': financement_ext_2023,
        'evol_financement_ext': evol_financement_ext,
        'chart_labels': years,
        'chart_recettes': chart_recettes,
        'chart_solde': chart_solde,
        'chart_financement_net': chart_financement_net,
        'chart_financement_ext': chart_financement_ext,
        'all_data': all_data,
        'table_data': table_data,
        'years': years,
    }
    return render(request, 'stats/dashboard_TOFE.html', context)


# Vue pour le dashboard des douanes

def douanes_dashboard(request):
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'douanes.xlsx')
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names
    
    tableaux = []
    for i, sheet_name in enumerate(sheet_names, 1):
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        if not df.empty:
            table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {i}"
            tableaux.append({'id': i, 'name': table_name})
    
    context = {
        'tableaux': tableaux,
    }
    return render(request, 'stats/douanes_dashboard.html', context)


# Nouvelle vue AJAX pour récupérer les données d’un tableau spécifique
def get_tableau_data(request):
    tableau_id = request.GET.get('tableau_id')
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'douanes.xlsx')
    
    try:
        df = pd.read_excel(file_path, sheet_name=int(tableau_id) - 1, header=None)
        if not df.empty and len(df) > 1:
            table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {tableau_id}"
            potential_headers = df.iloc[1]
            headers = potential_headers.tolist()
            if isinstance(headers[-1], str):
                headers[1:-2] = list(map(int, headers[1:-2]))
            else:
                headers[1:] = list(map(int, headers[1:]))
            table_data = df.iloc[2:].reset_index(drop=True)
            table_data.columns = headers
            
            years = [2019, 2020, 2021, 2022, 2023]
            existing_years = [year for year in years if year in table_data.columns]
            all_data = {}
            first_col_name = table_data.columns[0]
            for index, row in table_data.iterrows():
                if pd.notna(row[first_col_name]) and isinstance(row[first_col_name], str):
                    category = row[first_col_name].strip()
                    all_data[category] = row[existing_years].tolist()
            table_data_list = [[row[first_col_name]] + [row.get(year, '') for year in existing_years] for index, row in table_data.iterrows()]

            response_data = {
                'id': tableau_id,
                'name': table_name,
                'all_data': all_data,
                'table_data': table_data_list,
                'years': existing_years,
            }
            return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def financements_dashboard(request):
    # Chemin vers le fichier Excel des financements
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'financements.xlsx')
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names
    
    # Générer la liste des tableaux disponibles
    tableaux = []
    for i, sheet_name in enumerate(sheet_names, 1):
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        if not df.empty:
            table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {i}"
            tableaux.append({'id': i, 'name': table_name})
    
    context = {
        'tableaux': tableaux,
    }
    return render(request, 'stats/financements_dashboard.html', context)

# Vue pour le dashboard des financements

import os
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render

import os
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render

def get_financements_data(request):
    tableau_id = request.GET.get('tableau_id')
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'financements.xlsx')
    
    try:
        # Lire le fichier avec dtype=str pour éviter les conversions en float
        df = pd.read_excel(file_path, sheet_name=int(tableau_id) - 1, header=None, dtype=str)
        if not df.empty and len(df) > 1:
            table_name = df.iloc[0, 0] if pd.notna(df.iloc[0, 0]) and isinstance(df.iloc[0, 0], str) else f"Tableau {tableau_id}"
            potential_headers = df.iloc[1]
            # Nettoyer les en-têtes : supprimer les .0 des nombres
            headers = [str(header).replace('.0', '') if str(header).endswith('.0') else str(header) for header in potential_headers.tolist()]
            
            # Prendre toutes les colonnes après la première comme "années"
            existing_years = headers[1:]
            
            table_data = df.iloc[2:].reset_index(drop=True)
            table_data.columns = headers
            
            all_data = {}
            first_col_name = table_data.columns[0]
            for index, row in table_data.iterrows():
                if pd.notna(row[first_col_name]) and isinstance(row[first_col_name], str):
                    category = row[first_col_name].strip()
                    all_data[category] = row[existing_years].tolist()
            
            table_data_list = [[row[first_col_name]] + [row.get(year, '') for year in existing_years] for index, row in table_data.iterrows()]

            response_data = {
                'id': tableau_id,
                'name': table_name,
                'all_data': all_data,
                'table_data': table_data_list,
                'years': existing_years,
            }
            print(f"Tableau {tableau_id} - Years: {existing_years}")  # Log pour debug
            return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)