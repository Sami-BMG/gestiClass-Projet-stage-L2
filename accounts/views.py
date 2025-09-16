from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test,permission_required
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
import csv
from io import StringIO
import secrets
import string
from .forms import CustomUserCreationForm,AssignRoleForm,RoleForm
from .models import Result, Module, User, ContactMessage, FAQ, SchoolInfo,Teacher ,Student
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, Group, Permission 
from django import forms



User = get_user_model()

# ============ FONCTIONS UTILITAIRES ============
def send_login_email(user, password):
    """Envoie un email avec les informations de connexion à un nouvel utilisateur"""
    subject = 'Vos informations de connexion - Plateforme Éducative'
    
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'password': password,
        'login_url': 'http://127.0.0.1:8000/login'
    }
    
    html_message = render_to_string('email/welcome_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def is_admin(user):
    """Vérifie si l'utilisateur est administrateur"""
    return user.is_authenticated and user.profil == 'admin'


# ============ VUES D'AUTHENTIFICATION ============
def index(request):
    """Vue d'accueil redirigeant vers le dashboard approprié"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return redirect('accounts:login')


@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def create_user(request):
    """Vue pour créer un nouvel utilisateur (accessible seulement aux admins)"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"L'utilisateur {user.username} a été créé avec succès!")
            return redirect('accounts:create_user')
        else:
            messages.error(request, "Erreur lors de la création. Veuillez corriger les erreurs.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/create_user.html', {'form': form})


def user_login(request):
    """Vue de connexion utilisateur"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user:
                login(request, user)
                if hasattr(user, 'profil'):
                    print(user.profil, "login")
                    if user.profil == 'admin':
                        return redirect('dashboard:admin_dashboard')
                    elif user.profil == 'teacher':
                        return redirect('dashboard:teacher_dashboard')
                    elif user.profil == 'student':
                        return redirect('dashboard:student_dashboard')
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Identifiants invalides.')
        else:
            messages.error(request, 'Veuillez vérifier vos identifiants.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    return redirect('accounts:login')


@login_required
def change_password(request):
    """Vue pour changer le mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe mis à jour avec succès!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})


# ============ VUES DE RÉINITIALISATION DE MOT DE PASSE ============
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, _("Un email avec les instructions de réinitialisation a été envoyé."))
        return response


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Votre mot de passe a été réinitialisé avec succès."))
        return response


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
    
    def get(self, request, *args, **kwargs):
        messages.success(request, _("Votre mot de passe a été modifié avec succès. Vous pouvez maintenant vous connecter."))
        return super().get(request, *args, **kwargs)



# ============ VUES POUR LES ROLES ============


class RoleForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom du rôle (ex: Délégué, Enseignant, etc.)'
        })
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '10'
        })
    )

@login_required
@permission_required('accounts.assign_role', raise_exception=True)
def role_list(request):
    """Affiche la liste de tous les rôles existants avec possibilité de création"""
    groups = Group.objects.all().prefetch_related('permissions')
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role_name = form.cleaned_data['name']
            permissions = form.cleaned_data['permissions']
            
            # Créer le nouveau rôle
            new_role, created = Group.objects.get_or_create(name=role_name)
            
            # Ajouter les permissions sélectionnées
            if permissions:
                new_role.permissions.set(permissions)
            
            if created:
                messages.success(request, f'Rôle "{role_name}" créé avec succès!')
            else:
                messages.warning(request, f'Rôle "{role_name}" existe déjà et a été mis à jour!')
            
            return redirect('accounts:role_list')
    else:
        form = RoleForm()
    
    # Récupérer toutes les permissions par catégorie
    permissions_by_category = {}
    for perm in Permission.objects.all():
        app_label = perm.content_type.app_label
        if app_label not in permissions_by_category:
            permissions_by_category[app_label] = []
        permissions_by_category[app_label].append(perm)
    
    context = {
        'groups': groups,
        'form': form,
        'permissions_by_category': permissions_by_category,
        'groups': groups,
        'total_permissions': Permission.objects.count(),
        'total_users': User.objects.filter(groups__isnull=False).count(),
        'title': 'Gestion des Rôles et Permissions'
    }
    return render(request, 'roles/role_list.html', context)

