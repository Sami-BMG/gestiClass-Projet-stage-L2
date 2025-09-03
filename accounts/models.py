from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('teacher', 'Enseignant'),
        ('student', 'Élève'),
    )
    profil = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='users/', null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    def is_administrator(self):
        return self.profil == 'admin'
    
    def is_teacher(self):
        return self.profil == 'teacher'
    
    def is_student(self):
        return self.profil == 'student'
    
    def get_type(self):
        return self.profil == 'admin' if self.is_administrator() else 'teacher' if self.is_teacher() else 'student'

class Module(models.Model):
    SEMESTER_CHOICES = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nom du module")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code du module")
    description = models.TextField(blank=True, verbose_name="Description")
    coefficient = models.FloatField(default=1, verbose_name="Coefficient")
    credit = models.IntegerField(default=1, verbose_name="Crédits")
    semester = models.CharField(
        max_length=2, 
        choices=SEMESTER_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="Semestre"
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'profil': 'teacher'},
        verbose_name="Enseignant"
    )
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100)
    hire_date = models.DateField()
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialty}"

    class Meta:
        # CORRECTION : Utiliser un champ existant ou supprimer l'ordering
        ordering = ['user__last_name', 'user__first_name']  # Ordonner par nom de l'utilisateur

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}"

class Result(models.Model):
    SEMESTER_CHOICES = [
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profil': 'student'})
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Note")
    exam_date = models.DateField(verbose_name="Date de l'examen")
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES, verbose_name="Semestre")
    comments = models.TextField(blank=True, verbose_name="Commentaires")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    niveau = models.CharField(max_length=50, default='Non spécifié')

    class Meta:
        unique_together = ['student', 'module']
        ordering = ['-exam_date', 'module']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.module.code}: {self.score}"
    
    def get_grade(self):
        """Convertir la note en mention"""
        if self.score >= 16:
            return "Excellent"
        elif self.score >= 14:
            return "Très bien"
        elif self.score >= 12:
            return "Bien"
        elif self.score >= 10:
            return "Assez bien"
        else:
            return "Insuffisant"

# SUPPRIMER LES DOUBLONS CI-DESSOUS - Ces classes sont déjà définies plus haut

class ContactMessage(models.Model):
    TYPE_CHOICES = [
        ('suggestion', 'Suggestion'),
        ('problem', 'Problème'),
        ('question', 'Question'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
        ('closed', 'Fermé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de message")
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
    
    def __str__(self):
        return f"{self.subject} - {self.get_message_type_display()}"

class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'Général'),
        ('technical', 'Technique'),
        ('academic', 'Académique'),
        ('administration', 'Administration'),
        ('other', 'Autre'),
    ]
    
    question = models.CharField(max_length=255, verbose_name="Question")
    answer = models.TextField(verbose_name="Réponse")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Catégorie")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'category', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
    
    def __str__(self):
        return self.question

class SchoolInfo(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de l'école")
    address = models.TextField(verbose_name="Adresse")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Site web")
    description = models.TextField(verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Information de l'école"
        verbose_name_plural = "Informations de l'école"
    
    def __str__(self):
        return self.name
    
    
    
class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    valeur = models.FloatField()
    appreciation = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} - {self.module} : {self.valeur}"    