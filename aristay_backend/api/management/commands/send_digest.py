from django.core.management.base import BaseCommand
from api.services.email_digest_service import EmailDigestService

class Command(BaseCommand):
    help = "Send daily digest emails to users"

    def handle(self, *args, **kwargs):
        EmailDigestService.send_daily_digest()
        self.stdout.write(self.style.SUCCESS("✅ Digest sent!"))