@login_required
@permission_required('auth.change_group', raise_exception=True)
def edit_role(request, role_id):
    """Modifier un rôle existant"""
    role = get_object_or_404(Group, id=role_id)
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role_name = form.cleaned_data['name']
            permissions = form.cleaned_data['permissions']
            
            # Mettre à jour le nom du rôle
            if role.name != role_name:
                role.name = role_name
                role.save()
            
            # Mettre à jour les permissions
            role.permissions.set(permissions)
            
            messages.success(request, f'Rôle "{role_name}" modifié avec succès!')
            return redirect('accounts:role_list')
    else:
        # Pré-remplir le formulaire avec les données actuelles
        form = RoleForm(initial={
            'name': role.name,
            'permissions': role.permissions.all()
        })
    
    permissions_by_category = {}
    for perm in Permission.objects.all():
        app_label = perm.content_type.app_label
        if app_label not in permissions_by_category:
            permissions_by_category[app_label] = []
        permissions_by_category[app_label].append(perm)
    
    context = {
        'form': form,
        'role': role,
        'permissions_by_category': permissions_by_category,
        'title': f'Modifier le rôle {role.name}'
    }
    return render(request, 'roles/edit_role.html', context)


@login_required
@permission_required('auth.delete_group', raise_exception=True)
def delete_role(request, role_id):
    """Supprimer un rôle"""
    role = get_object_or_404(Group, id=role_id)
    
    if request.method == 'POST':
        role_name = role.name
        role.delete()
        messages.success(request, f'Rôle "{role_name}" supprimé avec succès!')
        return redirect('accounts:role_list')
    
    context = {
        'role': role,
        'title': f'Supprimer le rôle {role.name}'
    }
    return render(request, 'roles/delete_role.html', context)

@login_required
@permission_required('accounts.assign_role', raise_exception=True)
def assign_user_role(request, user_id, user_type):
    """Attribuer un rôle à un utilisateur spécifique (étudiant ou enseignant)"""
    
    # Validation du type d'utilisateur
    if user_type not in ['student', 'teacher']:
        messages.error(request, 'Type d\'utilisateur non valide.')
        return redirect('dashboard:home')
    
    # Récupération de l'utilisateur avec vérification du profil
    user = get_object_or_404(User, id=user_id, profil=user_type)
    
    if request.method == 'POST':
        role_id = request.POST.get('role')
        if role_id:
            role = get_object_or_404(Group, id=role_id)
            user.groups.clear()
            user.groups.add(role)
            messages.success(request, f'Rôle "{role.name}" attribué à {user.username} avec succès!')
        else:
            # Option pour retirer le rôle si aucun n'est sélectionné
            user.groups.clear()
            messages.success(request, f'Tous les rôles ont été retirés de {user.username}!')
        
        return redirect('accounts:assign_user_role', user_id=user_id, user_type=user_type)
    
    available_roles = Group.objects.all()
    
    context = {
        'elem': user,  # Variable commune pour les deux types
        'user_type': user_type,
        'available_roles': available_roles,
        'title': f'Attribuer un rôle à {user.username}'
    }
    
    # Utiliser le template unique
    return render(request, 'roles/assign_user_role.html', context)


@login_required
def remove_user_role(request, user_id):
    """Retirer un rôle spécifique d'un utilisateur (étudiant ou enseignant)"""
    user = get_object_or_404(User, id=user_id)
    
    # Vérifier que l'utilisateur est bien un étudiant ou enseignant
    if user.profil not in ['student', 'teacher']:
        messages.error(request, 'Utilisateur non autorisé.')
        return redirect('dashboard:home')
        
        
    user_type = user.profil 
    
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        if role_id:
            try:
                role = Group.objects.get(id=role_id)
                user.groups.clear()
                messages.success(request, f'Rôle "{role.name}" retiré de {user.username} avec succès!')
            except Group.DoesNotExist:
                messages.error(request, 'Rôle non trouvé.')
        else:
            messages.error(request, 'Aucun rôle spécifié pour le retrait.')   
        return redirect('accounts:assign_user_role', user_type=user_type, user_id=user_id)




# ============ VUES POUR LA GESTION DES ÉLÈVES ============
@login_required
@permission_required('accounts.can_view_student_list', raise_exception=True)
def list_students(request):
    """Vue pour lister les élèves - Accessible à tous les utilisateurs connectés"""
    User = get_user_model()
    students = User.objects.filter(profil='student')
    is_admin_user = hasattr(request.user, 'profil') and request.user.profil == 'admin'
    
    return render(request, 'students/list.html', {
        'students': students,
        'is_admin': is_admin_user
    })


