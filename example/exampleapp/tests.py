from django.urls import reverse
from django.test import TestCase

from authority.compat import get_user_model


class AddPermissionTestCase(TestCase):
    def test_add_permission_permission_denied_is_403(self):
        user = get_user_model().objects.create(
            username='foo',
            email='foo@example.com',
        )
        user.set_password('pw')
        user.save()

        assert self.client.login(username='foo@example.com', password='pw')
        url = reverse(
            'authority-add-permission-request',
            kwargs={
                'app_label': 'foo',
                'module_name': 'Bar',
                'pk': 1,
            },
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)
