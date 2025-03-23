# planning/forms.py
from django import forms

class PaoStatusForm(forms.Form):
    STATUT_CHOICES = [
        ('Non entamé', 'Non entamé'),
        ('En cours', 'En cours'),
        ('Suspendu', 'Suspendu'),
        ('Achevé', 'Achevé'),
    ]
    statut = forms.ChoiceField(choices=STATUT_CHOICES, label="Statut", widget=forms.Select(attrs={'class': 'form-select'}))