@login_required
@permission_required('accounts.can_add_student', raise_exception=True)
def create_student(request):
    """Vue pour créer un nouvel élève"""
    if request.method == 'POST':
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        count_students = User.objects.filter(profil='student').count()
        
        username = f"{request.POST['first_name'][0].lower()}{request.POST['last_name'].lower()}{count_students + 1}"
        
        # Créer l'utilisateur
        user = User.objects.create(
            username=username,
            email=request.POST['email'],
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            birth_date=request.POST['birth_date'],
            phone=request.POST.get('phone', ''),
            profil='student'
        )
        
        # Gérer l'upload de la photo
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']
            user.save()
        
        # Envoyer l'email avec les informations de connexion
        send_login_email(user, password)
        
        return redirect('accounts:students_list')
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
@permission_required('accounts.can_change_student', raise_exception=True)
def update_student(request, student_id):
    """Vue pour modifier les informations d'un élève"""
    student = get_object_or_404(User, id=student_id)
    
    if request.method == 'POST':
        try:
            # Validation des données
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"Le champ {field} est obligatoire.")
                    return redirect('accounts:students_list')
            
            # Vérifier si l'email est déjà utilisé
            email = request.POST['email']
            if User.objects.filter(email=email).exclude(id=student_id).exists():
                messages.error(request, "Cet email est déjà utilisé par un autre utilisateur.")
                return redirect('accounts:students_list')
            
            # Mise à jour des informations
            student.first_name = request.POST['first_name']
            student.last_name = request.POST['last_name']
            student.email = email
            student.phone = request.POST.get('phone', '')
            student.address = request.POST.get('address', '')
            
            # Date de naissance
            birth_date = request.POST.get('birth_date')
            if birth_date:
                student.birth_date = birth_date
            
            # Gestion de la photo
            if 'remove_photo' in request.POST and request.POST['remove_photo'] == 'on':
                if student.photo:
                    student.photo.delete(save=False)
                    student.photo = None
            
            if 'photo' in request.FILES:
                if student.photo:
                    student.photo.delete(save=False)
                student.photo = request.FILES['photo']
            
            student.save()
            
            messages.success(request, f"✅ L'élève {student.get_full_name()} a été modifié avec succès.")
            return redirect('accounts:students_list')
            
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la modification: {str(e)}")
            return redirect('accounts:students_list')
    
    # GET request - afficher le formulaire
    return render(request, 'students/update_student.html', {'student': student})


@login_required
@permission_required('accounts.can_view_student_details', raise_exception=True)
def student_detail(request, student_id):
    """Vue pour afficher les détails d'un élève"""
    student = get_object_or_404(User, id=student_id, profil='student')
    context = {
        'student': student,
        'title': f'Détails de {student.get_full_name()}'
    }
    return render(request, 'students/student_detail.html', context)


@login_required
@permission_required('accounts.can_delete_student', raise_exception=True)
def delete_student(request, student_id):
    """Vue pour supprimer un élève - Admin seulement"""
    if not request.user.is_superuser:
        raise PermissionDenied("Seuls les administrateurs peuvent supprimer les élèves.")
    
    if request.method == 'POST':
        try:
            student = get_object_or_404(User, id=student_id, profil='student')
            student_name = student.get_full_name()
            student.delete()
            messages.success(request, f"✅ L'élève {student_name} a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la suppression: {str(e)}")
    
    return redirect('accounts:students_list')


# ============ VUES POUR LA GESTION DES ENSEIGNANTS ============
@login_required
@permission_required('accounts.can_view_teacher_list', raise_exception=True)
def list_teachers(request):
    """Vue pour lister les enseignants - Accessible à tous les utilisateurs connectés"""
    teachers = User.objects.filter(profil='teacher')
    is_admin_user = hasattr(request.user, 'profil') and request.user.profil == 'admin'
    
    return render(request, 'teachers/list.html', {
        'teachers': teachers,
        'user_type': 'teacher',
        'is_admin': is_admin_user
    })


