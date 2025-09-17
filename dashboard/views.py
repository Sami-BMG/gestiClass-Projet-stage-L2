from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages as django_messages
from datetime import datetime,timedelta
from django.utils import timezone
import calendar
from accounts.models import User, Student, Teacher, Module, Result, Timetable, InfoMessage, ContactMessage, FAQ, SchoolInfo,Note
from django.db import models
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from chartjs.views.lines import BaseLineChartView
from django.db.models import Avg
from django.db import transaction 
from django.views.decorators.http import require_GET, require_POST

from django.utils import timezone
from datetime import timedelta
from accounts.models import Timetable 






User = get_user_model()

@login_required
def home(request):
    print(request.user.profil, "home")
    """Vue principale qui redirige vers le tableau de bord approprié"""
    if not request.user.is_authenticated:
        return redirect('login')
        # Rediriger en fonction du rôle de l'utilisateur
    if request.user.has_perm('accounts.peut_acceder_au_dashboard'):
        return redirect('dashboard:dashboard')
    return redirect('accounts:login')
    
    
    
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profil') and user.profil == 'admin'

# ============ VUES DES TABLEAUX DE BOARD ============


@login_required
def dashboard(request):
    """Tableau de bord pour les administrateurs"""
    #if not request.user.is_administrator():
        #django_messages.error(request, "Accès réservé aux administrateurs.")
        #return redirect('accounts:login')
    
    # Récupérer les données pour le dashboard
    context = {
        'title': 'Tableau de bord',
        'user': request.user,
        'student_count': User.objects.filter(profil='student').count(),
        'teacher_count': User.objects.filter(profil='teacher').count(),
        'module_count': Module.objects.count(),
        'new_contacts_count': ContactMessage.objects.count(),
        'modules': Module.objects.all(),
        'teachers': Teacher.objects.all(),
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        'week_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'student_info': InfoMessage.objects.filter(audience='student').first(),
        'teacher_info': InfoMessage.objects.filter(audience='teacher').first(),
        'show_module_chart': True,
    }
    return render(request, 'dashboard/dashboard.html', context)


