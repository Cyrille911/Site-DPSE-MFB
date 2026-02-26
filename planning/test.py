from django.test import TestCase
from django.contrib.auth.models import User, Group
from .models import PlanAction, Effet, Produit, Action, Activite, ActivityLog

class ActiviteTestCase(TestCase):
    def setUp(self):
        # Créer des utilisateurs
        self.pf_user = User.objects.create_user(username='pf', email='pf@example.com', password='test')
        self.resp_user = User.objects.create_user(username='resp', email='resp@example.com', password='test')
        self.se_user = User.objects.create_user(username='se', email='se@example.com', password='test')
        se_group = Group.objects.create(name='SuiveurEvaluateur')
        self.se_user.groups.add(se_group)

        # Créer une hiérarchie
        self.plan = PlanAction.objects.create(titre="Test Plan", horizon=3, annee_debut=2025)
        self.effet = Effet.objects.create(plan=self.plan, titre="Effet Test")
        self.produit = Produit.objects.create(effet=self.effet, titre="Produit Test")
        self.action = Action.objects.create(produit=self.produit, titre="Action Test")
        self.activite = Activite.objects.create(
            action=self.action,
            titre="Test Activité",
            type="Réforme",
            indicateur_label="Indicateur",
            indicateur_reference="IND001",
            cibles=[10, 20, 30],
            realisation=[0, 0, 0],
            couts=[100, 200, 300],
            point_focal=self.pf_user,
            responsable=self.resp_user,
        )

    def test_validation_by_responsable(self):
        self.assertEqual(self.activite.status, 'Draft')
        self.activite.validate_by_responsable(self.resp_user)
        self.activite.refresh_from_db()
        self.assertEqual(self.activite.status, 'Validated')

    def test_submit_to_se(self):
        self.activite.status = 'Validated'
        self.activite.save(user=self.resp_user)
        self.activite.submit_to_se(self.resp_user)
        self.activite.refresh_from_db()
        self.assertEqual(self.activite.status, 'Submitted_SE')

    def test_email_notification(self):
        self.activite.status = 'Validated'
        self.activite.save(user=self.resp_user)
        self.assertTrue(ActivityLog.objects.filter(activite=self.activite, action='Validated').exists())
        # Vérifie manuellement les logs console pour l'email avec EMAIL_BACKEND='console'

    def test_filter_by_status(self):
        response = self.client.login(username='pf', password='test')
        response = self.client.get(f'/planification/pao/{self.plan.id}/manage-activities/?status=Draft')
        self.assertContains(response, self.activite.titre)