@login_required
@permission_required('accounts.can_add_teacher', raise_exception=True)
def create_teacher(request):
    """Vue pour créer un nouvel enseignant"""
    if request.method == 'POST':
        try:
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            count_teachers = User.objects.filter(profil='teacher').count()
            
            username = f"prof.{request.POST['first_name'][0].lower()}{request.POST['last_name'].lower()}{count_teachers + 1}"
            
            # Créer l'utilisateur
            user = User.objects.create(
                username=username,
                email=request.POST['email'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                birth_date=request.POST.get('birth_date', None),
                phone=request.POST.get('phone', ''),
                specialty=request.POST.get('speciality', ''),
                profil='teacher'
            )
            
            # Gérer l'upload de la photo
            if 'photo' in request.FILES:
                user.photo = request.FILES['photo']
            user.save()
            
            send_login_email(user, password)
            messages.success(request, f"Enseignant {user.get_full_name()} créé avec succès!")
            return redirect('accounts:teachers_list')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de l'enseignant: {str(e)}")
            return redirect('accounts:teachers_list')
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
@permission_required('accounts.can_change_teacher', raise_exception=True)
def update_teacher(request, teacher_id):
    """Vue pour modifier les informations d'un enseignant"""
    teacher = get_object_or_404(User, id=teacher_id, profil='teacher')
    
    if request.method == 'POST':
        try:
            # Validation des données
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"Le champ {field} est obligatoire.")
                    return redirect('accounts:teachers_list')
            
            # Vérifier si l'email est déjà utilisé
            email = request.POST['email']
            if User.objects.filter(email=email).exclude(id=teacher_id).exists():
                messages.error(request, "Cet email est déjà utilisé par un autre utilisateur.")
                return redirect('accounts:teachers_list')
            
            # Mise à jour des informations
            teacher.first_name = request.POST['first_name']
            teacher.last_name = request.POST['last_name']
            teacher.email = email
            teacher.phone = request.POST.get('phone', '')
            teacher.specialty = request.POST.get('speciality', '')
            
            # Date de naissance
            birth_date = request.POST.get('birth_date')
            if birth_date:
                teacher.birth_date = birth_date
            
            # Gestion de la photo
            if 'remove_photo' in request.POST and request.POST['remove_photo'] == 'on':
                if teacher.photo:
                    teacher.photo.delete(save=False)
                    teacher.photo = None
            
            if 'photo' in request.FILES:
                if teacher.photo:
                    teacher.photo.delete(save=False)
                teacher.photo = request.FILES['photo']
            
            teacher.save()
            
            messages.success(request, f"✅ L'enseignant {teacher.get_full_name()} a été modifié avec succès.")
            return redirect('accounts:teachers_list')
            
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la modification: {str(e)}")
            return redirect('accounts:teachers_list')
    
    # GET request - afficher le formulaire
    return render(request, 'teachers/update_teacher.html', {'teacher': teacher})


@login_required
@permission_required('accounts.can_view_teacher_details', raise_exception=True)
def teacher_detail(request, teacher_id):
    """Vue pour afficher les détails d'un enseignant"""
    teacher = get_object_or_404(User, id=teacher_id, profil='teacher')
    context = {
        'teacher': teacher,
        'title': f'Détails de {teacher.get_full_name()}'
    }
    return render(request, 'teachers/teacher_detail.html', context)


@login_required
def delete_teacher(request, teacher_id):
    """Vue pour supprimer un enseignant - Admin seulement"""
    if not request.user.is_superuser:
        raise PermissionDenied("Seuls les administrateurs peuvent supprimer les enseignants.")
    
    if request.method == 'POST':
        try:
            teacher = get_object_or_404(User, id=teacher_id, profil='teacher')
            teacher_name = teacher.get_full_name()
            teacher.delete()
            messages.success(request, f"✅ L'enseignant {teacher_name} a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la suppression: {str(e)}")
    
    return redirect('accounts:teachers_list')


# ============ VUES POUR LA GESTION DES MODULES ============
@login_required
@permission_required('accounts.can_view_module_list', raise_exception=True)
def modules_list(request):
    """Vue pour afficher la liste des modules"""
    modules = Module.objects.all().order_by('name')
    is_admin_user = request.user.is_superuser

    # Filtrer par semestre si spécifié
    semester = request.GET.get('semester')
    if semester:
        modules = modules.filter(semester=semester)
    
    # Filtrer par enseignant si spécifié
    teacher_id = request.GET.get('teacher')
    if teacher_id:
        modules = modules.filter(teacher_id=teacher_id)
    
    teachers = User.objects.filter(profil='teacher')
    
    # Définir les choix de semestre
    semesters = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ]
    
    context = {
        'modules': modules,
        'teachers': teachers,
        'semesters': semesters,
        'selected_semester': semester,
        'selected_teacher': teacher_id,
        'is_admin': is_admin_user,
        'title': 'Liste des modules'
    }
    return render(request, 'modules/list.html', context)


