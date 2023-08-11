from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models


class User(AbstractUser):
    mobile_number = models.CharField(max_length=11, null=True, blank=True)
    birthday = models.DateTimeField(null=True, blank=True)
    user_type = models.CharField(max_length=100, null=False, blank=False)
    profile_image = models.ImageField(blank=True, null=True)
    profile_avatar_url = models.CharField(default="images/avatars/avatar10.png", max_length=2000)
    default_account_id = models.IntegerField(null=True, blank=True)
    is_enabled = models.BooleanField(null=False, blank=False, default=True)


class MemberAccount(models.Model):
    user_accounts = models.ManyToManyField(get_user_model(), related_name="user_accounts", blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING, null=True, blank=True)

    class Meta:
        db_table = 'MemberAccounts'

    def __str__(self):
        return self.title


class Invitation(models.Model):
    statuses = [
        ("a", "accepted"),
        ("d", "declined"),
        ("p", "pending"),
    ]
    account = models.ForeignKey(MemberAccount, on_delete=models.DO_NOTHING, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    status = models.CharField(max_length=1, choices=statuses, null=False, blank=False, default="p")

    class Meta:
        db_table = 'Invitations'

    def __str__(self):
        return "{} -> {}".format(self.account.id, self.user.username)
