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
from accounts.models import User, Student, Teacher, Module, Result, Timetable, InfoMessage, ContactMessage, FAQ, SchoolInfo,TimetableEntry,Note
from django.db import models
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from chartjs.views.lines import BaseLineChartView
from django.db.models import Avg






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
        'stats': {'total_students': Student.objects.count()},
        'show_module_chart': True,  # ← Nouveau: Activer le graphique
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
    
    timetable = Timetable.objects.filter(week=week_str).order_by('day', 'timeslot')
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    schedule_dict = {day: {'8h-10h': None, '10h-12h': None, '14h-16h': None, '16h-18h': None} for day in days}
    
    for entry in timetable:
        time_slot = entry.get_timeslot_display()
        schedule_dict[entry.day][time_slot] = {
            'module': entry.module,
            'teacher': entry.teacher
        }
    
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

class ModuleAverageJSONView(BaseLineChartView):
    def get_labels(self):
        """Retourne les noms des modules pour l'axe X"""
        from modules.models import Module
        return list(Module.objects.values_list('name', flat=True))

    def get_providers(self):
        """Retourne le nom du dataset"""
        return ["Moyenne des notes"]

    def get_data(self):
        """Retourne les données des moyennes pour chaque module"""
        from modules.models import Module
        averages = []
        
        for module in Module.objects.all():
            # Calcul de la moyenne des notes pour ce module
            avg_note = Note.objects.filter(
                module=module
            ).aggregate(avg=Avg('value'))['avg'] or 0
            
            averages.append(round(avg_note, 2) if avg_note else 0)
        
        return [averages]


class ModuleChartView(TemplateView):
    template_name = 'graphe/module_chart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chart_title'] = "Moyennes des notes par module"
        return context


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
@login_required
def timetable_view(request):
    # Utiliser directement le champ 'profil' de l'utilisateur
    user_profile = request.user  # L'utilisateur a directement le champ 'profil'
    
    # Récupérer les modules et enseignants
    modules = Module.objects.all()
    teachers = Teacher.objects.all()
    
    # Déterminer la semaine actuelle
    today = datetime.now().date()
    current_week = today - timedelta(days=today.weekday())
    
    
    context = {
        'user_profile': user_profile,  # On envoie l'utilisateur directement
        'modules': modules,
        'teachers': teachers,
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        'week_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'current_week': current_week,
    }
    
    return render(request, 'planning/create_planning.html', context)

@login_required
def timetable_view(request):
    # Utiliser directement le champ 'profil' de l'utilisateur
    user_profile = request.user
    
    # Récupérer les modules et enseignants
    modules = Module.objects.all()
    teachers = Teacher.objects.all()
    
    # Déterminer la semaine actuelle
    today = datetime.now().date()
    current_week = today - timedelta(days=today.weekday())
    
    # Récupérer le nom de la classe (à adapter selon votre logique)
    class_name = "Classe Principale"  # Exemple
    
    context = {
        'user_profile': user_profile,
        'modules': modules,
        'teachers': teachers,
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        'week_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'current_week': current_week,
        'class_name': class_name,
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
        monday = jan1 + timedelta(days=(week_num - 1) * 7 - jan1.weekday())
        
        # Récupérer l'emploi du temps
        timetable = Timetable.objects.filter(week_start=monday).first()
        
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
                    'teacher_id': entry.teacher.id if entry.teacher else None,
                }
        
        return JsonResponse({'success': True, 'data': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
@csrf_exempt
@login_required
def save_timetable_data(request):
    """Sauvegarder les données d'emploi du temps"""
    try:
        # Vérifier que l'utilisateur est admin
        if not request.user.profil == 'admin':
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        data = json.loads(request.body)
        week_str = data.get('week')
        timetable_data = data.get('timetable_data', {})
        
        if not week_str:
            return JsonResponse({'success': False, 'error': 'Paramètre week manquant'})
        
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
            '8-10': ('08:00:00', '10:00:00'),
            '10-12': ('10:00:00', '12:00:00'),
            '14-16': ('14:00:00', '16:00:00'),
            '16-18': ('16:00:00', '18:00:00')
        }
        
        for day, slots in timetable_data.items():
            for slot, entry_data in slots.items():
                if entry_data.get('module') and entry_data.get('teacher'):
                    start_time, end_time = time_slots.get(slot, ('00:00:00', '00:00:00'))
                    
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

