# Dictionnaire de traduction et de regroupement des permissions

# Structure :
# {
#     'app_label': {
#         'nom_groupe': 'Nom affiché du groupe (ex: Actualités)',
#         'permissions': {
#             'codename': 'Libellé traduit (ex: Peut publier une actualité)',
#         }
#     }
# }

PERMISSIONS_CONFIG = {
    'news': {
        'label': 'Actualités',
        'permissions': {
            'add_news': 'Ajouter une actualité',
            'change_news': 'Modifier une actualité',
            'delete_news': 'Supprimer une actualité',
            'view_news': 'Voir les actualités (admin)',
            'add_newscomment': 'Ajouter un commentaire',
            'change_newscomment': 'Modifier un commentaire',
            'delete_newscomment': 'Supprimer un commentaire',
        }
    },
    'blog': {
        'label': 'Blog',
        'permissions': {
            'add_blog': 'Créer un article de blog',
            'change_blog': 'Modifier un article de blog',
            'delete_blog': 'Supprimer un article de blog',
            'view_blog': 'Voir les articles (admin)',
            'add_blogcomment': 'Ajouter un commentaire',
            'change_blogcomment': 'Modifier un commentaire',
            'delete_blogcomment': 'Supprimer un commentaire',
        }
    },
    'documents': {
        'label': 'Documents',
        'permissions': {
            # MFB
            'add_document_mfb': 'Ajouter un document MFB',
            'change_document_mfb': 'Modifier un document MFB',
            'delete_document_mfb': 'Supprimer un document MFB',
            'view_document_mfb': 'Voir les documents MFB',
            # Planification
            'add_document_dpse_planification': 'Ajouter un document Planification',
            'change_document_dpse_planification': 'Modifier un document Planification',
            'delete_document_dpse_planification': 'Supprimer un document Planification',
            'view_document_dpse_planification': 'Voir les documents Planification',
            # Suivi Evaluation
            'add_document_dpse_suivi_evaluation': 'Ajouter un document Suivi & Évaluation',
            'change_document_dpse_suivi_evaluation': 'Modifier un document Suivi & Évaluation',
            'delete_document_dpse_suivi_evaluation': 'Supprimer un document Suivi & Évaluation',
            'view_document_dpse_suivi_evaluation': 'Voir les documents Suivi & Évaluation',
            # Statistiques
            'add_document_dpse_statistiques': 'Ajouter un document Statistiques',
            'change_document_dpse_statistiques': 'Modifier un document Statistiques',
            'delete_document_dpse_statistiques': 'Supprimer un document Statistiques',
            'view_document_dpse_statistiques': 'Voir les documents Statistiques',
            # Qualité
            'add_document_dpse_qualite': 'Ajouter un document Qualité',
            'change_document_dpse_qualite': 'Modifier un document Qualité',
            'delete_document_dpse_qualite': 'Supprimer un document Qualité',
            'view_document_dpse_qualite': 'Voir les documents Qualité',
            # Archives
            'add_document_dpse_archives': 'Ajouter un document Archives',
            'change_document_dpse_archives': 'Modifier un document Archives',
            'delete_document_dpse_archives': 'Supprimer un document Archives',
            'view_document_dpse_archives': 'Voir les documents Archives',
        }
    },
    'planning': {
        'label': 'Planning & Activités',
        'permissions': {
            'add_planaction': 'Créer un Plan d\'Action',
            'change_planaction': 'Modifier un Plan d\'Action',
            'delete_planaction': 'Supprimer un Plan d\'Action',
            'view_planaction': 'Voir les Plans d\'Action',
            
            'add_activite': 'Ajouter une activité',
            'change_activite': 'Modifier une activité',
            'delete_activite': 'Supprimer une activité',
            'view_activite': 'Voir les activités',
        }
    },
    'general': {
        'label': 'Général / FAQ',
        'permissions': {
            'add_discussion': 'Ajouter une question FAQ',
            'change_discussion': 'Modifier une question FAQ',
            'delete_discussion': 'Supprimer une question FAQ',
        }
    },
    'users': {
        'label': 'Gestion Utilisateurs',
        'permissions': {
            'add_user': 'Ajouter un utilisateur',
            'change_user': 'Modifier un utilisateur',
            'delete_user': 'Supprimer un utilisateur',
            'view_user': 'Voir la liste des utilisateurs',
        }
    }
}

