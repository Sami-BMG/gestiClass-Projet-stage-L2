from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Pages d'accueil par rôle (de la première version)
    path('', views.home, name='home'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    
    # Fonctionnalités du tableau de bord (de la deuxième version)
    path('update-student-info/', views.update_student_info, name='update_student_info'),
    path('update-teacher-info/', views.update_teacher_info, name='update_teacher_info'),
    path('get-students-by-class/', views.get_students_by_class, name='get_students_by_class'),
    
    # Gestion des suggestions (des deux versions)
    path('suggestions/', views.suggestions_list, name='suggestions_list'),
    path('suggestions/<int:suggestion_id>/mark-read/', views.mark_suggestion_read, name='mark_suggestion_read'),
    path('suggestions/<int:suggestion_id>/delete/', views.delete_suggestion, name='delete_suggestion'),
    path('get-suggestion-detail/', views.get_suggestion_detail, name='get_suggestion_detail'),
    
    #urls du planning 
    path('timetable/', views.timetable_view, name='timetable_view'),
    path('timetable/data/', views.get_timetable_data, name='get_timetable_data'),
    path('timetable/save/', views.save_timetable_data, name='save_timetable_data'),
    #path('timetable/clear/', views.clear_timetable, name='clear_timetable'),
    
    #urls du graphe
    path('module-chart-data/', views.module_chart_data, name='module_chart_data'),


]