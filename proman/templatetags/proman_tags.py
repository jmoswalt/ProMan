from django.template import Library

from proman.models import HOURLY_RATE

register = Library()

@register.inclusion_tag("proman/harvest/progress-bar.html", takes_context=True)
def harvest_progress_bar(context, project):
    harvest_on = True
    if harvest_on:
        context.update({
            "project": project,
            "hourly_rate": HOURLY_RATE,
        })
        return context
    return ""

@register.inclusion_tag("proman/action_flag_icon.html", takes_context=True)
def action_flag_icon(context, af):
    context.update({
        "af": af,
    })
    return context
