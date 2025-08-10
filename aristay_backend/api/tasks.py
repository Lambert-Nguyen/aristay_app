from api.services.email_digest_service import EmailDigestService

def send_daily_digest():
    """
    Thin wrapper so any scheduler that still imports api.tasks.send_daily_digest
    continues to work.  All real logic lives in the service.
    """
    EmailDigestService.send_daily_digest()