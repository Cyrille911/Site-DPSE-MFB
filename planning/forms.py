# planning/forms.py
from django import forms
from .models import PreuveRealisation


class PaoStatusForm(forms.Form):
    STATUT_CHOICES = [
        ('Non entamé', 'Non entamé'),
        ('En cours', 'En cours'),
        ('Suspendu', 'Suspendu'),
        ('Achevé', 'Achevé'),
    ]
    statut = forms.ChoiceField(choices=STATUT_CHOICES, label="Statut", widget=forms.Select(attrs={'class': 'form-select'}))


class PreuveRealisationForm(forms.ModelForm):
    class Meta:
        model = PreuveRealisation
        fields = ['type', 'fichier', 'url', 'description', 'annee']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select', 'id': 'id_type_preuve'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description de la preuve'}),
            'annee': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        type_preuve = cleaned_data.get('type')
        fichier = cleaned_data.get('fichier')
        url = cleaned_data.get('url')

        if type_preuve == 'lien':
            if not url:
                self.add_error('url', 'Un lien est requis pour ce type de preuve.')
        else:
            if not fichier and not self.instance.pk:
                self.add_error('fichier', 'Un fichier est requis pour ce type de preuve.')

        # Validation des extensions selon le type
        if fichier and type_preuve != 'lien':
            ext = fichier.name.rsplit('.', 1)[-1].lower() if '.' in fichier.name else ''
            allowed = {
                'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'],
                'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
                'video': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
            }
            if ext not in allowed.get(type_preuve, []):
                self.add_error('fichier', f"Extension '.{ext}' non autorisée pour le type '{type_preuve}'. Extensions acceptées : {', '.join(allowed.get(type_preuve, []))}")

        return cleaned_data
