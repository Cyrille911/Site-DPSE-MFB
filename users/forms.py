from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

# Formulaire d'inscription pour les membres
class InscriptionMembreForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'program', 'entity', 'function', 'email', 'phone_number', 'password', 'photo']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Hachage du mot de passe
        if commit:
            user.save()
        return user

# Formulaire d'inscription pour les visiteurs
class InscriptionVisiteurForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmez le mot de passe")

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'profession', 'interest', 'email', 'phone_number', 'password', 'photo']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Hachage du mot de passe
        if commit:
            user.save()
        return user

# Formulaire de connexion
class ConnexionForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre adresse email'}),
        required=True
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Votre mot de passe'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Email"
