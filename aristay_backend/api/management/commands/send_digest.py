# api/management/commands/send_digest.py
from django.core.management.base import BaseCommand
from api.services.email_digest_service import EmailDigestService
import sys

class Command(BaseCommand):
    help = "Send daily task email digest"

    def handle(self, *args, **opts):
        n = EmailDigestService.send_daily_digest()
        print(f"[digest] {n} email(s) sent.")