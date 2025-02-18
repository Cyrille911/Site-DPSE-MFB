from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta
import six

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) +
            six.text_type(timestamp) +
            six.text_type(user.is_active)
        )
    
    def _get_timestamp_from_token(self, token):
        """
        Extrait le timestamp du jeton. 
        Utilisez la méthode de base pour récupérer le timestamp si cela est applicable.
        """
        try:
            # Essayez d'extraire le timestamp du jeton
            return super()._get_timestamp_from_token(token)
        except AttributeError:
            # Si la méthode n'est pas disponible, retournez None
            return None
    
    def check_token(self, user, token):
        """
        Vérifie si le jeton est valide et n'est pas expiré.
        Ici, le jeton expire après 24 heures.
        """
        # Utiliser le super pour obtenir le timestamp
        timestamp = self._get_timestamp_from_token(token)
        if timestamp:
            # Définir la durée d'expiration
            expiration_time = timestamp + timedelta(hours=24)  # Changer à 24 heures
            if timezone.now() > expiration_time:
                return False  # Le jeton a expiré
        return super().check_token(user, token)

account_activation_token = AccountActivationTokenGenerator()
