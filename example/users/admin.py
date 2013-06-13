from django.contrib.auth.admin import UserAdmin
from example.users.User


admin.site.register(User, UserAdmin)
