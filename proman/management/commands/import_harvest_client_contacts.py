from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from proman.models import Client, ThirdParty, Profile
from proman.harvest import Harvest

class Command(BaseCommand):
    """
    Loads in Client Contacts from Harvest API
    """
    def handle(self, *args, **options):
        total = 0
        data = Harvest().client_contacts()
        if data:
            print "Receiving data..."
            for d in data:
                c = d['contact']
                print c
                try:
                    profile_match = ThirdParty.objects.get(
                        service_item_value=c['id'],
                        service_item_label="harvest_client_contact_id",
                        content_type=ContentType.objects.get(model='profile')
                    )
                    match = Profile.objects.get(id=profile_match.object_id)
                    print "MATCH!!! ", match
                except:
                    try:
                        tp = ThirdParty.objects.get(
                            content_type=ContentType.objects.get(model='client'),
                            service_item_label='harvest_client_id',
                            service_item_value=c['client_id'],
                        )
                        client = Client.objects.get(id=tp.object_id)
                    except:
                        client = None

                    username = "".join([c['first_name'], c['last_name']]).lower()[:29]

                    try:
                        user_exists = User.objects.get(username=username)
                        username = "".join([username, "1"]).lower()
                        try:
                            user_exists = User.objects.get(username=username)
                            username = "".join([username, "2"]).lower()
                        except:
                            pass
                    except:
                        pass

                    # make the user
                    user = User(
                        email=c['email'],
                        first_name=c['first_name'][:30],
                        last_name=c['last_name'][:30],
                        username=username,
                        date_joined=c['created_at'],
                        is_active=True,
                        is_staff=False,
                        is_superuser=False)
                    user.save()

                    # update the profile with the team and employee role
                    profile = Profile.objects.get(user=user)
                    profile.email = c['email']
                    profile.first_name = c['first_name']
                    profile.last_name = c['last_name']
                    profile.phone = c['phone_office']
                    profile.role = "client"
                    profile.client = client
                    profile.save()

                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='profile'),
                        object_id=profile.id,
                        service_item_label='harvest_client_contact_id',
                        service_item_value=c['id'],
                    )

                    obj, created = ThirdParty.objects.get_or_create(
                        content_type=ContentType.objects.get(model='profile'),
                        object_id=profile.id,
                        service_item_label='harvest_client_contact_client_id',
                        service_item_value=c['client_id'],
                    )

                    total += 1
            print "Done. Added %s of %s Client Contacts" % (total, len(data))
