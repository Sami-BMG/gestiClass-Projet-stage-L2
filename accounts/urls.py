from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView, assign_user_role
app_name = 'accounts'

urlpatterns = [
     
     path('login/', views.user_login,
          name='login'),

    
     path('logout/', views.logout_view,
         name='logout'),
    
     path('password-change/', views.change_password,
         name='password_change'),
    
    #path de la page de création d'utilisateur(eleve,enseignant)
     path('create-user/', views.create_user,
         name='create_user'),
    # Password reset avec vues personnalisées
     path('password-reset/', 
         CustomPasswordResetView.as_view(), 
         name='password_reset'),
    
    path('password-reset/done/', 
         CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
 
 #Chemins pour la gestion des élèves   
    path('students/list/', views.list_students,
         name='students_list'),
    
    path('students/create/', views.create_student,
         name='create_student'),
    
     path('students/<int:student_id>/update/', views.update_student
          , name='update_student'),
     
     path('students/<int:student_id>/detail/', views.student_detail,
          name='student_detail'),
     
     path('students/<int:student_id>/delete/', views.delete_student,
          name='delete_student'),
# chemins pour la gestion des enseignants
     path('teacher/list/', views.list_teachers,
         name='teachers_list'),
     
     path('teacher/create/', views.create_teacher,
         name='create_teacher'),
     
     path('teacher/<int:teacher_id>/update/', views.update_teacher,
          name='update_teacher'),
     
     path('teacher/<int:teacher_id>/detail/', views.teacher_detail,
          name='teacher_detail'),
       
     path('teacher/<int:teacher_id>/delete/', views.delete_teacher,
          name='delete_teacher'),
     
# chemins pour la gestion des modules
     path('modules/list/', views.modules_list,
          name='modules_list'),
    path('modules/create/', views.create_module,
         name='create_module'),
    path('modules/<int:module_id>/', views.module_detail,
         name='module_detail'),
    path('modules/<int:module_id>/update/', views.update_module,
         name='update_module'),
    path('modules/<int:module_id>/delete/', views.delete_module,
         name='delete_module'),
        
        
# URLs pour les résultats
    path('results/', views.results_list,
         name='results_list'),
    path('results/student/<int:student_id>/', views.student_results
         , name='student_results'),
    path('results/module/<int:module_id>/', views.module_results,
         name='module_results'),
    path('results/create/', views.create_result,
         name='create_result'),
    path('results/<int:result_id>/update/', views.update_result,
         name='update_result'),
    path('results/<int:result_id>/delete/', views.delete_result,
         name='delete_result'),
    path('results/bulletin/<int:student_id>/', views.generate_bulletin,
         name='generate_bulletin'),
    path('module/<int:module_id>/add-grades/', views.add_grades, name='add_grades'),
    
     # URLs pour le contact et les informations
    path('contact/', views.contact,
         name='contact'),
    path('suggestions/', views.suggestions_list,
         name='suggestions_list'),
    path('suggestions/<int:message_id>/', views.suggestion_detail,
         name='suggestion_detail'),
    path('suggestions/<int:message_id>/update-status/',
         views.update_suggestion_status,
         name='update_suggestion_status'),
    path('faq/', views.faq_list,
         name='faq_list'),
    path('school-info/', views.school_info,
         name='school_info'),
    #View pour le profil utilisateur
    path('profile/', views.profile,
         name='profile'),

     #url pour le bulletin en PDF
    path('results/bulletin/<int:student_id>/', views.generate_bulletin,
          name='generate_bulletin'),


          #url pour les roles 
    path('roles/', views.role_list, name='role_list'),
    path('roles/<int:role_id>/edit/', views.edit_role, name='edit_role'),
    path('roles/<int:role_id>/delete/', views.delete_role, name='delete_role'),
    path('user/<str:user_type>/<int:user_id>/assign-role/', views.assign_user_role, name='assign_user_role'),
    path('user/<int:user_id>/remove-role/', views.remove_user_role, name='remove_user_role'),    
]    
        