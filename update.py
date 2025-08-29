from django.contrib.auth import get_user_model
from appBrowser.models import PaperInfo

User = get_user_model()
user = User.objects.get(username="noyon")  # pick the user you want
PaperInfo.objects.update(owner=user)