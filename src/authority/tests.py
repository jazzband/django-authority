from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission as DjangoPermission

import authority
from authority import permissions
from authority.models import Permission

class UserPermission(permissions.BasePermission):
    checks = ('browse',)
    label = 'user_permission'
authority.register(User, UserPermission)

class BehaviourTest(TestCase):
    '''
    self.user will be given:
    - django permission add_user (test_add)
    - authority to delete_user which is him (test_delete)

    This permissions are given in the test case and not in the fixture, for
    later reference.
    '''
    
    fixtures = ['tests.json',]

    def setUp(self):
        self.user = User.objects.get(username='jezdez')
        self.check = UserPermission(self.user)

    def test_no_permission(self):
        self.assertFalse(self.check.add_user())
        self.assertFalse(self.check.delete_user())
        self.assertFalse(self.check.delete_user(self.user))

    def test_add(self):
        # setup
        perm = DjangoPermission.objects.get(codename='add_user')
        self.user.user_permissions.add(perm)

        # test
        self.assertTrue(self.check.add_user())

    def test_delete(self):
        perm = Permission(
            user=self.user,
            content_object=self.user,
            codename='user_permission.delete_user',
            approved=True
        )
        perm.save()

        # test
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))
