from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from mock import patch, MagicMock

import authority
from authority import permissions
from authority.models import Permission
from authority.admin import PermissionAdmin
from authority.exceptions import NotAModel, UnsavedModelInstance
from authority.widgets import GenericForeignKeyRawIdWidget

# Load the form
from authority.forms import UserPermissionForm  # noqa


User = get_user_model()
FIXTURES = ["tests_custom.json"]
QUERY = Q(email="jezdez@github.com")


class UserPermission(permissions.BasePermission):
    checks = ("browse",)
    label = "user_permission"


authority.utils.register(User, UserPermission)


class GroupPermission(permissions.BasePermission):
    checks = ("browse",)
    label = "group_permission"


authority.utils.register(Group, GroupPermission)


class DjangoPermissionChecksTestCase(TestCase):
    """
    Django permission objects have certain methods that are always present,
    test those here.

    self.user will be given:
    - django permission add_user (test_add)
    - authority to delete_user which is him (test_delete)

    This permissions are given in the test case and not in the fixture, for
    later reference.
    """

    fixtures = FIXTURES

    def setUp(self):
        self.user = User.objects.get(QUERY)
        self.check = UserPermission(self.user)

    def test_no_permission(self):
        self.assertFalse(self.check.add_user())
        self.assertFalse(self.check.delete_user())
        self.assertFalse(self.check.delete_user(self.user))

    def test_add(self):
        # setup
        perm = DjangoPermission.objects.get(codename="add_user")
        self.user.user_permissions.add(perm)

        # test
        self.assertTrue(self.check.add_user())

    def test_delete(self):
        perm = Permission(
            user=self.user,
            content_object=self.user,
            codename="user_permission.delete_user",
            approved=True,
        )
        perm.save()

        # test
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))


class AssignBehaviourTest(TestCase):
    """
    self.user will be given:
    - permission add_user (test_add),
    - permission delete_user for him (test_delete),
    - all existing codenames permissions: a/b/c/d (test_all),
    """

    fixtures = FIXTURES

    def setUp(self):
        self.user = User.objects.get(QUERY)
        self.group1, _ = Group.objects.get_or_create(name="Test Group 1")
        self.group2, _ = Group.objects.get_or_create(name="Test Group 2")
        self.group3, _ = Group.objects.get_or_create(name="Test Group 2")
        self.check = UserPermission(self.user)

    def test_add(self):
        result = self.check.assign(check="add_user")

        self.assertTrue(isinstance(result[0], DjangoPermission))
        self.assertTrue(self.check.add_user())

    def test_assign_to_group(self):
        result = UserPermission(group=self.group1).assign(
            check="delete_user", content_object=self.user
        )

        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Permission)
        self.assertTrue(UserPermission(group=self.group1).delete_user(self.user))

    def test_assign_to_group_does_not_overwrite_other_group_permission(self):
        UserPermission(group=self.group1).assign(
            check="delete_user", content_object=self.user
        )
        UserPermission(group=self.group2).assign(
            check="delete_user", content_object=self.user
        )
        self.assertTrue(UserPermission(group=self.group2).delete_user(self.user))
        self.assertTrue(UserPermission(group=self.group1).delete_user(self.user))

    def test_assign_to_group_does_not_fail_when_two_group_perms_exist(self):
        for group in self.group1, self.group2:
            perm = Permission(
                group=group,
                content_object=self.user,
                codename="user_permission.delete_user",
                approved=True,
            )
            perm.save()

        try:
            UserPermission(group=self.group3).assign(
                check="delete_user", content_object=self.user
            )
        except MultipleObjectsReturned:
            self.fail("assign() should not have raised this exception")

    def test_delete(self):
        result = self.check.assign(content_object=self.user, check="delete_user",)

        self.assertTrue(isinstance(result[0], Permission))
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))

    def test_all(self):
        result = self.check.assign(content_object=self.user)
        self.assertTrue(isinstance(result, list))
        self.assertTrue(self.check.browse_user(self.user))
        self.assertTrue(self.check.delete_user(self.user))
        self.assertTrue(self.check.add_user(self.user))
        self.assertTrue(self.check.change_user(self.user))


