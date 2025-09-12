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
from django.views.decorators.http import require_GET
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
    
    # Redirection basée sur le profil de l'utilisateur
    if request.user.profil == 'admin':
        return redirect('dashboard:admin_dashboard')
    elif request.user.profil == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    elif request.user.profil == 'student':
        return redirect('dashboard:student_dashboard')
    else:
        return render(request, 'accounts/login.html')
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profil') and user.profil == 'admin'

# ============ VUES DES TABLEAUX DE BOARD ============
@login_required
def admin_dashboard(request):
    """Tableau de bord pour les administrateurs"""
    if not hasattr(request.user, 'profil') or request.user.profil != 'admin':
        django_messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('accounts:login')
    
    # Récupérer les données pour le dashboard
    context = {
        'title': 'Tableau de bord Administrateur',
        'user': request.user,
        'student_count': User.objects.filter(profil='student').count(),
        'teacher_count': User.objects.filter(profil='teacher').count(),
        'new_contacts_count': ContactMessage.objects.count(),
        'modules': Module.objects.all(),
        'teachers': Teacher.objects.all(),
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        'week_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'student_info': InfoMessage.objects.filter(audience='student').first(),
        'teacher_info': InfoMessage.objects.filter(audience='teacher').first(),
        'show_module_chart': True,  # ← Nouveau: Activer le graphique
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Tableau de bord pour les enseignants"""
    if not request.user.is_teacher():
        django_messages.error(request, "Accès réservé aux enseignants.")
        return redirect('accounts:login')
    
    teacher_info = InfoMessage.objects.filter(audience='teacher').first()
    
    context = {
        'title': 'Tableau de bord Enseignant',
        'user': request.user,
        'teacher_info': teacher_info,
        'student_count': User.objects.filter(profil='student').count(),
        'teacher_count': User.objects.filter(profil='teacher').count(),
        'module_count': Module.objects.count(),  
        'teacher_modules_count': teacher_modules_count, 
        'stats': {'total_students': Student.objects.count(),'total_modules': available_modules_count,},
        'show_module_chart': True,  
    }
    
    return render(request, 'dashboard/teacher_dashboard.html', context)

@login_required
def student_dashboard(request):
    """Tableau de bord pour les élèves"""
    if not request.user.is_student():
        django_messages.error(request, "Accès réservé aux étudiants.")
        return redirect('accounts:login')
    
    student_user = request.user
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_str = week_start.strftime("%Y-%m-%d")
    
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    schedule_dict = {day: {'8h-10h': None, '10h-12h': None, '14h-16h': None, '16h-18h': None} for day in days}
    
    
    student_info = InfoMessage.objects.filter(audience='student').first()
    
    context = {
        'title': 'Tableau de bord Élève',
        'user': request.user,
        'student_user': student_user,  
        'student_info': student_info,
        'schedule': schedule_dict,
        'days': days,
        'student_count': User.objects.filter(profil='student').count(),
        'teacher_count': User.objects.filter(profil='teacher').count(),
        'show_module_chart': True,  # ← Nouveau: Activer le graphique
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


# ============ VUES DE Graphe ============

@require_GET
def module_chart_data(request):
    """
    Vue qui retourne les données pour le graphique des moyennes par module
    """
    try:
        # Récupérer les moyennes par module
        # Adaptez cette requête selon votre structure de données
        modules_data = Note.objects.values('module__nom').annotate(
            moyenne=Avg('valeur')
        ).order_by('module__nom')
        
        # Préparer les données pour le graphique
        labels = [item['module'] for item in modules]
        datasets = [round(float(item['moyenne'] or 0), 2) for item in modules_data]
        
        data = {
            'labels': labels,
            'datasets': [datasets],
            'providers': ['Moyennes générales']  # Vous pouvez avoir plusieurs providers
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        # En cas d'erreur, retourner des données d'exemple
        labels = ['Mathématiques', 'Physique', 'Informatique', 'Anglais', 'Histoire']
        datasets = [14.5, 12.8, 15.2, 13.7, 11.9]
        
        data = {
            'labels': labels,
            'datasets': [datasets],
            'providers': ['Moyennes générales'],
            'error': str(e)
        }
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
        
        return redirect('dashboard:admin_dashboard')
    
    django_messages.error(request, "Méthode non autorisée.")
    return redirect('dashboard:admin_dashboard')

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
        
        return redirect('dashboard:admin_dashboard')
    
    django_messages.error(request, "Méthode non autorisée.")
    return redirect('dashboard:admin_dashboard')


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
def timetable_view(request):
    # Déterminer la semaine actuelle
    week_param = request.GET.get('week')
    if week_param:
        try:
            year, week_num = map(int, week_param.split('-'))
            jan1 = datetime(year, 1, 1)
            # Trouver le premier lundi de l'année
            while jan1.weekday() != 0:  # 0 = lundi
                jan1 += timedelta(days=1)
            current_week = jan1 + timedelta(weeks=week_num - 1)
        except (ValueError, IndexError):
            current_week = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    else:
        current_week = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    
    # Récupérer tous les emplois du temps de la semaine actuelle
    timetable_entries = Timetable.objects.filter(week_start=current_week)
    
    # Structurer les données pour le template
    morning_slots = ['8-10', '10-12']  # Créneaux du matin
    afternoon_slots = ['14-16', '16-18']  # Créneaux de l'après-midi
    
    time_slots = morning_slots + afternoon_slots  
    days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    
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
        'time_slots': time_slots,  # Tous les créneaux
        'morning_slots': morning_slots,  # Créneaux du matin seulement
        'afternoon_slots': afternoon_slots,  # Créneaux de l'après-midi seulement
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
@permission_required('planning.can_manage_timetable', raise_exception=True)
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