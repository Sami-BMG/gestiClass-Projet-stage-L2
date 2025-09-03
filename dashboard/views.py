from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages as django_messages
from datetime import datetime,timedelta
import calendar
from accounts.models import User, Student, Teacher, Module, Result, Timetable, InfoMessage, ContactMessage, FAQ, SchoolInfo,TimetableEntry
from django.db import models
from django.contrib.auth.models import User







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

# Les views de l'admin dashboard
@login_required
def admin_dashboard(request):
    """Tableau de bord pour les administrateurs"""
    print(request.user.profil, "admin_dashboard")
    if not hasattr(request.user, 'profil') or request.user.profil != 'admin':
        django_messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('accounts:login')
    
    # Récupérer les données pour le dashboard
    context = {
        'title': 'Tableau de bord Administrateur',
        'user': request.user,
        'student_count' : User.objects.filter(profil='student').count(),
        'teacher_count' : User.objects.filter(profil='teacher').count(),
        'new_contacts_count': ContactMessage.objects.count(),
        'modules': Module.objects.all(),
        'teachers': Teacher.objects.all(),
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        'week_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'student_info': InfoMessage.objects.filter(audience='student').first(),
        'teacher_info': InfoMessage.objects.filter(audience='teacher').first(),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

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

@login_required
@user_passes_test(lambda u: u.profil == 'admin')
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
@user_passes_test(lambda u: u.profil == 'admin')
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
@user_passes_test(lambda u: u.profil == 'admin')
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


@login_required
def teacher_dashboard(request):
    """Tableau de bord pour les enseignants"""
    print(request.user.profil, "teacher_dashboard")
    if not hasattr(request.user, 'profil') or request.user.profil != 'teacher':
        django_messages.error(request, "Accès réservé aux enseignants.")
        return redirect('accounts:login')
    
    # Récupérer les informations de l'enseignant connecté
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        django_messages.error(request, "Profil enseignant non trouvé.")
        return redirect('accounts:login')
    
    # Récupérer les modules enseignés par cet enseignant
    modules_taught = Module.objects.filter(teacher=teacher)
    
    # Récupérer les classes où cet enseignant donne cours
    classes_taught = Class.objects.filter(module__teacher=teacher).distinct()
    
    # Récupérer les informations pour les enseignants
    teacher_info = InfoMessage.objects.filter(audience='teacher').first()
    
    context = {
        'title': 'Tableau de bord Enseignant',
        'user': request.user,
        'teacher': teacher,
        'teacher_info': teacher_info,
        'modules_taught': modules_taught,
        'classes_taught': classes_taught,
        'stats': {
            'total_modules': modules_taught.count(),
            'total_classes': classes_taught.count(),
            'total_students': Student.objects.count(),
        }
    }
    
    return render(request, 'dashboard/teacher_dashboard.html', context)

@login_required
def student_dashboard(request):
    """Tableau de bord pour les élèves"""
    print(request.user.profil, "student_dashboard")
    if not hasattr(request.user, 'profil') or request.user.profil != 'student':
        django_messages.error(request, "Accès réservé aux étudiants.")
        return redirect('accounts:login')
    
    # Récupérer les informations de l'étudiant connecté
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        django_messages.error(request, "Profil étudiant non trouvé.")
        return redirect('accounts:login')
    

    
    # Récupérer l'emploi du temps de la classe
    today = datetime.now()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_str = week_start.strftime("%Y-%m-%d")
    
    timetable = Timetable.objects.filter(
        week=week_str
    ).order_by('day', 'timeslot')
    
    # Organiser l'emploi du temps par jour
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    schedule_dict = {day: {'8h-10h': None, '10h-12h': None, '14h-16h': None, '16h-18h': None} for day in days}
    
    for entry in timetable:
        time_slot = entry.get_timeslot_display()
        schedule_dict[entry.day][time_slot] = {
            'module': entry.module,
            'teacher': entry.teacher
        }
    
    # Récupérer les informations pour les étudiants
    student_info = InfoMessage.objects.filter(audience='student').first()
    

    
    context = {
        'title': 'Tableau de bord Élève',
        'user': request.user,
        'student': student,
        'student_info': student_info,
        'schedule': schedule_dict,
        'days': days,
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)

def is_admin(user):
    return user.profil == 'admin'

#les views de planning
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profil') and user.profil == 'admin'

@login_required
def timetable_view(request):
    
    # Vérifier les permissions
    user_profile = request.user.profil == 'admin'
    
    # Récupérer les modules et enseignants
    modules = Module.objects.all()
    teachers = Teacher.objects.all()
    
    # Déterminer la semaine actuelle
    today = datetime.now().date()
    current_week = today - timedelta(days=today.weekday())
    
    context = {
        'user_profil': user_profile,
        'modules': modules,
        'teachers': teachers,
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        'week_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'current_week': current_week,
    }
    
    return render(request, 'planning/create_planning.html', context)


@require_http_methods(["GET"])
@login_required
def get_timetable_data(request):
    """Récupérer les données d'emploi du temps pour une classe et une semaine spécifique"""
    try:
        week_str = request.GET.get('week')
        year, week_num = map(int, week_str.split('-W'))
        
        # Calculer la date du lundi de cette semaine
        jan1 = datetime(year, 1, 1)
        monday = jan1 + timedelta(days=(week_num - 1) * 7 - jan1.weekday())
        
        # Récupérer l'emploi du temps
        timetable = Timetable.objects.filter(
            week_start=monday
        ).first()
        
        data = {}
        if timetable:
            entries = TimetableEntry.objects.filter(timetable=timetable)
            for entry in entries:
                day = entry.day.lower()
                slot = f"{entry.start_time.strftime('%H')}-{entry.end_time.strftime('%H')}"
                
                if day not in data:
                    data[day] = {}
                
                data[day][slot] = {
                    'module_id': entry.module.id if entry.module else None,
                    'module_name': entry.module.name if entry.module else '',
                    'teacher_id': entry.teacher.id if entry.teacher else None,
                    'teacher_name': f"{entry.teacher.first_name} {entry.teacher.last_name}" if entry.teacher else ''
                }
        
        return JsonResponse({'success': True, 'data': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def save_timetable_data(request):
    """Sauvegarder les données d'emploi du temps (admin seulement)"""
    try:
        data = json.loads(request.body)
        week_str = data.get('week')
        timetable_data = data.get('timetable_data', {})
        
        year, week_num = map(int, week_str.split('-W'))
        jan1 = datetime(year, 1, 1)
        week_start = jan1 + timedelta(days=(week_num - 1) * 7 - jan1.weekday())
        
        # Créer ou mettre à jour l'emploi du temps
        timetable, created = Timetable.objects.get_or_create(
            week_start=week_start,
            defaults={'created_by': request.user}
        )
        
        if not created:
            timetable.updated_by = request.user
            timetable.save()
        
        # Supprimer les anciennes entrées
        TimetableEntry.objects.filter(timetable=timetable).delete()
        
        # Créer les nouvelles entrées
        time_slots = {
            '8-10': ('08:00', '10:00'),
            '10-12': ('10:00', '12:00'),
            '14-16': ('14:00', '16:00'),
            '16-18': ('16:00', '18:00')
        }
        
        for day, slots in timetable_data.items():
            for slot, entry_data in slots.items():
                if entry_data.get('module') and entry_data.get('teacher'):
                    start_time, end_time = time_slots.get(slot, ('00:00', '00:00'))
                    
                    TimetableEntry.objects.create(
                        timetable=timetable,
                        day=day.upper(),
                        start_time=start_time,
                        end_time=end_time,
                        module_id=entry_data['module'],
                        teacher_id=entry_data['teacher']
                    )
        
        return JsonResponse({'success': True, 'message': 'Emploi du temps sauvegardé avec succès'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
@csrf_exempt
@login_required
@user_passes_test(is_admin)
def clear_timetable(request):
    """Effacer l'emploi du temps pour une semaine (admin seulement)"""
    try:
        week_str = request.POST.get('week')
        year, week_num = map(int, week_str.split('-W'))
        jan1 = datetime(year, 1, 1)
        week_start = jan1 + timedelta(days=(week_num - 1) * 7 - jan1.weekday())
        
        timetable = Timetable.objects.filter(
            classe_id=class_id,
            week_start=week_start
        ).first()
        
        if timetable:
            timetable.delete()
            return JsonResponse({'success': True, 'message': 'Emploi du temps effacé'})
        else:
            return JsonResponse({'success': False, 'error': 'Aucun emploi du temps trouvé'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