@login_required
@permission_required('accounts.can_add_module', raise_exception=True)
def create_module(request):
    """Vue pour créer un nouveau module"""
    if request.method == 'POST':
        try:
            # Validation des données
            required_fields = ['name', 'code']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"Le champ {field} est obligatoire.")
                    return redirect('accounts:modules_list')
            
            # Vérifier si le code est déjà utilisé
            code = request.POST['code']
            if Module.objects.filter(code=code).exists():
                messages.error(request, "Ce code de module est déjà utilisé.")
                return redirect('accounts:modules_list')
            
            # Créer le module
            module = Module.objects.create(
                name=request.POST['name'],
                code=code,
                coefficient=request.POST.get('coefficient', 1),
                credit=request.POST.get('credit', 1),
                description=request.POST.get('description', ''),
            )
            
            # Assigner le semestre si fourni
            semester = request.POST.get('semester')
            if semester:
                module.semester = semester
            
            # Assigner l'enseignant si fourni
            teacher_id = request.POST.get('teacher')
            if teacher_id:
                teacher = get_object_or_404(User, id=teacher_id, profil='teacher')
                module.teacher = teacher
            
            module.save()
            
            messages.success(request, f"Module {module.name} créé avec succès!")
            return redirect('accounts:modules_list')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du module: {str(e)}")
            return redirect('accounts:modules_list')
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
@permission_required('accounts.can_change_module', raise_exception=True)
def update_module(request, module_id):
    """Vue pour modifier un module"""
    module = get_object_or_404(Module, id=module_id)
    
    if request.method == 'POST':
        try:
            # Validation des données
            required_fields = ['name', 'code']
            for field in required_fields:
                if not request.POST.get(field):
                    messages.error(request, f"Le champ {field} est obligatoire.")
                    return redirect('accounts:modules_list')
            
            # Vérifier si le code est déjà utilisé par un autre module
            code = request.POST['code']
            if Module.objects.filter(code=code).exclude(id=module_id).exists():
                messages.error(request, "Ce code de module est déjà utilisé par un autre module.")
                return redirect('accounts:modules_list')
            
            # Mise à jour des informations
            module.name = request.POST['name']
            module.code = code
            module.coefficient = request.POST.get('coefficient', 1)
            module.credit = request.POST.get('credit', 1)
            module.description = request.POST.get('description', '')
            
            # Semestre
            semester = request.POST.get('semester')
            if semester:
                module.semester = semester
            else:
                module.semester = None
            
            # Enseignant
            teacher_id = request.POST.get('teacher')
            if teacher_id:
                teacher = get_object_or_404(User, id=teacher_id, profil='teacher')
                module.teacher = teacher
            else:
                module.teacher = None
            
            module.save()
            
            messages.success(request, f"✅ Le module {module.name} a été modifié avec succès.")
            return redirect('accounts:modules_list')
            
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la modification: {str(e)}")
            return redirect('accounts:modules_list')
    
    # GET request - afficher le formulaire
    teachers = User.objects.filter(profil='teacher')
    semesters = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ]
    
    return render(request, 'modules/update_module.html', {
        'module': module,
        'teachers': teachers,
        'semesters': semesters
    })


@login_required
@permission_required('accounts.can_view_module_details', raise_exception=True)
def module_detail(request, module_id):
    """Vue pour afficher les détails d'un module"""
    module = get_object_or_404(Module, id=module_id)
    context = {
        'module': module,
        'title': f'Détails du module {module.name}'
    }
    return render(request, 'modules/module_detail.html', context)


@login_required
@permission_required('accounts.can_delete_module', raise_exception=True)
def delete_module(request, module_id):
    """Vue pour supprimer un module - Admin seulement"""
    if not request.user.is_superuser:
        raise PermissionDenied("Seuls les administrateurs peuvent supprimer les modules.")
    
    if request.method == 'POST':
        try:
            module = get_object_or_404(Module, id=module_id)
            module_name = module.name
            module.delete()
            messages.success(request, f"✅ Le module {module_name} a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la suppression: {str(e)}")
    
    return redirect('accounts:modules_list')