class GenericAssignBehaviourTest(TestCase):
    """
    self.user will be given:
    - permission add (test_add),
    - permission delete for him (test_delete),
    """

    fixtures = FIXTURES

    def setUp(self):
        self.user = User.objects.get(QUERY)
        self.check = UserPermission(self.user)

    def test_add(self):
        result = self.check.assign(check="add", generic=True)

        self.assertTrue(isinstance(result[0], DjangoPermission))
        self.assertTrue(self.check.add_user())

    def test_delete(self):
        result = self.check.assign(
            content_object=self.user, check="delete", generic=True,
        )

        self.assertTrue(isinstance(result[0], Permission))
        self.assertFalse(self.check.delete_user())
        self.assertTrue(self.check.delete_user(self.user))


class AssignExceptionsTest(TestCase):
    """
    Tests that exceptions are thrown if assign() was called with inconsistent
    arguments.
    """

    fixtures = FIXTURES

    def setUp(self):
        self.user = User.objects.get(QUERY)
        self.check = UserPermission(self.user)

    def test_unsaved_model(self):
        try:
            self.check.assign(content_object=User())
        except UnsavedModelInstance:
            return True
        self.fail()

    def test_not_model_content_object(self):
        try:
            self.check.assign(content_object="fail")
        except NotAModel:
            return True
        self.fail()


class SmartCachingTestCase(TestCase):
    """
    The base test case for all tests that have to do with smart caching.
    """

    fixtures = FIXTURES

    def setUp(self):
        # Create a user.
        self.user = User.objects.get(QUERY)

        # Create a group.
        self.group = Group.objects.create()
        self.group.user_set.add(self.user)

        # Make the checks
        self.user_check = UserPermission(user=self.user)
        self.group_check = GroupPermission(group=self.group)

        # Ensure we are using the smart cache.
        settings.AUTHORITY_USE_SMART_CACHE = True

    def tearDown(self):
        ContentType.objects.clear_cache()

    def _old_user_permission_check(self):
        # This is what the old, pre-cache system would check to see if a user
        # had a given permission.
        return Permission.objects.user_permissions(
            self.user, "foo", self.user, approved=True, check_groups=True,
        )

    def _old_group_permission_check(self):
        # This is what the old, pre-cache system would check to see if a user
        # had a given permission.
        return Permission.objects.group_permissions(
            self.group, "foo", self.group, approved=True,
        )


class PerformanceTest(SmartCachingTestCase):
    """
    Tests that permission are actually cached and that the number of queries
    stays constant.
    """

    def test_has_user_perms(self):
        # Show that when calling has_user_perms multiple times no additional
        # queries are done.

        # Make sure the has_user_perms check does not get short-circuited.
        assert not self.user.is_superuser
        assert self.user.is_active

        # Regardless of how many times has_user_perms is called, the number of
        # queries is the same.
        # Content type and permissions (2 queries)
        with self.assertNumQueries(3):
            for _ in range(5):
                # Need to assert it so the query actually gets executed.
                assert not self.user_check.has_user_perms(
                    "foo", self.user, True, False,
                )

    def test_group_has_perms(self):
        with self.assertNumQueries(2):
            for _ in range(5):
                assert not self.group_check.has_group_perms("foo", self.group, True,)

    def test_has_user_perms_check_group(self):
        # Regardless of the number groups permissions, it should only take one
        # query to check both users and groups.
        # Content type and permissions (2 queries)
        with self.assertNumQueries(3):
            self.user_check.has_user_perms(
                "foo", self.user, approved=True, check_groups=True,
            )

    def test_invalidate_user_permissions_cache(self):
        # Show that calling invalidate_permissions_cache will cause extra
        # queries.
        # For each time invalidate_permissions_cache gets called, you
        # will need to do one query to get content type and one to get
        # the permissions.
        with self.assertNumQueries(6):
            for _ in range(5):
                assert not self.user_check.has_user_perms(
                    "foo", self.user, True, False,
                )

            # Invalidate the cache to show that a query will be generated when
            # checking perms again.
            self.user_check.invalidate_permissions_cache()
            ContentType.objects.clear_cache()

            # One query to re generate the cache.
            for _ in range(5):
                assert not self.user_check.has_user_perms(
                    "foo", self.user, True, False,
                )

    def test_invalidate_group_permissions_cache(self):
        # Show that calling invalidate_permissions_cache will cause extra
        # queries.
        # For each time invalidate_permissions_cache gets called, you
        # will need to do one query to get content type and one to get
        with self.assertNumQueries(4):
            for _ in range(5):
                assert not self.group_check.has_group_perms("foo", self.group, True,)

            # Invalidate the cache to show that a query will be generated when
            # checking perms again.
            self.group_check.invalidate_permissions_cache()
            ContentType.objects.clear_cache()

            # One query to re generate the cache.
            for _ in range(5):
                assert not self.group_check.has_group_perms("foo", self.group, True,)

    def test_has_user_perms_check_group_multiple(self):
        # Create a permission with just a group.
        Permission.objects.create(
            content_type=Permission.objects.get_content_type(User),
            object_id=self.user.pk,
            codename="foo",
            group=self.group,
            approved=True,
        )
        # By creating the Permission objects the Content type cache
        # gets created.

        # Check the number of queries.
        with self.assertNumQueries(2):
            assert self.user_check.has_user_perms("foo", self.user, True, True)

        # Create a second group.
        new_group = Group.objects.create(name="new_group")
        new_group.user_set.add(self.user)

        # Create a permission object for it.
        Permission.objects.create(
            content_type=Permission.objects.get_content_type(User),
            object_id=self.user.pk,
            codename="foo",
            group=new_group,
            approved=True,
        )

        self.user_check.invalidate_permissions_cache()

        # Make sure it is the same number of queries.
        with self.assertNumQueries(2):
            assert self.user_check.has_user_perms("foo", self.user, True, True)


