# dashboard/templatetags/custom_filters.py
from django import template
from datetime import timedelta



register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Récupère une valeur d'un dictionnaire à partir d'une clé
    Usage: {{ my_dict|get_item:key }}
    """
    # Vérifier si c'est un dictionnaire
    if not isinstance(dictionary, dict):
        return None
    
    # Utiliser get() pour éviter KeyError
    return dictionary.get(key)

@register.filter
def replace(value, arg):
    """
    Remplace une chaîne par une autre
    Usage: {{ value|replace:"old,new" }}
    """
    if ',' in arg:
        original, replacement = arg.split(',', 1)
        return value.replace(original, replacement)
    return value

@register.filter
def get_profil_display(user):
    """
    Retourne le nom d'affichage du profil utilisateur
    """
    profil_map = {
        'admin': 'Administrateur',
        'teacher': 'Enseignant',
        'student': 'Étudiant',
    }
    return profil_map.get(user.profil, user.profil)

@register.filter
def day_french(day):
    """
    Convertit le jour anglais en français
    """
    days_map = {
        'monday': 'Lundi',
        'tuesday': 'Mardi',
        'wednesday': 'Mercredi',
        'thursday': 'Jeudi',
        'friday': 'Vendredi',
        'saturday': 'Samedi',
    }
    return days_map.get(day, day)

@register.filter
def add_days(date, days):
    """
    Ajoute un nombre de jours à une date
    Usage: {{ some_date|add_days:5 }}
    """
    try:
        return date + timedelta(days=int(days))
    except (ValueError, TypeError):
        return date
    
@register.filter
def get_nested(dictionary, keys):
    """
    Accède à une valeur nested dans un dictionnaire
    Usage: {{ my_dict|get_nested:"key1,key2" }}
    """
    if not dictionary:
        return None
        
    if isinstance(keys, str):
        keys = keys.split(',')
    
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current
    
    
    
    
    