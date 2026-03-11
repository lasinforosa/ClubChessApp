from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import chess.pgn
import io

class Partida(models.Model):
    # Camps que s'omplen automàticament del PGN
    blanc = models.CharField("Blanques", max_length=100, blank=True)
    negre = models.CharField("Negres", max_length=100, blank=True)
    resultat = models.CharField("Resultat", max_length=15, blank=True)
    data_partida = models.CharField("Data", max_length=20, blank=True)
    esdeveniment = models.CharField("Torneig", max_length=200, blank=True)
    lloc = models.CharField("Lloc", max_length=200, blank=True) # Nou camp
    ronda = models.CharField("Ronda", max_length=20, blank=True) # Nou camp
    
    # El cor de la partida: el PGN pur
    pgn_text = models.TextField("PGN Complet")

    # Metadades de l'aplicació
    pujada_per = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_creacio = models.DateTimeField(auto_now_add=True)
    
    # Visibilitat
    PUBLICA = 'PUB'
    CLUB = 'CLB'
    PRIVADA = 'PRI'
    OPCIONS_VISIBILITAT = [
        (PUBLICA, 'Pública (visible per tothom)'),
        (CLUB, 'Club (només membres)'),
        (PRIVADA, 'Privada (només jo)'),
    ]
    visibilitat = models.CharField(max_length=3, choices=OPCIONS_VISIBILITAT, default=CLUB)

    def __str__(self):
        return f"{self.blanc} vs {self.negre} ({self.data_partida} )"

    def save(self, *args, **kwargs):
        if self.pgn_text:
            pgn_io = io.StringIO(self.pgn_text)
            try:
                game = chess.pgn.read_game(pgn_io)
                if game:
                    headers = game.headers
                    
                    # LÒGICA MILLORADA: Només omplim si el camp està buit
                    if not self.blanc: self.blanc = headers.get("White", "?")
                    if not self.negre: self.negre = headers.get("Black", "?")
                    if not self.resultat: self.resultat = headers.get("Result", "*")
                    if not self.data_partida: self.data_partida = headers.get("Date", "????.??.??")
                    if not self.esdeveniment: self.esdeveniment = headers.get("Event", "Partida Amistosa")
                    if not self.lloc: self.lloc = headers.get("Site", "?")
                    if not self.ronda: self.ronda = headers.get("Round", "?")
                    
            except Exception as e:
                print(f"Error llegint PGN: {e}")
                
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.blanc} vs {self.negre} ({self.data_partida})"


class Comentari(models.Model):
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='comentaris')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    # Opcional: Per saber a quina jugada fa referència el comentari
    jugada_num = models.IntegerField(null=True, blank=True) 
    data_creacio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentari de {self.autor} a {self.partida}"
    

class Club(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    adreca = models.CharField(max_length=200, blank=True)
    provincia = models.CharField(max_length=50, blank=True)
    federacio = models.CharField(max_length=50, blank=True, default="FCE")
    telefon = models.CharField(max_length=20, blank=True)
    web = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    # Camp per identificar el club de "proves"
    is_default = models.BooleanField(default=False) 

    def __str__(self):
        return self.nom
    
class PerfilJugador(models.Model):
    usuari = models.OneToOneField(User, on_delete=models.CASCADE)
    nom_complet = models.CharField("Nom complet (com a la federació)", max_length=100)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    fcat_id = models.CharField("ID Federació Catalana", max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.nom_complet
    
# MAGICA: Crear perfil automàticament quan es crea un usuari nou
@receiver(post_save, sender=User)
def crear_perfil_usuari(sender, instance, created, **kwargs):
    if created:
        # Assignem el club "SENSE_CLUB" per defecte si existeix
        club_default = Club.objects.filter(is_default=True).first()
        PerfilJugador.objects.create(
            usuari=instance, 
            nom_complet=instance.username, # Per defecte agafa el username
            club=club_default
        )
