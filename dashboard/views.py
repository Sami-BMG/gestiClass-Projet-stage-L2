from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
import calendar

User = get_user_model()

@login_required
def home(request):
    print(request.user.profil, "home")
    """Vue principale qui redirige vers le tableau de bord approprié"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Redirection basée sur le profil de l'utilisateur
    if request.user.profil == 'admin':
        return redirect('dashboard:admin_dashboard')  # Redirection vers la création d'utilisateurs
    elif request.user.profil == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    elif request.user.profil == 'student':
        return redirect('dashboard:student_dashboard')
    else:
        return render(request, 'accounts/login.html')
    
@login_required
def admin_dashboard(request):
    """Tableau de bord pour les administrateurs"""
    print(request.user.profil, "admin_dashboard")
    if not hasattr(request.user, 'profil') or request.user.profil != 'admin':
        from django.contrib import messages
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('accounts:login')
    
    context = {
        'title': 'Tableau de bord Administrateur',
        'user': request.user,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Tableau de bord pour les enseignants"""
    print(request.user.profil, "teacher_dashboard")
    if not hasattr(request.user, 'profil') or request.user.profil != 'teacher':
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('accounts:login')
    
    # Données factices pour le moment - à remplacer par vos modèles réels
    context = {
        'title': 'Tableau de bord Enseignant',
        'user': request.user,
        'teacher': request.user,  # Utilisateur actuel comme "teacher"
        'stats': {
            'total_modules': 5,  # Données factices
            'total_students': 42,
            'recent_results': 15,
        },
        'modules': [
            {'code': 'MATH101', 'name': 'Mathématiques', 'coefficient': 3},
            {'code': 'PHYS202', 'name': 'Physique', 'coefficient': 2},
            {'code': 'INFO303', 'name': 'Informatique', 'coefficient': 4},
        ],
        'results': [
            {
                'student': {'user': {'get_full_name': 'Jean Dupont'}},
                'module': {'name': 'Mathématiques'},
                'score': 16.5,
                'exam_date': '2024-01-15'
            },
            {
                'student': {'user': {'get_full_name': 'Marie Martin'}},
                'module': {'name': 'Physique'},
                'score': 12.0,
                'exam_date': '2024-01-10'
            },
        ]
    }
    
    return render(request, 'dashboard/teacher_dashboard.html', context)


@login_required
def student_dashboard(request):
    """Tableau de bord pour les élèves"""
    print(request.user.profil, "student_dashboard")
    if not hasattr(request.user, 'profil') or request.user.profil != 'student':
         return redirect('accounts:login')
    context = {
        'title': 'Tableau de bord Élève',
        'user': request.user,
    }
    return render(request, 'dashboard/student_dashboard.html', context)




def is_admin(user):
    return user.profil == 'admin'

'''@login_required
def schedule_view(request):
    user = request.user
    today = datetime.today()
    current_week = today.isocalendar()[1]
    
    # Déterminer la classe de l'utilisateur
    if user.profil == 'student':
        user_class = Class.objects.filter(students=user).first()
        schedules = Schedule.objects.filter(class_group=user_class) if user_class else Schedule.objects.none()
    elif user.profil == 'teacher':
        schedules = Schedule.objects.filter(subject__teacher=user)
    else:  # admin
        schedules = Schedule.objects.all()
    
    # Organiser par jour
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    time_slots = ['8-12',  '14-18']
    
    schedule_dict = {}
    for day in days:
        schedule_dict[day] = {}
        for slot in time_slots:
            schedule_dict[day][slot] = schedules.filter(day=day, time_slot=slot)
    
    # Récupérer les informations du délégué si l'utilisateur est étudiant
    delegate = None
    if user.profil == 'student' and user_class:
        delegate = user_class.delegate
    
    context = {
        'schedule': schedule_dict,
        'days': days,
        'time_slots': time_slots,
        'current_week': current_week,
        'delegate': delegate,
        'user_class': user_class if user.profil == 'student' else None,
    }
    
    return render(request, 'schedule/schedule.html', context)

'''



