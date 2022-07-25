from django import template

register = template.Library()


@register.filter(name="nextitem")
def next_item(value, current_index):
    return value[int(current_index) + 1]
