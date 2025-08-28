"""
Management command to create sample recurring schedule templates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, timedelta
from api.models import (
    Property, ScheduleTemplate, ChecklistTemplate
)


class Command(BaseCommand):
    help = 'Create sample recurring schedule templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample recurring schedule templates...')
        
        # Get existing data
        admin_user = User.objects.get(username='admin')
        properties = list(Property.objects.all())
        cleaning_template = ChecklistTemplate.objects.get(name='Standard Room Cleaning')
        maintenance_template = ChecklistTemplate.objects.get(name='Property Maintenance Inspection')
        
        if not properties:
            self.stdout.write(self.style.ERROR('No properties found. Run create_sample_mvp_data first.'))
            return
        
        schedules_created = 0
        
        # Create weekly cleaning schedules for each property
        for prop in properties:
            # Weekly cleaning on Fridays
            schedule, created = ScheduleTemplate.objects.get_or_create(
                name=f'Weekly Cleaning - {prop.name}',
                task_type='cleaning',
                property_ref=prop,
                defaults={
                    'task_title_template': 'Weekly Cleaning - {property} ({date})',
                    'task_description_template': 'Complete weekly deep cleaning for {property}. Ensure all rooms are guest-ready.',
                    'frequency': 'weekly',
                    'interval': 1,
                    'weekday': 4,  # Friday
                    'start_date': date.today(),
                    'time_of_day': '10:00:00',
                    'advance_days': 2,  # Create task 2 days in advance
                    'checklist_template': cleaning_template,
                    'created_by': admin_user,
                }
            )
            if created:
                schedules_created += 1
                self.stdout.write(f'Created weekly cleaning schedule for {prop.name}')
        
        # Create monthly maintenance schedules for each property
        for prop in properties:
            schedule, created = ScheduleTemplate.objects.get_or_create(
                name=f'Monthly Maintenance - {prop.name}',
                task_type='maintenance',
                property_ref=prop,
                defaults={
                    'task_title_template': 'Monthly Maintenance - {property} ({date})',
                    'task_description_template': 'Complete monthly maintenance inspection and inventory check for {property}.',
                    'frequency': 'monthly',
                    'interval': 1,
                    'day_of_month': 1,  # First of the month
                    'start_date': date.today(),
                    'time_of_day': '09:00:00',
                    'advance_days': 3,  # Create task 3 days in advance
                    'checklist_template': maintenance_template,
                    'created_by': admin_user,
                }
            )
            if created:
                schedules_created += 1
                self.stdout.write(f'Created monthly maintenance schedule for {prop.name}')
        
        # Create a daily laundry check for the first property (as example)
        if properties:
            prop = properties[0]
            schedule, created = ScheduleTemplate.objects.get_or_create(
                name=f'Daily Laundry Check - {prop.name}',
                task_type='laundry',
                property_ref=prop,
                defaults={
                    'task_title_template': 'Daily Laundry Check - {property} ({date})',
                    'task_description_template': 'Check laundry status and restock linens as needed.',
                    'frequency': 'daily',
                    'interval': 1,
                    'start_date': date.today(),
                    'time_of_day': '08:00:00',
                    'advance_days': 1,
                    'created_by': admin_user,
                }
            )
            if created:
                schedules_created += 1
                self.stdout.write(f'Created daily laundry check for {prop.name}')
        
        # Create a quarterly deep clean schedule for all properties
        schedule, created = ScheduleTemplate.objects.get_or_create(
            name='Quarterly Deep Clean - All Properties',
            task_type='cleaning',
            property_ref=None,  # Applies to all properties
            defaults={
                'task_title_template': 'Quarterly Deep Clean - {property} ({date})',
                'task_description_template': 'Comprehensive quarterly deep cleaning including carpets, windows, and detailed maintenance.',
                'frequency': 'quarterly',
                'interval': 1,
                'start_date': date.today(),
                'time_of_day': '09:00:00',
                'advance_days': 7,  # Create task 1 week in advance
                'checklist_template': cleaning_template,
                'created_by': admin_user,
            }
        )
        if created:
            schedules_created += 1
            self.stdout.write('Created quarterly deep clean schedule (all properties)')
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {schedules_created} recurring schedule templates')
        )