@csrf_exempt
@require_POST
@login_required
def save_info_message(request):
    """Sauvegarder ou mettre à jour un message d'information"""
    if not request.user.is_administrator():
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        audience = data.get('audience')
        title = data.get('title')
        content = data.get('content')
        
        # Valider les données
        if not all([audience, title, content]):
            return JsonResponse({'success': False, 'error': 'Tous les champs sont requis'})
        
        # Chercher s'il existe déjà un message pour cet audience
        info_message, created = InfoMessage.objects.get_or_create(
            audience=audience,
            defaults={'title': title, 'content': content, 'is_active': True}
        )
        
        if not created:
            info_message.title = title
            info_message.content = content
            info_message.is_active = True
            info_message.save()
        
        return JsonResponse({'success': True, 'message': 'Informations enregistrées avec succès!'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
@login_required
def delete_info_message(request):
    """Supprimer un message d'information"""
    if not request.user.is_administrator():
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        audience = data.get('audience')
        
        # Supprimer le message pour cet audience
        InfoMessage.objects.filter(audience=audience).delete()
        
        return JsonResponse({'success': True, 'message': 'Informations supprimées avec succès!'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ VUES DE GRAPHIQUES ============

@login_required
@permission_required('accounts.can_view_student_performance_data', raise_exception=True)
def student_performance_data(request):
    """Données pour le graphique personnel de l'élève (ses résultats par module)"""
    print(f"DEBUG: student_performance_data appelée par {request.user}")
    
    if not request.user.is_authenticated or not request.user.is_student():
        print("DEBUG: Accès non autorisé - utilisateur non étudiant")
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    results = Result.objects.filter(student=request.user).select_related('module')
    print(f"DEBUG: {results.count()} résultats trouvés pour {request.user}")
    
    data = {
        'labels': [result.module.name for result in results],
        'datasets': [{
            'label': f'Résultats de {request.user.first_name}',
            'data': [float(result.score) for result in results],
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1
        }]
    }
    
    print(f"DEBUG: Données retournées: {data}")
    return JsonResponse(data)



@login_required
@permission_required('accounts.can_view_teacher_module_performance_data', raise_exception=True)
def teacher_module_performance_data(request):
    """Données pour le graphique de l'enseignant (performances des élèves dans son module)"""
    print(f"DEBUG: teacher_module_performance_data appelée par {request.user}")
    
    if not request.user.is_authenticated or not request.user.is_teacher():
        print("DEBUG: Accès non autorisé - utilisateur non enseignant")
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    # Récupérer les modules enseignés par ce professeur
    teacher_modules = Module.objects.filter(teacher=request.user)
    print(f"DEBUG: {teacher_modules.count()} modules trouvés pour l'enseignant {request.user}")
    
    data = {
        'labels': [],
        'datasets': [{
            'label': 'Moyenne des élèves',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }]
    }
    
    for module in teacher_modules:
        # Calculer la moyenne des résultats pour ce module
        avg_score = Result.objects.filter(module=module).aggregate(Avg('score'))['score__avg'] or 0
        print(f"DEBUG: Module {module.name} - moyenne: {avg_score}")
        
        data['labels'].append(module.name)
        data['datasets'][0]['data'].append(float(avg_score))
    
    print(f"DEBUG: Données retournées pour l'enseignant: {data}")
    return JsonResponse(data)


@login_required
@permission_required('accounts.can_view_all_students_performance_data', raise_exception=True)
def all_students_performance_data(request):
    """Données pour le graphique global (performances de tous les élèves par module)"""
    print(f"DEBUG: all_students_performance_data appelée par {request.user}")
    
    if not request.user.is_authenticated or not (request.user.is_administrator() or request.user.is_teacher()):
        print("DEBUG: Accès non autorisé - utilisateur non administrateur/enseignant")
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    # Récupérer tous les modules avec la moyenne des résultats
    modules = Module.objects.all()
    print(f"DEBUG: {modules.count()} modules trouvés au total")
    
    data = {
        'labels': [],
        'datasets': [{
            'label': 'Moyenne des résultats par module',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.5)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1
        }]
    }
    
    for module in modules:
        avg_score = Result.objects.filter(module=module).aggregate(Avg('score'))['score__avg'] or 0
        print(f"DEBUG: Module {module.name} - moyenne globale: {avg_score}")
        
        data['labels'].append(module.name)
        data['datasets'][0]['data'].append(float(avg_score))
    
    print(f"DEBUG: Données globales retournées: {data}")
    return JsonResponse(data)

# ============ VUES DE MODIFICATIONS ============
@login_required
@user_passes_test(lambda u: u.profil == 'admin')
def update_student_info(request):
    """Vue pour mettre à jour les informations destinées aux étudiants"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            info_message, created = InfoMessage.objects.update_or_create(
                audience='student',
                defaults={
                    'title': title,
                    'content': content
                }
            )
            
            django_messages.success(request, "Informations pour les étudiants mises à jour avec succès!")
        else:
            django_messages.error(request, "Veuillez remplir tous les champs.")
        
        return redirect('dashboard:dashboard')
    
    django_messages.error(request, "Méthode non autorisée.")
    return redirect('dashboard:dashboard')

@login_required
@user_passes_test(lambda u: u.profil == 'admin')
def update_teacher_info(request):
    """Vue pour mettre à jour les informations destinées aux enseignants"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            info_message, created = InfoMessage.objects.update_or_create(
                audience='teacher',
                defaults={
                    'title': title,
                    'content': content
                }
            )
            
            django_messages.success(request, "Informations pour les enseignants mises à jour avec succès!")
        else:
            django_messages.error(request, "Veuillez remplir tous les champs.")
        
        return redirect('dashboard:dashboard')
    
    django_messages.error(request, "Méthode non autorisée.")
    return redirect('dashboard:dashboard')


@login_required
@user_passes_test(lambda u: u.profil == 'admin')
def get_students_by_class(request):
    """Vue API pour récupérer les étudiants d'une classe (AJAX)"""
    class_id = request.GET.get('class_id')
    
    if class_id:
        students = Student.objects.values('id', 'first_name', 'last_name')
        students_list = list(students)
        
        # Formater les noms complets
        for student in students_list:
            student['full_name'] = f"{student['first_name']} {student['last_name']}"
        
        return JsonResponse({'students': students_list})
    
    return JsonResponse({'error': 'Class ID not provided'}, status=400)



# ============ VUES DES SUGGESTIONS ============
@login_required
def suggestions_list(request):
    """Vue pour afficher la liste des suggestions"""
    suggestions = ContactMessage.objects.all().order_by('-created_at')
    
    # Options de filtrage
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'read':
        suggestions = suggestions.filter(is_read=True)
    elif status_filter == 'unread':
        suggestions = suggestions.filter(is_read=False)
    
    context = {
        'suggestions': suggestions,
        'status_filter': status_filter,
        'title': 'Suggestions des utilisateurs'
    }
    return render(request, 'suggestions/suggestions.html', context)

@login_required
def mark_suggestion_read(request, suggestion_id):
    """Marquer une suggestion comme lue"""
    # Correction: Utiliser ContactMessage au lieu de Suggestion
    suggestion = get_object_or_404(ContactMessage, id=suggestion_id)
    suggestion.is_read = True
    suggestion.save()
    
    django_messages.success(request, "Suggestion marquée comme lue")
    return redirect('dashboard:suggestions_list')

@login_required
@user_passes_test(lambda u: u.profil == 'admin')
def delete_suggestion(request, suggestion_id):
    """Supprimer une suggestion"""
    # Correction: Utiliser ContactMessage au lieu de Suggestion
    suggestion = get_object_or_404(ContactMessage, id=suggestion_id)
    suggestion.delete()
    
    django_messages.success(request, "Suggestion supprimée avec succès")
    return redirect('dashboard:suggestions_list')

@login_required
def get_suggestion_detail(request):
    """Récupérer les détails d'une suggestion (AJAX)"""
    suggestion_id = request.GET.get('suggestion_id')
    
    if suggestion_id:
        # Correction: Utiliser ContactMessage au lieu de Suggestion
        suggestion = get_object_or_404(ContactMessage, id=suggestion_id)
        data = {
            'id': suggestion.id,
            'name': suggestion.name,
            'email': suggestion.email,
            'message': suggestion.message,
            'created_at': suggestion.created_at.strftime("%d/%m/%Y %H:%M")
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Suggestion ID not provided'}, status=400)


# ============ VUES DU PLANNING ============
@login_required
@permission_required('accounts.view_timetable', raise_exception=True)
def timetable_view(request):
    # Déterminer la semaine actuelle
    week_param = request.GET.get('week')
    if week_param:
        try:
            year, week_num = map(int, week_param.split('-'))
            jan1 = datetime(year, 1, 1)
            while jan1.weekday() != 0:  
                jan1 += timedelta(days=1)
            current_week = jan1 + timedelta(weeks=week_num - 1)
        except (ValueError, IndexError):
            current_week = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    else:
        current_week = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    
    # Récupérer tous les emplois du temps de la semaine actuelle
    timetable_entries = Timetable.objects.filter(week_start=current_week)
    
    # Structurer les données pour le template
    morning_slots = ['8-10', '10-12']  
    afternoon_slots = ['14-16', '16-18']  
    
    time_slots = morning_slots + afternoon_slots  
    days = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI']
    
    # Créer une structure de données organisée par jour et créneau
    organized_entries = {}
    for day in days:
        organized_entries[day] = {}
        for time_slot in time_slots:
            organized_entries[day][time_slot] = None
    
    # Remplir avec les données existantes
    for entry in timetable_entries:
        if entry.day in organized_entries and entry.timeslot in organized_entries[entry.day]:
            organized_entries[entry.day][entry.timeslot] = entry
    
    # Vérifier les permissions
    can_edit = request.user.has_perm('planning.can_manage_timetable')
    can_publish = request.user.has_perm('planning.can_publish_timetable')
    
    context = {
        'user': request.user,
        'timetable_entries': organized_entries,
        'modules': Module.objects.all(),
        'teachers': User.objects.filter(profil='teacher'),
        'days': days,
        'time_slots': time_slots,
        'morning_slots': morning_slots,  
        'afternoon_slots': afternoon_slots,
        'current_week': current_week,
        'can_edit': can_edit,
        'can_publish': can_publish,
    }
    
    return render(request, 'planning/create_planning.html', context)


@require_http_methods(["GET"])
@login_required
def get_timetable_data(request):
    """Récupérer les données d'emploi du temps pour une semaine spécifique"""
    try:
        week_str = request.GET.get('week')
        
        if not week_str:
            return JsonResponse({'success': False, 'error': 'Paramètre week manquant'})
        
        year, week_num = map(int, week_str.split('-W'))
        
        # Calculer la date du lundi de cette semaine
        jan1 = datetime(year, 1, 1)
        week_start = jan1 + timedelta(days=(week_num - 1) * 7 - jan1.weekday())
        
        # Récupérer les entrées d'emploi du temps
        entries = Timetable.objects.filter(week_start=week_start)
        
        data = {}
        for entry in entries:
            day = entry.day
            time_slot = entry.timeslot
            
            if day not in data:
                data[day] = {}
            
            data[day][time_slot] = {
                'module_id': entry.module.id,
                'module_name': entry.module.name,
                'module_code': entry.module.code,
                'teacher_id': entry.teacher.id,
                'teacher_name': f"{entry.teacher.first_name} {entry.teacher.last_name}",
                'classroom': entry.classroom,
                'notes': entry.notes,
            }
        
        return JsonResponse({
            'success': True, 
            'data': data,
            'week_start': week_start.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
@csrf_exempt
@login_required
@permission_required('accounts.manage_timetable', raise_exception=True)
def save_timetable_data(request):
    """Sauvegarder les données d'emploi du temps"""
    try:
        data = json.loads(request.body)
        week_str = data.get('week')
        timetable_data = data.get('timetable_data', {})
        
        print(f"Données reçues: {data}")  # DEBUG
        
        if not week_str:
            return JsonResponse({'success': False, 'error': 'Paramètre week manquant'})
        
        # Extraire l'année et le numéro de semaine
        try:
            year = int(week_str.split('-W')[0])
            week_num = int(week_str.split('-W')[1])
        except (ValueError, IndexError):
            return JsonResponse({'success': False, 'error': 'Format de semaine invalide'})
        
        # Calculer la date du lundi de cette semaine
        jan1 = datetime(year, 1, 1)
        # Trouver le premier lundi de l'année
        while jan1.weekday() != 0:  # 0 = lundi
            jan1 += timedelta(days=1)
        
        week_start = jan1 + timedelta(weeks=week_num - 1)
        
        print(f"Week start calculée: {week_start}")  # DEBUG
        
        with transaction.atomic():  # MAINTENANT transaction EST DÉFINI
            # Supprimer les anciennes entrées pour cette semaine
            Timetable.objects.filter(week_start=week_start).delete()
            
            # Créer les nouvelles entrées
            for day, slots in timetable_data.items():
                for time_slot, entry_data in slots.items():
                    if (entry_data.get('module_id') and entry_data.get('teacher_id')):
                        
                        # Vérifier que le jour et le timeslot sont valides
                        if day not in [choice[0] for choice in Timetable.DAY_CHOICES]:
                            continue
                        if time_slot not in [choice[0] for choice in Timetable.TIMESLOT_CHOICES]:
                            continue
                        
                        Timetable.objects.create(
                            week_start=week_start,
                            day=day,
                            timeslot=time_slot,
                            module_id=entry_data['module_id'],
                            teacher_id=entry_data['teacher_id'],
                            classroom=entry_data.get('classroom', ''),
                            notes=entry_data.get('notes', '')
                        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Emploi du temps sauvegardé avec succès',
            'week_start': week_start.isoformat()
        })
    
    except Exception as e:
        print(f"Erreur: {str(e)}")  # DEBUG
        return JsonResponse({'success': False, 'error': str(e)})
    
@require_http_methods(["GET"])
@login_required
def get_available_resources(request):
    """Récupérer les ressources disponibles"""
    modules = list(Module.objects.values('id', 'name', 'code'))
    teachers = list(User.objects.filter(profil='teacher').values(
        'id', 'first_name', 'last_name', 'email'
    ))
    
    return JsonResponse({
        'success': True,
        'modules': modules,
        'teachers': teachers
    })
    

    