# Définition des permissions par défaut pour chaque rôle
# Ces permissions seront automatiquement attribuées aux groupes correspondants
DEFAULT_ROLE_PERMISSIONS = {
    'SuiveurEvaluateur': [
        # News
        'add_news', 'change_news', 'delete_news', 'view_news',
        'add_newscomment', 'change_newscomment', 'delete_newscomment',
        # Blog
        'add_blog', 'change_blog', 'delete_blog', 'view_blog',
        'add_blogcomment', 'change_blogcomment', 'delete_blogcomment',
        # Planning & Activités
        'add_planaction', 'change_planaction', 'delete_planaction', 'view_planaction',
        'add_activite', 'change_activite', 'delete_activite', 'view_activite',
        # FAQ
        'add_discussion', 'change_discussion', 'delete_discussion',
        # Users
        'add_user', 'view_user', 'change_user', 'delete_user',
        # Documents - Tous les accès complets
        'add_document_mfb', 'change_document_mfb', 'delete_document_mfb', 'view_document_mfb',
        'add_document_dpse_planification', 'change_document_dpse_planification', 'delete_document_dpse_planification', 'view_document_dpse_planification',
        'add_document_dpse_suivi_evaluation', 'change_document_dpse_suivi_evaluation', 'delete_document_dpse_suivi_evaluation', 'view_document_dpse_suivi_evaluation',
        'add_document_dpse_statistiques', 'change_document_dpse_statistiques', 'delete_document_dpse_statistiques', 'view_document_dpse_statistiques',
        'add_document_dpse_qualite', 'change_document_dpse_qualite', 'delete_document_dpse_qualite', 'view_document_dpse_qualite',
        'add_document_dpse_archives', 'change_document_dpse_archives', 'delete_document_dpse_archives', 'view_document_dpse_archives',
    ],
    'PointFocal': [
        # Planning & Activités (Cœur de métier)
        'add_planaction', 'change_planaction', 'view_planaction',
        'add_activite', 'change_activite', 'view_activite',
        # Documents (Peut généralement ajouter des docs techniques)
        'add_document_dpse_planification', 'change_document_dpse_planification', 'view_document_dpse_planification',
        'add_document_dpse_suivi_evaluation', 'change_document_dpse_suivi_evaluation', 'view_document_dpse_suivi_evaluation',
        # Lecture seule sur le reste
        'view_news', 'view_blog',
        'view_document_mfb',
    ],
    'Responsable': [
        # Planning & Activités (Supervision)
        'view_planaction', 'view_activite',
        # News/Blog (Contribution possible)
        'add_news', 'change_news', 'view_news',
        'add_blog', 'change_blog', 'view_blog',
        # Documents
        'view_document_mfb', 'add_document_mfb',
        'view_document_dpse_planification',
        'view_document_dpse_suivi_evaluation',
        'view_document_dpse_statistiques',
        'view_document_dpse_qualite',
        'view_document_dpse_archives',
    ],
    'CabinetMFB': [
        # Vision globale
        'view_planaction', 'view_activite',
        'view_news', 'view_blog',
        # Documents stratégiques
        'view_document_mfb', 'add_document_mfb', 'change_document_mfb',
        'view_document_dpse_planification',
        'view_document_dpse_suivi_evaluation',
        'view_document_dpse_statistiques',
    ],
    'Visiteur': [
        # Accès public restreint (géré hors permissions souvent, mais explicite ici)
    ]
}

def get_readable_permission_name(app_label, codename):
    """Retourne le nom lisible d'une permission ou None si non configurée."""
    app_config = PERMISSIONS_CONFIG.get(app_label)
    if app_config:
        return app_config['permissions'].get(codename)
    return None

def get_grouped_permissions(permissions_queryset):
    """
    Organise les permissions fournies en groupes lisibles.
    Retourne une liste de dicts:
    [
        {
            'label': 'Actualités',
            'perms': [Permission objects...]
        },
        ...
    ]
    Les permissions ont un attribut dynamique 'translated_name'.
    """
    grouped = {}
    
    for perm in permissions_queryset:
        app_label = perm.content_type.app_label
        codename = perm.codename
        
        # On ne traite que ce qui est dans notre config
        if app_label in PERMISSIONS_CONFIG:
            readable_name = get_readable_permission_name(app_label, codename)
            if readable_name:
                # On ajoute l'attribut traduit à l'objet permission (temporaire pour la vue)
                perm.translated_name = readable_name
                
                group_label = PERMISSIONS_CONFIG[app_label]['label']
                
                if group_label not in grouped:
                    grouped[group_label] = []
                grouped[group_label].append(perm)
    
    # Conversion en liste triée
    result = []
    for label, perms in grouped.items():
        # Trier les permissions par nom traduit à l'intérieur du groupe
        perms.sort(key=lambda x: x.translated_name)
        result.append({
            'label': label,
            'perms': perms
        })
        
    # Trier les groupes par label
    result.sort(key=lambda x: x['label'])
    return result
