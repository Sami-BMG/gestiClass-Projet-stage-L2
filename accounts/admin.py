from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Teacher, Module, Result, Timetable, InfoMessage, ContactMessage, FAQ, SchoolInfo, Question
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'profil', 'is_staff']
    list_filter = ['profil', 'is_staff', 'is_superuser', 'is_active']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
        ('Informations supplémentaires', {'fields': ('profil', 'phone', 'address', 'birth_date', 'photo', 'specialty', 'hire_date')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'profil', 'phone'),
        }),
    )
    
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'enrollment_date']  
    list_filter = ['enrollment_date']  
    raw_id_fields = ['user']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'user', 'hire_date')
    list_filter = ('hire_date',)
    search_fields = ('user__first_name', 'user__last_name', )
    raw_id_fields = ('user',)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'coefficient', 'credit', 'semester', 'teacher')
    list_filter = ('semester',)
    search_fields = ('name', 'code')
    raw_id_fields = ('teacher',)

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'module', 'score', 'exam_date', 'semester')
    list_filter = ('semester', 'exam_date', 'module')
    search_fields = ('student__first_name', 'student__last_name', 'module__name')
    raw_id_fields = ('student', 'module')

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['week_start', 'day', 'timeslot', 'module', 'teacher', 'classroom']
    list_filter = ['week_start', 'day', 'timeslot', 'module', 'teacher']
    search_fields = ['module__name', 'teacher__first_name', 'teacher__last_name', 'classroom']
    date_hierarchy = 'week_start'
    ordering = ['week_start', 'day', 'timeslot']


@admin.register(InfoMessage)
class InfoMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'updated_at', 'is_active')
    list_filter = ('audience', 'is_active')
    search_fields = ('title', 'content')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['email', 'category', 'question_short', 'is_answered', 'created_at']
    list_filter = ['category', 'is_answered', 'created_at']
    search_fields = ['question', 'email']
    list_editable = ['is_answered']
    
    def question_short(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_short.short_description = 'Question'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message_type', 'subject', 'status', 'created_at')
    list_filter = ('message_type', 'status', 'created_at')
    search_fields = ('name', 'email', 'subject')


@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active')
    list_filter = ('is_active',)

models_to_unregister = [Student, Teacher, Timetable,Module,Result,Timetable, TimetableAdmin,InfoMessage,ContactMessage,FAQ,SchoolInfo, Question]
for model in models_to_unregister:
    if admin.site.is_registered(model):
        admin.site.unregister(model)
        
        


admin.site.register(User)
admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Module)
admin.site.register(Result)
admin.site.register(Timetable, TimetableAdmin)
admin.site.register(InfoMessage)
admin.site.register(ContactMessage)
admin.site.register(Question, QuestionAdmin)        
admin.site.register(FAQ, FAQAdmin)
admin.site.register(SchoolInfo)