# ============ VUES POUR LA GESTION DES RÉSULTATS ============
@login_required
@permission_required('accounts.can_view_results_list', raise_exception=True)
def results_list(request):
    """Vue pour afficher tous les résultats avec filtres"""
    # Si l'utilisateur est un étudiant, ne montrer que ses propres résultats
    if request.user.profil == 'student' and not request.user.is_staff and not request.user.is_superuser:
        results = Result.objects.filter(student=request.user).select_related('student', 'module')
        students = User.objects.filter(id=request.user.id)  # Seulement l'étudiant lui-même
    else:
        results = Result.objects.all().select_related('student', 'module')
        students = User.objects.filter(profil='student')
    
    # Filtres (uniquement pour admin/staff)
    student_id = request.GET.get('student')
    module_id = request.GET.get('module')
    semester = request.GET.get('semester')
    
    if student_id and (request.user.is_staff or request.user.is_superuser):
        results = results.filter(student_id=student_id)
    if module_id:
        results = results.filter(module_id=module_id)
    if semester:
        results = results.filter(semester=semester)
    
    modules = Module.objects.all()
    
    semesters = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ]
    
    # Calcul des statistiques de la classe
    if results.exists():
        scores = [result.score for result in results]
        class_stats = {
            'average': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
        }
    else:
        class_stats = {
            'average': 0,
            'highest_score': 0,
            'lowest_score': 0,
        }
    
    context = {
        'results': results,
        'students': students,
        'modules': modules,
        'semesters': semesters,
        'selected_student': student_id,
        'selected_module': module_id,
        'selected_semester': semester,
        'is_admin': request.user.is_superuser,
        'class_stats': class_stats,  # Ajout des statistiques
        'title': 'Gestion des Résultats' if (request.user.is_staff or request.user.is_superuser) else 'Mes Résultats'
    }
    return render(request, 'results/results_list.html', context)


@login_required
def student_results(request, student_id):
    """Vue pour afficher les résultats d'un étudiant spécifique"""
    # Vérifier que l'étudiant peut seulement voir ses propres résultats
    if not (request.user.has_perm('accounts.cans_view_results') or 
            (request.user.has_perm('accounts.can_view_own_results') and 
             request.user.id == student_id)):
        raise PermissionDenied("Vous n'êtes pas autorisé à voir ces résultats.")
    
    student = get_object_or_404(User, id=student_id, profil='student')
    results = Result.objects.filter(student=student).select_related('module')
    
    # Calcul des statistiques
    total_score = sum(result.score for result in results)
    average = total_score / len(results) if results else 0
    
    # Calcul des notes extrêmes
    if results:
        meilleure_note = max(result.score for result in results)
        plus_faible_note = min(result.score for result in results)
        results_validés = sum(1 for result in results if result.score >= 10)
    else:
        meilleure_note = 0
        plus_faible_note = 0
        results_validés = 0
    
    context = {
        'student': student,
        'results': results,
        'average': round(average, 2),
        'meilleure_note': round(meilleure_note, 2),
        'plus_faible_note': round(plus_faible_note, 2),
        'results_validés': results_validés,
        'title': f'Résultats de {student.get_full_name()}'
    }
    return render(request, 'results/student_results.html', context)



@login_required
def module_results(request, module_id):
    """Vue pour afficher les résultats d'un module spécifique"""
    module = get_object_or_404(Module, id=module_id)
    results = Result.objects.filter(module=module).select_related('student')
    
    context = {
        'module': module,
        'results': results,
        'title': f'Résultats du module {module.name}'
    }
    return render(request, 'accounts/module_results.html', context)