class GroupPermissionCacheTestCase(SmartCachingTestCase):
    """
    Tests that peg expected behaviour
    """

    def test_has_user_perms_with_groups(self):
        perms = self._old_user_permission_check()
        self.assertEqual([], list(perms))

        # Use the new cached user perms to show that the user does not have the
        # perms.
        can_foo_with_group = self.user_check.has_user_perms(
            "foo", self.user, approved=True, check_groups=True,
        )
        self.assertFalse(can_foo_with_group)

        # Create a permission with just that group.
        perm = Permission.objects.create(
            content_type=Permission.objects.get_content_type(User),
            object_id=self.user.pk,
            codename="foo",
            group=self.group,
            approved=True,
        )

        # Old permission check
        perms = self._old_user_permission_check()
        self.assertEqual([perm], list(perms))

        # Invalidate the cache.
        self.user_check.invalidate_permissions_cache()
        can_foo_with_group = self.user_check.has_user_perms(
            "foo", self.user, approved=True, check_groups=True,
        )
        self.assertTrue(can_foo_with_group)

    def test_has_group_perms_no_user(self):
        # Make sure calling has_user_perms on a permission that does not have a
        # user does not throw any errors.
        can_foo_with_group = self.group_check.has_group_perms(
            "foo", self.user, approved=True,
        )
        self.assertFalse(can_foo_with_group)

        perms = self._old_group_permission_check()
        self.assertEqual([], list(perms))

        # Create a permission with just that group.
        perm = Permission.objects.create(
            content_type=Permission.objects.get_content_type(Group),
            object_id=self.group.pk,
            codename="foo",
            group=self.group,
            approved=True,
        )

        # Old permission check
        perms = self._old_group_permission_check()
        self.assertEqual([perm], list(perms))

        # Invalidate the cache.
        self.group_check.invalidate_permissions_cache()

        can_foo_with_group = self.group_check.has_group_perms(
            "foo", self.group, approved=True,
        )
        self.assertTrue(can_foo_with_group)


class AddPermissionTestCase(TestCase):
    def test_add_permission_permission_denied_is_403(self):
        user = get_user_model().objects.create(username="foo", email="foo@example.com",)
        user.set_password("pw")
        user.save()

        assert self.client.login(username="foo@example.com", password="pw")
        url = reverse(
            "authority-add-permission-request",
            kwargs={"app_label": "foo", "module_name": "Bar", "pk": 1,},
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 403)


class PermissionAdminForDBFieldTests(SimpleTestCase):
    """
    Tests for correct behavior of PermissionAdmin.formfield_for_dbfield
    Borrwed and adapted from `tests/admin_widgets/tests.py`
    """

    def assertFormfield(self, model, fieldname, widgetclass, **admin_overrides):
        """
        Helper to call formfield_for_dbfield for a given model and field name
        and verify that the returned formfield is appropriate.
        """
        # Override any settings on the model admin
        class MyModelAdmin(PermissionAdmin):
            pass
        for k in admin_overrides:
            setattr(MyModelAdmin, k, admin_overrides[k])

        # Construct the admin, and ask it for a formfield
        ma = MyModelAdmin(model, admin.site)
        ff = ma.formfield_for_dbfield(model._meta.get_field(fieldname), request=None)
        widget = ff.widget

        self.assertIsInstance(widget, widgetclass)

        # Return the formfield so that other tests can continue
        return ff

    def test_raw_id_GenericForeignKey(self):
        self.assertFormfield(Permission, 'object_id', 
                             GenericForeignKeyRawIdWidget,
                             raw_id_fields=['object_id'])


