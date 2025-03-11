from django import forms
from .models import User

# Formulaire d'inscription pour les membres
class InscriptionMembreForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'program', 'entity', 'function', 'email', 'phone_number', 'password', 'confirm_password', 'photo']
    
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
        if password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        # Attribuer automatiquement le rôle 'membre'
        cleaned_data['role'] = 'membre'
        return cleaned_data

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