@login_required
def add_grades(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    students = User.objects.filter(profil='student')
    
    if request.method == 'POST':
        for student in students:
            score_key = f'score_{student.id}'
            exam_date_key = f'exam_date_{student.id}'
            comments_key = f'comments_{student.id}'
            
            if score_key in request.POST and request.POST[score_key]:
                try:
                    score = float(request.POST[score_key])
                    exam_date = request.POST[exam_date_key]
                    comments = request.POST.get(comments_key, '')
                    
                    # Fournir une valeur par défaut si module.semester est None
                    semester = module.semester if module.semester else 'S1'
                    
                    result, created = Result.objects.update_or_create(
                        student=student,
                        module=module,
                        defaults={
                            'score': score,
                            'exam_date': exam_date,
                            'comments': comments,
                            'semester': semester
                        }
                    )
                except ValueError:
                    messages.error(request, f"Valeur de note invalide pour {student.get_full_name()}")
        
        messages.success(request, "Les notes ont été enregistrées avec succès.")
        return redirect('accounts:modules_list')
    
    existing_results = {}
    for result in Result.objects.filter(module=module):
        existing_results[result.student.id] = result
    
    context = {
        'module': module,
        'students': students,
        'existing_results': existing_results,
    }
    
    return render(request, 'modules/add_grades.html', context)


@login_required
def create_result(request):
    """Vue pour créer un nouveau résultat"""
    if not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Seuls les administrateurs et le staff peuvent créer des résultats.")
    
    if request.method == 'POST':
        try:
            result = Result.objects.create(
                student_id=request.POST['student'],
                module_id=request.POST['module'],
                score=request.POST['score'],
                exam_date=request.POST['exam_date'],
                semester=request.POST['semester'],
                comments=request.POST.get('comments', '')
            )
            messages.success(request, f"Résultat créé avec succès pour {result.student.get_full_name()}!")
            return redirect('accounts:results_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du résultat: {str(e)}")
            return redirect('accounts:results_list')
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def update_result(request, result_id):
    """Vue pour modifier un résultat"""
    result = get_object_or_404(Result, id=result_id)
    
    if not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Seuls les administrateurs et le staff peuvent modifier des résultats.")
    
    if request.method == 'POST':
        try:
            result.student_id = request.POST['student']
            result.module_id = request.POST['module']
            result.score = request.POST['score']
            result.exam_date = request.POST['exam_date']
            result.semester = request.POST['semester']
            result.comments = request.POST.get('comments', '')
            result.save()
            
            messages.success(request, "Résultat modifié avec succès!")
            return redirect('accounts:results_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
            return redirect('accounts:results_list')
    
    students = User.objects.filter(profil='student')
    modules = Module.objects.all()
    semesters = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ]
    
    context = {
        'result': result,
        'students': students,
        'modules': modules,
        'semesters': semesters,
        'title': 'Modifier le résultat'
    }
    return render(request, 'results/update_result.html', context)


@login_required
def delete_result(request, result_id):
    """Vue pour supprimer un résultat"""
    if not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Seuls les administrateurs et le staff peuvent supprimer des résultats.")
    
    if request.method == 'POST':
        try:
            result = get_object_or_404(Result, id=result_id)
            result.delete()
            messages.success(request, "Résultat supprimé avec succès!")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
    
    return redirect('accounts:results_list')


@login_required
def export_results(request):
    """Vue pour exporter les résultats en CSV"""
    results = Result.objects.all().select_related('student', 'module')
    
    # Filtrer si nécessaire
    student_id = request.GET.get('student')
    module_id = request.GET.get('module')
    semester = request.GET.get('semester')
    
    if student_id:
        results = results.filter(student_id=student_id)
    if module_id:
        results = results.filter(module_id=module_id)
    if semester:
        results = results.filter(semester=semester)
    
    # Créer un fichier CSV en mémoire
    output = StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['Étudiant', 'Module', 'Code', 'Note', 'Mention', 'Semestre', 'Date examen'])
    
    # Données
    for result in results:
        writer.writerow([
            result.student.get_full_name(),
            result.module.name,
            result.module.code,
            str(result.score),
            result.get_grade(),
            result.get_semester_display(),
            result.exam_date.strftime("%d/%m/%Y")
        ])
    
    # Préparer la réponse
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="resultats.csv"'
    
    return response



@login_required
def generate_bulletin(request, student_id):
    """Vue pour générer le bulletin d'un étudiant"""
    # Vérifier que l'étudiant peut seulement voir son propre bulletin
    if request.user.profil == 'student' and str(request.user.id) != str(student_id):
        raise PermissionDenied("Vous ne pouvez accéder qu'à vos propres résultats.")
    
    student = get_object_or_404(User, id=student_id, profil='student')
    results = Result.objects.filter(student=student).select_related('module')
    
    # Calcul des moyennes par semestre
    semesters = {}
    for result in results:
        if result.semester not in semesters:
            semesters[result.semester] = []
        semesters[result.semester].append(result)
    
    # Calcul de la moyenne générale
    total_score = sum(result.score for result in results)
    general_average = total_score / len(results) if results else 0
    
    context = {
        'student': student,
        'semesters': semesters,
        'general_average': round(general_average, 2),
        'title': f'Bulletin de {student.get_full_name()}'
    }
    
    # Si demande CSV
    if request.GET.get('format') == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Bulletin de notes -', student.get_full_name()])
        writer.writerow([])
        writer.writerow(['Module', 'Code', 'Note', 'Mention', 'Semestre', 'Date examen'])
        
        for result in results:
            writer.writerow([
                result.module.name,
                result.module.code,
                str(result.score),
                result.get_grade(),
                result.get_semester_display(),
                result.exam_date.strftime("%d/%m/%Y")
            ])
        
        writer.writerow([])
        writer.writerow(['Moyenne générale:', f"{general_average:.2f}/20"])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bulletin_{student.username}.csv"'
        return response
    
    return render(request, 'results/bulletin.html', context)


# ============ VUES POUR LE CONTACT ET INFORMATIONS ============
def contact(request):
    """Vue pour la page de contact"""
    if request.method == 'POST':
        try:
            # Créer le message de contact
            contact_message = ContactMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=request.POST['name'],
                email=request.POST['email'],
                message_type=request.POST['message_type'],
                subject=request.POST['subject'],
                message=request.POST['message']
            )
            
            # Envoyer un email de confirmation (optionnel)
            if settings.DEFAULT_FROM_EMAIL:
                try:
                    send_mail(
                        f"Confirmation de votre message: {contact_message.subject}",
                        f"Merci de nous avoir contacté. Nous traitons votre {contact_message.get_message_type_display().lower()} et vous répondrons bientôt.\n\nVotre message:\n{contact_message.message}",
                        settings.DEFAULT_FROM_EMAIL,
                        [contact_message.email],
                        fail_silently=True,
                    )
                except:
                    pass
            
            messages.success(request, "Votre message a été envoyé avec succès! Nous vous répondrons bientôt.")
            return redirect('accounts:contact')
            
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite: {str(e)}")
            return redirect('accounts:contact')
    
    # GET request - afficher le formulaire
    return render(request, 'contact/contact.html', {'title': 'Contactez-nous'})


