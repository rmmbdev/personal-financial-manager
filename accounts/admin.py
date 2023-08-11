from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, MemberAccount


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        *BaseUserAdmin.fieldsets,  # original form fieldsets, expanded
        (  # new fieldset added on to the bottom
            'User fields',  # group heading of your choice; set to None for a blank space instead of a header
            {
                'fields': (
                    'mobile_number', 'birthday', 'user_type', 'profile_image', 'default_account_id'
                ),
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(MemberAccount)
