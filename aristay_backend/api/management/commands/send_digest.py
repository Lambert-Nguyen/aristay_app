# api/management/commands/send_digest.py
import sys

from django.core.management.base import BaseCommand

from api.services.email_digest_service import EmailDigestService


class Command(BaseCommand):
    help = "Send daily task email digest"

    def handle(self, *args, **opts):
        n = EmailDigestService.send_daily_digest()
        print(f"[digest] {n} email(s) sent.")
