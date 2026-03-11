# games/views.py
import chess.pgn
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages # Per mostrar missatges a l'usuari
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q # Per a consultes complexes OR
from django.core.paginator import Paginator # Per paginar
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse

from .models import Partida, Comentari, PerfilJugador
from .forms import PartidaForm, ComentariForm, ImportPGNForm, RegistreForm
 


def llista_partides(request):
    queryset = None
    
    if request.user.is_authenticated:
        
        try:
            # Obtenim el club de l'usuari actual
            perfil = request.user.perfiljugador
            meu_club = perfil.club

            # Construim la Query
            # Lògica:
            # - Públiques (PUB) -> Tothom
            # - Pujades per mi -> Jo
            # - Club (CLB) -> Només si qui la va pujar és del MEU MATEIX CLUB

            # Query complexa:
            queryset = Partida.objects.filter(
                Q(visibilitat=Partida.PUBLICA) | 
                Q(pujada_per=request.user) |
                # AQUÍ ESTÀ LA MÀGIA: Travessar de Partida -> User -> Perfil -> Club
                (Q(visibilitat=Partida.CLUB) & Q(pujada_per__perfiljugador__club=meu_club))
            ).distinct()

        except PerfilJugador.DoesNotExist:
            # Cas estrany: usuari sense perfil
            queryset = Partida.objects.filter(
                Q(visibilitat=Partida.PUBLICA) | Q(pujada_per=request.user)
            )
    else:
        # Usuaris anònims: Només Públiques
        queryset = Partida.objects.filter(visibilitat=Partida.PUBLICA)  

            # NOTA: Perquè això funcioni bé, la partida ha de saber a quin club pertany
            # l'usuari i 'propietari de la partida si la visibilitat es CLUB o PRIVADA
            
    # --- RESTA DEL CODI (FILTRES, PAGINACIÓ, RENDER) ---  
    # Cerca
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(blanc__icontains=query) | 
            Q(negre__icontains=query) | 
            Q(esdeveniment__icontains=query)
        )

    # Ordenació
    queryset = queryset.order_by('-data_partida', '-ronda')

    # Paginació
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'games/llista_partides.html', {'page_obj': page_obj, 'query': query}) 


@login_required
def detall_partida(request, partida_id):
    partida = get_object_or_404(Partida, pk=partida_id)
    
    if request.method == 'POST' and 'btn_comentari' in request.POST:
        form = ComentariForm(request.POST)
        if form.is_valid():
            comentari = form.save(commit=False)
            comentari.partida = partida
            comentari.autor = request.user
            comentari.save()
            return redirect('detall_partida', partida_id=partida.id)
    else:
        form = ComentariForm()

    comentaris = partida.comentaris.all().order_by('jugada_num', 'data_creacio')

    context = {
        'partida': partida,
        'comentaris': comentaris,
        'form': form
    }
    return render(request, 'games/detall_partida.html', context)

# @login_required
# def editar_partida(request, partida_id):
#     # Només el propietari pot editar
#     partida = get_object_or_404(Partida, pk=partida_id, pujada_per=request.user)

#     if request.method == 'POST':
#         form = PartidaForm(request.POST, instance=partida)
#         if form.is_valid():
#             form.save()
#             return redirect('detall_partida', partida_id=partida.id)
#     else:
#         form = PartidaForm(instance=partida)

#     return render(request, 'games/editar_partida.html', {'form': form, 'partida': partida})

@login_required
def esborrar_partida(request, partida_id):
    partida = get_object_or_404(Partida, pk=partida_id)

    # COMPROVACIÓ DE SEGURETAT
    if partida.pujada_per != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tens permís per esborrar aquesta partida.")

    if request.method == 'POST':
        partida.delete()
        return redirect('llista_partides')
    
    return render(request, 'games/confirmar_esborrat.html', {'partida': partida})


@login_required
def pujar_partida(request):
    if request.method == 'POST':
        form = PartidaForm(request.POST)
        if form.is_valid():
            partida = form.save(commit=False)
            partida.pujada_per = request.user
            partida.save()
            # Si tot va bé, anem al detall
            return redirect('detall_partida', partida_id=partida.id)
        else:
            # Si el formulari té errors, el tornem a mostrar
            return render(request, 'games/pujar_partida.html', {'form': form})
    else:
        # Si és GET (entrar normal), creem formulari buit
        form = PartidaForm()

    return render(request, 'games/pujar_partida.html', {'form': form})

