from django.db import models
from accounts.models import MemberAccount, User


class Tag(models.Model):
    account = models.ForeignKey(MemberAccount, on_delete=models.DO_NOTHING, null=True, blank=True)
    title = models.CharField(max_length=1000, null=False, blank=False)

    class Meta:
        db_table = 'Tags'
        ordering = ['title']

    def __str__(self):
        return self.title


class Transaction(models.Model):
    account = models.ForeignKey(MemberAccount, on_delete=models.DO_NOTHING, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="transaction_tags")
    title = models.CharField(max_length=1000, null=False, blank=False)
    date = models.DateTimeField(null=False, blank=False)
    value_raw = models.IntegerField(blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'Transactions'
        ordering = ['date', 'title']

    def __str__(self):
        return "{} *** {} - {}".format(self.date, ", ".join([t["title"] for t in self.tags.all().values()]), self.title)
