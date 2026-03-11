from django.contrib import admin  
from django.contrib.auth.admin import UserAdmin  
from django.contrib.auth.models import User 
from .models import Partida, Comentari, Club, PerfilJugador

@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ('blanc', 'negre', 'resultat', 'data_partida', 'visibilitat', 'data_creacio')
    list_filter = ('visibilitat', 'data_creacio')
    search_fields = ('blanc', 'negre', 'esdeveniment')

admin.site.register(Comentari)

admin.site.register(Club)

# Afegim el perfil dins de l'admin d'usuari (més còmode)
class PerfilInline(admin.StackedInline):
    model = PerfilJugador
    can_delete = False
    verbose_name_plural = 'Perfil Jugador'

class CustomUserAdmin(UserAdmin):
    inlines = (PerfilInline,)

# Re-registrem l'UserAdmin amb el nou inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)