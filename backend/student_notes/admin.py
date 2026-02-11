from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Standard, Subject, Topic, MasterNote, AINote

admin.site.register(Standard)
admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(MasterNote)
admin.site.register(AINote)