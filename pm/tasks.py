from celery import task

from django.core.mail.message import EmailMessage
from django.core.mail import get_connection

@task()
def send_notification(subject, message, from_email, recipient_list, fail_silently=False):
    from django.conf import settings
    connection = get_connection(username=None,
                                    password=None,
                                    fail_silently=fail_silently)

    msg = EmailMessage(subject, message, settings.EMAIL_HOST_USER, recipient_list,
                        connection=connection, headers={'Reply-To': from_email})
    msg.content_subtype = "html"

    msg.send()

    return True
