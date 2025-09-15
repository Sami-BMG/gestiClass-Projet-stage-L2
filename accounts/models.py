from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


    

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
    address = models.TextField(blank=True)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    def is_administrator(self):
        return self.profil == 'admin'
    
    def is_teacher(self):
        return self.profil == 'teacher'
    
    def is_student(self):
        return self.profil == 'student'
    
    def get_type(self):
        return self.profil
    
    class Meta:
        permissions = [
        ("peut_acceder_module", "Peut acceder au module"),  
        ("peut_acceder_aux_eleve", "Peut acceder aux eleves"), 
        ("peut_acceder_aux_enseigants", "peut acceder aux enseigants"),  
        ("peut_acceder_aux_roles", "peut acceder aux roles"),  
        
        
        ("can_assign_roles", "Peut assigner des rôles aux utilisateurs"),

        
        ("peut_acceder_au_student_dashboard", "Peut accéder au tableau de bord étudiant"),
        ("peut_acceder_au_dashboard", "Peut accéder au tableau de bord enseignant"),
        ("peut_acceder_au_admin_dashboard", "Peut accéder au tableau de bord administrateur"),
        
        ("peut_voir_notes", "Peut voir toutes les notes"),
        ("peut voir_ses_notes", "Peut voir ses propres notes"),
        ("peut voir_student_list", "Peut voir la liste des étudiants"),
        ("peut voir_teacher_list", "Peut voir la liste des enseignants"),
        

        ]   
    

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now)
    
    class Meta:
        permissions = [
        ]
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.student_id})"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20,null=True, unique=True)
    hire_date = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.teacher_id})"
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']

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
    


class Note(models.Model):
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'profil': 'student'},
        verbose_name="Étudiant"
    )
    module = models.ForeignKey(
        'Module',
        on_delete=models.CASCADE,
        verbose_name="Module"
    )
    value = models.FloatField(
        verbose_name="Note",
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    date = models.DateField(
        auto_now_add=True,
        verbose_name="Date d'évaluation"
    )
    
    class Meta:
        unique_together = ['student', 'module']
    
    def __str__(self):
        return f"{self.student.username} - {self.module.code}: {self.value}"

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

class Timetable(models.Model):
    DAY_CHOICES = [
        ('MONDAY', 'Lundi'),
        ('TUESDAY', 'Mardi'),
        ('WEDNESDAY', 'Mercredi'),
        ('THURSDAY', 'Jeudi'),
        ('FRIDAY', 'Vendredi'),
        ('SATURDAY', 'Samedi'),
    ]
    
    TIMESLOT_CHOICES = [
        ('8-10', '8h-10h'),
        ('10-12', '10h-12h'),
        ('14-16', '14h-16h'),
        ('16-18', '16h-18h'),
    ]
    
    week_start = models.DateField(null=True,verbose_name="Début de semaine")
    day = models.CharField(max_length=10, choices=DAY_CHOICES, verbose_name="Jour")
    timeslot = models.CharField(max_length=5, choices=TIMESLOT_CHOICES, verbose_name="Créneau")
    module = models.ForeignKey('Module', on_delete=models.CASCADE, verbose_name="Module")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profil': 'teacher'}, verbose_name="Enseignant")
    classroom = models.CharField(max_length=50, blank=True, verbose_name="Salle")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        unique_together = ('week_start', 'day', 'timeslot')
        ordering = ['week_start', 'day', 'timeslot']
        verbose_name = "Emploi du temps"
        verbose_name_plural = "Emplois du temps"
        permissions = [
            ('can_manage_timetable', 'Peut gérer les emplois du temps'),
            ('can_publish_timetable', 'Peut publier les emplois du temps'),
        ]
    
    def __str__(self):
        return f"{self.week_start} - {self.get_day_display()} {self.get_timeslot_display()} - {self.module}"



class InfoMessage(models.Model):
    AUDIENCE_CHOICES = [
        ('student', 'Étudiants'),
        ('teacher', 'Enseignants'),
        ('all', 'Tous'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Info for {self.get_audience_display()} - {self.title}"

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
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        
    def __str__(self):
        return f"Message de {self.name} - {self.created_at}"
    
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