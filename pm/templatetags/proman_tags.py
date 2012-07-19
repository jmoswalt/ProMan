from django.template import Library

from pm.models import DEFAULT_RATE, get_setting

register = Library()

@register.inclusion_tag("proman/harvest/progress-bar.html", takes_context=True)
def harvest_progress_bar(context, project):
    harvest_on = True
    if harvest_on:
        context.update({
            "project": project,
            "hourly_rate": get_setting('hourly_rate', DEFAULT_RATE),
        })
        return context
    return ""

@register.inclusion_tag("proman/action_flag_icon.html", takes_context=True)
def action_flag_icon(context, af):
    context.update({
        "af": af,
    })
    return context

@register.inclusion_tag("proman/profiles/add_link.html", takes_context=True)
def profile_add_link(context):
    if context['request'].user.is_staff or context['request'].user.is_superuser:
        context.update({
            "show_link": True,
        })
    return context