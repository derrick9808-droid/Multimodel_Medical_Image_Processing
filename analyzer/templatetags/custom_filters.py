from django import template

register = template.Library()

@register.filter(name='dict_lookup')
def dict_lookup(dict_obj, key):
    """Safely retrieves a value from a dictionary by string or int key."""
    if not dict_obj or not isinstance(dict_obj, dict):
        return ""
    # Try exact key, stringified key, or integer key
    if key in dict_obj:
        return dict_obj[key]
    str_key = str(key)
    if str_key in dict_obj:
        return dict_obj[str_key]
    try:
        int_key = int(key)
        if int_key in dict_obj:
            return dict_obj[int_key]
    except Exception:
        pass
    return ""
