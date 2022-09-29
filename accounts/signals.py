from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender = User)
def post_Save_create_profile_reciever(sender, instance, created, **kwargs):
    # print(created)
    if created:
        UserProfile.objects.create(user = instance)
        # print("create the user profile")
    else:
        try:
            profile = UserProfile.objects.get(user = instance)
            profile.save()
            # print("user is updated")
        except:
            UserProfile.objects.create(user = instance)
            # print("Profile was not exist but I created one")

# post_save.connect(post_Save_create_profile_reciever, sender = User)

@receiver(pre_save, sender = User)
def pre_save_profile_reciever(sender, instance, **kwargs):
    # print(instance.username, 'this user is being saved')
    pass