class GenericForeignKeyRawIdWidgetTests(SimpleTestCase):
    """
    Sanity checks the code in a simple fashion checking flow and making sure
    that mocked objects are called.
    """
    def get_mock_request(self):
        """
        Helper for obtaining a mock request object.
        """
        mock_request = MagicMock()
        mock_request.path_info = "/myapp/one/two/three/four/"
        mock_request.resolver_match = MagicMock()
        mock_request.resolver_match.app_name = "myapp"
        return mock_request

    def test_construction(self):
        with patch('authority.widgets.forms.TextInput.__init__') as mock_text_input:
            widget = GenericForeignKeyRawIdWidget("ct_field", "cts", "attrs", "request")
            self.assertEqual(widget.ct_field, "ct_field")
            self.assertEqual(widget.cts, "cts")
            self.assertEqual(widget.request, "request")
            mock_text_input.assert_called_with(widget, "attrs")

    def test_render(self):
        with patch('authority.widgets.forms.TextInput.__init__') as mock_text_input:
            with patch('authority.widgets.forms.TextInput.render') as mock_text_input_render:
                mock_text_input_render.return_value = "mock_text_input_rendering"
                mock_get_for_model = MagicMock()
                mock_get_for_model.return_value = MagicMock()
                mock_get_for_model.return_value.id = "id"
                mock_models = MagicMock()
                ct = MagicMock()
                ct._meta = MagicMock()
                ct._meta.app_label = "app_label"
                ct._meta.object_name = "Object_Name"
                cts = (ct,)
                with patch("authority.tests.ContentType.objects.get_for_model", mock_get_for_model):
                    mock_get_for_model.return_value = MagicMock()
                    mock_get_for_model.return_value.id = "id"
                    mock_request = self.get_mock_request()
                    widget = GenericForeignKeyRawIdWidget("ct_field", cts, "attrs", mock_request)
                    attrs = dict()
                    markup = widget.render("name", "value", attrs)
                    mock_text_input_render.assert_called()
                    self.assertEqual(markup, 
                    """mock_text_input_rendering
<script type="text/javascript">
function showGenericRelatedObjectLookupPopup(ct_select, triggering_link, url_base) {
    var url = content_types[ct_select.options[ct_select.selectedIndex].value];
    if (url != undefined) {
        triggering_link.href = url_base + url;
        return showRelatedObjectLookupPopup(triggering_link);
    }
    return false;
}
</script>

                <a href="../../../../"
                    class="related-lookup"
                    id="lookup_id_name"
                    onclick="return showGenericRelatedObjectLookupPopup(
                        document.getElementById('id_ct_field'), this, '../../../../');">
            <img src="None/admin/img/selector-search.gif" width="16" height="16" alt="Lookup" /></a>
        <script type="text/javascript">
        var content_types = new Array();
        content_types[id] = 'app_label/object_name/';
        </script>
        """)

    def test_get_context(self):
        with patch('authority.widgets.forms.TextInput.__init__') as mock_text_input:
            with patch('authority.widgets.forms.TextInput.get_context') as mock_get_context:
                widget = GenericForeignKeyRawIdWidget("ct_field", "cts", "attrs", "request")
                widget.get_context("name", "value", "attrs")
                mock_get_context.assert_called_with(widget, "name", "value", "attrs")

    def test_url_parameters(self):
        with patch('authority.widgets.forms.TextInput.__init__') as mock_text_input:
            widget = GenericForeignKeyRawIdWidget("ct_field", "cts", "attrs", "request")
            self.assertEqual(widget.url_parameters(), {})

    def test_get_related_url(self):
        with patch('authority.widgets.forms.TextInput.__init__') as mock_text_input:
            widget = GenericForeignKeyRawIdWidget("ct_field", "cts", "attrs", None)
            self.assertIsNone(widget.request)
            self.assertEqual(widget.get_related_url(), "../../../")
        with patch('authority.widgets.forms.TextInput.__init__') as mock_text_input:
            mock_request = self.get_mock_request()
            widget = GenericForeignKeyRawIdWidget("ct_field", "cts", "attrs", mock_request)
            self.assertIsNotNone(widget.request)
            self.assertEqual(widget.get_related_url(), "../../../../")
