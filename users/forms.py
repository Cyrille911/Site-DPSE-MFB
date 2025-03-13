from django import forms
from .models import User

# Formulaire d'inscription pour les membres
class InscriptionMembreForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")
    
    # Ajout du champ 'role' avec les choix
    ROLE_CHOICES = (
        ('membre', 'Membre simple'),
        ('responsable', 'Responsable'),
        ('point_focal', 'Point Focal'),
        ('cabinet', 'Cabinet MFB'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Rôle", initial='membre')

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'program', 'entity', 'function', 'email', 'phone_number', 'password', 'confirm_password', 'photo', 'role']

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

        # Pas besoin d'attribuer 'role' ici, il vient du formulaire
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hacher le mot de passe
        user.username = self.cleaned_data['email']  # Par exemple, utiliser l'email comme username
        if commit:
            user.save()
        return user

# Formulaire d'inscription pour les visiteurs
class InscriptionVisiteurForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'profession', 'interest', 'email', 'phone_number', 'password', 'confirm_password', 'photo']

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

class ConnexionForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

class ProfileUpdateForm(forms.ModelForm):
    # Champs communs à tous les utilisateurs
    first_name = forms.CharField(
        label="Prénom",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'input100', 'required': True})
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'input100', 'required': True})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'input100', 'required': True})
    )
    phone_number = forms.CharField(
        label="Numéro de téléphone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100'})
    )
    photo = forms.ImageField(
        label="Photo de profil",
        required=False,
        widget=forms.FileInput(attrs={'class': 'input100'})
    )

    # Champs spécifiques aux membres
    program = forms.CharField(
        label="Programme",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100'})
    )
    entity = forms.CharField(
        label="Entité",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100'})
    )
    function = forms.CharField(
        label="Fonction",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100'})
    )

    # Champs spécifiques aux visiteurs
    profession = forms.CharField(
        label="Profession",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100'})
    )
    interest = forms.CharField(
        label="Intérêt",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input100'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'photo', 
                  'program', 'entity', 'function', 'profession', 'interest']

    def __init__(self, *args, **kwargs):
        # Récupérer l’utilisateur pour conditionner les champs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si l’utilisateur est un membre, masquer les champs visiteurs
        if user and user.role == 'membre':
            del self.fields['profession']
            del self.fields['interest']
        # Si l’utilisateur est un visiteur, masquer les champs membres
        elif user and user.role == 'visiteur':
            del self.fields['program']
            del self.fields['entity']
            del self.fields['function']
            