from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Récupère une valeur d'un dictionnaire à partir d'une clé
    Usage: {{ my_dict|get_item:key }}
    """
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