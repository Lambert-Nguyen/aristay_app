from django.core.management.base import BaseCommand
from api.services.email_digest_service import EmailDigestService

class Command(BaseCommand):
    help = "Send daily task email digest"

    def handle(self, *args, **options):
        EmailDigestService.send_daily_digest()
        self.stdout.write(self.style.SUCCESS("Digest email sent."))