@login_required
def esborrar_comentari(request, comentari_id):
    comentari = get_object_or_404(Comentari, pk=comentari_id)
    # Seguretat: Només l'autor pot esborrar
    if comentari.autor == request.user:
        partida_id = comentari.partida.id
        comentari.delete()
        return redirect('detall_partida', partida_id=partida_id)
    else:
        return HttpResponseForbidden("No tens permís per esborrar aquest comentari.")
    
@login_required
def editar_comentari(request, comentari_id):
    # Vista per editar via AJAX
    comentari = get_object_or_404(Comentari, pk=comentari_id)
    
    if comentari.autor != request.user:
        return JsonResponse({'success': False, 'error': 'No autoritzat'}, status=403)

    if request.method == 'POST':
        nou_text = request.POST.get('text', '')
        if nou_text:
            comentari.text = nou_text
            comentari.save()
            return JsonResponse({'success': True, 'text': comentari.text})
        return JsonResponse({'success': False, 'error': 'Text buit'}, status=400)
    

def registre(request):
    if request.method == 'POST':
        form = RegistreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistreForm()
    
    return render(request, 'games/registre.html', {'form': form})


@login_required
def nova_partida(request, partida_id=None):
    instancia = None
    if partida_id:
        # Mode Edició: Busquem la partida i comprovem propietat
        instancia = get_object_or_404(Partida, pk=partida_id, pujada_per=request.user)

    if request.method == 'POST':
        # Recollim dades
        pgn_text = request.POST.get('pgn_text')
        blanc = request.POST.get('blanc')
        negre = request.POST.get('negre')
        resultat = request.POST.get('resultat')
        esdeveniment = request.POST.get('esdeveniment')
        lloc = request.POST.get('lloc')
        ronda = request.POST.get('ronda')
        visibilitat = request.POST.get('visibilitat')
        # Recollim la data (l'usuari la veu com a YYYY-MM-DD, la guardem igual per consistència PGN)
        data_partida = request.POST.get('data_partida')

        if instancia:
            # Actualitzar existent
            partida = instancia
            partida.pgn_text = pgn_text
            partida.blanc = blanc
            partida.negre = negre
            partida.resultat = resultat
            partida.esdeveniment = esdeveniment
            partida.lloc = lloc
            partida.ronda = ronda
            partida.visibilitat = visibilitat
            partida.data_partida = data_partida
        else:
            # Crear nova
            partida = Partida(
                pgn_text=pgn_text, blanc=blanc, negre=negre, resultat=resultat,
                esdeveniment=esdeveniment, lloc=lloc, ronda=ronda, 
                visibilitat=visibilitat, data_partida=data_partida,
                pujada_per=request.user
            )
        
        partida.save()
        return redirect('detall_partida', partida_id=partida.id)

    # GET: Preparar dades per mostrar
    context = {}
    if instancia:
        context['partida'] = instancia
        context['title'] = "Editar Partida"
    else:
        context['partida'] = None
        context['title'] = "Nova Partida"

    return render(request, 'games/nova_partida.html', context)

@login_required
def importar_pgn(request):
    if request.method == 'POST':
        form = ImportPGNForm(request.POST, request.FILES)
        if form.is_valid():
            pgn_file = request.FILES['pgn_file']
            visibilitat = form.cleaned_data['visibilitat']
            
            # Llegim el fitxer com a text
            try:
                # Intentem decodificar utf-8 (estàndard)
                text = pgn_file.read().decode('utf-8')
            except UnicodeDecodeError:
                # Si falla, provem latin-1 (alguns fitxers vells)
                text = pgn_file.read().decode('latin-1')

            # Creem un objecte "virtual" per llegir el PGN
            pgn_io = io.StringIO(text)
            
            partides_creades = 0
            
            # Bucle per llegir cada partida del fitxer
            while True:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break # Ja no hi ha més partides
                
                # Obtenim el PGN d'aquesta partida específica
                exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
                pgn_string = game.accept(exporter)
                
                # Creem l'objecte Partida
                partida = Partida(
                    pgn_text=pgn_string,
                    pujada_per=request.user,
                    visibilitat=visibilitat
                )
                # Guardem (el model extreurà automàticament els noms, esdeveniment, etc.)
                partida.save()
                partides_creades += 1

            if partides_creades > 0:
                messages.success(request, f"S'han importat {partides_creades} partides correctament!")
                return redirect('llista_partides')
            else:
                messages.error(request, "No s'ha trobat cap partida vàlida al fitxer.")
    else:
        form = ImportPGNForm()

    return render(request, 'games/importar_pgn.html', {'form': form})