@login_required
def suggestions_list(request):
    """Vue pour afficher les suggestions et problèmes (admin seulement)"""
    if not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Seuls les administrateurs peuvent accéder à cette page.")
    
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    
    # Filtres
    message_type = request.GET.get('type')
    status = request.GET.get('status')
    
    if message_type:
        messages_list = messages_list.filter(message_type=message_type)
    if status:
        messages_list = messages_list.filter(status=status)
    
    context = {
        'messages': messages_list,
        'selected_type': message_type,
        'selected_status': status,
        'title': 'Suggestions et Problèmes'
    }
    return render(request, 'contact/suggestions_list.html', context)


@login_required
def suggestion_detail(request, message_id):
    """Vue pour afficher les détails d'un message (admin seulement)"""
    if not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Seuls les administrateurs peuvent accéder à cette page.")
    
    message = get_object_or_404(ContactMessage, id=message_id)
    
    context = {
        'message': message,
        'title': f'Message: {message.subject}'
    }
    return render(request, 'contact/suggestion_detail.html', context)


@login_required
def update_suggestion_status(request, message_id):
    """Vue pour mettre à jour le statut d'un message (admin seulement)"""
    if not request.user.is_superuser and not request.user.is_staff:
        raise PermissionDenied("Seuls les administrateurs peuvent modifier les statuts.")
    
    if request.method == 'POST':
        try:
            message = get_object_or_404(ContactMessage, id=message_id)
            new_status = request.POST.get('status')
            
            if new_status in dict(ContactMessage.STATUS_CHOICES).keys():
                message.status = new_status
                message.save()
                
                # Envoyer un email de mise à jour (optionnel)
                if settings.DEFAULT_FROM_EMAIL and message.email:
                    try:
                        status_display = dict(ContactMessage.STATUS_CHOICES)[new_status]
                        send_mail(
                            f"Mise à jour de votre message: {message.subject}",
                            f"Le statut de votre message a été mis à jour: {status_display}.\n\nMessage original:\n{message.message}",
                            settings.DEFAULT_FROM_EMAIL,
                            [message.email],
                            fail_silently=True,
                        )
                    except:
                        pass
                
                messages.success(request, f"Statut mis à jour: {dict(ContactMessage.STATUS_CHOICES)[new_status]}")
            else:
                messages.error(request, "Statut invalide.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
    
    return redirect('contact/suggestion_detail', message_id=message_id)


def faq_list(request):
    """Vue pour afficher la FAQ"""
    faqs = FAQ.objects.filter(is_active=True).order_by('order', 'category', 'question')
    
    # Grouper par catégorie
    faqs_by_category = {}
    for faq in faqs:
        if faq.category not in faqs_by_category:
            faqs_by_category[faq.category] = []
        faqs_by_category[faq.category].append(faq)
    
    context = {
        'faqs_by_category': faqs_by_category,
        'title': 'Foire Aux Questions (FAQ)'
    }
    return render(request, 'contact/faq.html', context)


def school_info(request):
    """Vue pour afficher les informations de l'école"""
    school_info = SchoolInfo.objects.filter(is_active=True).first()
    
    context = {
        'school_info': school_info,
        'title': 'Informations sur l\'école'
    }
    return render(request, 'contact/school_info.html', context)


# ============ VUES PROFIL UTILISATEUR ============
@login_required
def profile(request):
    """Vue pour afficher le profil utilisateur"""
    return render(request, 'profile/profile.html', {
        'user': request.user
    })