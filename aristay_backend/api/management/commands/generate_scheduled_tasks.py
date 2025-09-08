"""
Management command to generate tasks from recurring schedules.
This should be run daily via cron job or similar scheduling system.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime, timedelta
from api.models import (
    ScheduleTemplate, Task, TaskChecklist, ChecklistResponse, 
    GeneratedTask, Property
)


class Command(BaseCommand):
    help = 'Generate tasks from active recurring schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what tasks would be generated without creating them',
        )
        parser.add_argument(
            '--check-date',
            type=str,
            help='Check for a specific date (YYYY-MM-DD format)',
        )
        parser.add_argument(
            '--schedule-id',
            type=int,
            help='Generate tasks for a specific schedule ID only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        check_date = options.get('check_date')
        schedule_id = options.get('schedule_id')
        
        if check_date:
            try:
                check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            check_date = date.today()
        
        self.stdout.write(f'Checking for tasks to generate on {check_date}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No tasks will be created'))
        
        # Get active schedules
        schedules = ScheduleTemplate.objects.filter(is_active=True)
        if schedule_id:
            schedules = schedules.filter(id=schedule_id)
        
        generated_count = 0
        
        for schedule in schedules:
            if schedule.should_generate_task(check_date):
                try:
                    if dry_run:
                        self.stdout.write(
                            f'Would generate: {schedule.name} for {schedule.property_ref or "All Properties"}'
                        )
                        generated_count += 1
                    else:
                        task = self.generate_task_from_schedule(schedule, check_date)
                        if task:
                            self.stdout.write(
                                self.style.SUCCESS(f'Generated: {task.title}')
                            )
                            generated_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error generating task for {schedule.name}: {str(e)}')
                    )
        
        if dry_run:
            self.stdout.write(f'Would generate {generated_count} tasks')
        else:
            self.stdout.write(f'Generated {generated_count} tasks successfully')

    def generate_task_from_schedule(self, schedule, check_date):
        """Generate a task from a schedule template."""
        
        # Calculate the actual due date for the task
        due_date = schedule.get_next_due_date()
        due_datetime = datetime.combine(due_date, schedule.time_of_day)
        due_datetime = timezone.make_aware(due_datetime)
        
        # Generate task title and description
        context = {
            'date': due_date.strftime('%Y-%m-%d'),
            'property': schedule.property_ref.name if schedule.property_ref else 'Property',
        }
        
        task_title = schedule.task_title_template.format(**context)
        task_description = schedule.task_description_template.format(**context) if schedule.task_description_template else ""
        
        # Create the task
        task = Task.objects.create(
            task_type=schedule.task_type,
            title=task_title,
            description=task_description,
            property_ref=schedule.property_ref,
            status='pending',
            created_by=schedule.created_by,
            assigned_to=schedule.default_assignee,
            due_date=due_datetime,
        )
        
        # Create checklist if template is specified
        if schedule.checklist_template:
            task_checklist = TaskChecklist.objects.create(
                task=task,
                template=schedule.checklist_template
            )
            
            # Create responses for all checklist items
            for item in schedule.checklist_template.items.all():
                ChecklistResponse.objects.create(
                    checklist=task_checklist,
                    item=item,
                    is_completed=False  # Start with all items uncompleted
                )
        
        # Record that this task was generated
        GeneratedTask.objects.create(
            schedule=schedule,
            task=task,
            generated_for_date=due_date
        )
        
        # Update the schedule's last generated timestamp
        schedule.last_generated = timezone.now()
        schedule.save(update_fields=['last_generated'])
        
        return task
