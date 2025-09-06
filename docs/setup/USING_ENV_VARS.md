# Using Environment Variables

## Overview

This project uses environment variables for configuration to ensure secrets and environment-specific settings are kept secure and separate from the codebase.

## Local Development Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual values:**
   - Replace `replace-me` placeholders with real values
   - Update URLs and hosts to match your local setup
   - Set `DEBUG=true` for development

3. **Important notes:**
   - The `.env` file is ignored by git and should never be committed
   - Each developer should have their own `.env` file with their specific configuration
   - The `.env` file will be automatically loaded during development

## Production/CI Deployment

1. **Set environment variables directly:**
   - On Heroku: `heroku config:set KEY=value`
   - On other platforms: Set via their environment variable configuration
   - In CI/CD: Set via your CI platform's secret management

2. **Disable .env loading (optional):**
   ```bash
   export LOAD_DOTENV=false
   ```
   - This is optional since .env loading is harmless if the file doesn't exist
   - Recommended for production to avoid any potential file system access

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key for cryptographic signing | `your-super-secret-key-here` |
| `DEBUG` | Enable/disable debug mode | `false` (production), `true` (development) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,yourdomain.com` |
| `EMAIL_HOST` | SMTP server hostname | `smtp.mailgun.org` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_USE_TLS` | Use TLS for email | `true` |
| `EMAIL_HOST_USER` | SMTP username | `your-email@example.com` |
| `EMAIL_HOST_PASSWORD` | SMTP password | `your-email-password` |
| `DEFAULT_FROM_EMAIL` | Default from email address | `noreply@yourdomain.com` |
| `USE_CLOUDINARY` | Enable Cloudinary file storage | `false` (local), `true` (production) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | `your-cloud-name` |
| `CLOUDINARY_API_KEY` | Cloudinary API key | `your-api-key` |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | `your-api-secret` |
| `SENTRY_DSN` | Sentry error tracking DSN | `https://...@sentry.io/...` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `https://yourfrontend.com` |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3000` |
| `REDIS_URL` | Redis connection URL (if using Redis) | `redis://localhost:6379` |
| `DATABASE_URL` | Database connection URL (for production) | `postgres://...` |
| `FCM_SERVER_KEY` | Firebase Cloud Messaging server key | `your-fcm-key` |

## Security Best Practices

1. **Never commit real secrets to git**
2. **Use different values for development, staging, and production**
3. **Rotate secrets regularly**
4. **Use strong, randomly generated secret keys**
5. **Limit access to production environment variables**
6. **Monitor for accidental secret exposure in logs**
