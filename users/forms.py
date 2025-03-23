from django import forms
from .models import User

# Formulaire d'inscription pour les membres
class InscriptionMembreForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input100', 'placeholder': 'Mot de passe'}), 
        label="Mot de passe"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input100', 'placeholder': 'Confirmez le mot de passe'}), 
        label="Confirmez le mot de passe"
    )
    
    # Ajout du champ 'role' avec les choix
    ROLE_CHOICES = (
        ('responsable', 'Responsable'),
        ('point_focal', 'Point Focal'),
        ('suiveur_evaluateur', 'Suiveur Evaluateur'),
        ('cabinet', 'Cabinet MFB'),
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        label="Rôle", 
        initial='point_focal',
        widget=forms.Select(attrs={'class': 'input100'})
    )

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email', 'phone_number', 'program', 'entity', 'function', 'role', 'password', 'confirm_password', 'photo']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Nom'}),
            'first_name': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Prénom'}),
            'email': forms.EmailInput(attrs={'class': 'input100', 'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Numéro de téléphone'}),
            'program': forms.Select(attrs={'class': 'input100'}),
            'entity': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Entité'}),
            'function': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Fonction'}),
            'photo': forms.FileInput(attrs={'class': 'input100'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Vérification de la correspondance des mots de passe
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hacher le mot de passe
        user.username = self.cleaned_data['email']  # Utiliser l'email comme username
        if commit:
            user.save()
        return user

# Formulaire d'inscription pour les visiteurs
class InscriptionVisiteurForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input100', 'placeholder': 'Mot de passe'}), 
        label="Mot de passe"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input100', 'placeholder': 'Confirmez le mot de passe'}), 
        label="Confirmez le mot de passe"
    )

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email', 'phone_number', 'profession', 'interest', 'password', 'confirm_password', 'photo']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Nom'}),
            'first_name': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Prénom'}),
            'email': forms.EmailInput(attrs={'class': 'input100', 'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Numéro de téléphone'}),
            'profession': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Profession'}),
            'interest': forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Intérêt'}),
            'photo': forms.FileInput(attrs={'class': 'input100'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Vérification de la correspondance des mots de passe
        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        # Attribuer automatiquement le rôle 'visiteur'
        cleaned_data['role'] = 'visiteur'
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hacher le mot de passe
        user.username = self.cleaned_data['email']  # Utiliser l'email comme username
        user.role = 'visiteur'  # Définir explicitement le rôle
        if commit:
            user.save()
        return user

class ConnexionForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'input100', 'placeholder': 'Votre email'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'input100', 'placeholder': 'Votre mot de passe'})
    )

# Remplacer la classe ProfileUpdateForm par celle-ci:

class ProfileUpdateForm(forms.ModelForm):
    # Champs communs à tous les utilisateurs
    first_name = forms.CharField(
        label="Prénom",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Prénom', 'required': True})
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Nom', 'required': True})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'input100', 'placeholder': 'Email', 'required': True})
    )
    phone_number = forms.CharField(
        label="Numéro de téléphone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Numéro de téléphone'})
    )
    photo = forms.ImageField(
        label="Photo de profil",
        required=False,
        widget=forms.FileInput(attrs={'class': 'input100'})
    )

    # Champs spécifiques aux membres
    program = forms.ChoiceField(
        label="Programme",
        choices=User.PROGRAM_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'input100'})
    )
    entity = forms.CharField(
        label="Entité",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Entité'})
    )
    function = forms.CharField(
        label="Fonction",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Fonction'})
    )

    # Champs spécifiques aux visiteurs
    profession = forms.CharField(
        label="Profession",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Profession'})
    )
    interest = forms.CharField(
        label="Intérêt",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100', 'placeholder': 'Intérêt'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'photo', 
                  'program', 'entity', 'function', 'profession', 'interest']

    def __init__(self, *args, **kwargs):
        # Récupérer l'utilisateur pour conditionner les champs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si l'utilisateur est un membre ou un rôle similaire, masquer les champs visiteurs
        if user and user.role.lower().rstrip('s') in ['membre', 'responsable', 'point_focal', 'cabinet']:
            del self.fields['profession']
            del self.fields['interest']
        # Si l'utilisateur est un visiteur, masquer les champs membres
        elif user and user.role.lower().rstrip('s') == 'visiteur':
            del self.fields['program']
            del self.fields['entity']
            del self.fields['function']

