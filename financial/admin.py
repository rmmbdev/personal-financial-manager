from django.contrib import admin
from .models import Tag, Transaction

# Register your models here.
admin.site.register([Tag, Transaction])
