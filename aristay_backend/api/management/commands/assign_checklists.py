#!/usr/bin/env python3
"""
Assign checklist templates to existing tasks
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Task, ChecklistTemplate, TaskChecklist, ChecklistResponse


class Command(BaseCommand):
    help = 'Assign checklist templates to existing tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-type',
            type=str,
            help='Only assign checklists to tasks of this type (e.g., cleaning, maintenance)',
        )
        parser.add_argument(
            '--template-id',
            type=int,
            help='Use specific template ID instead of auto-matching by task type',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Assign checklists even to tasks that already have them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        task_type = options.get('task_type')
        template_id = options.get('template_id')

        # Get tasks to process
        tasks_query = Task.objects.filter(is_deleted=False)
        
        if task_type:
            tasks_query = tasks_query.filter(task_type=task_type)
        
        if not force:
            # Exclude tasks that already have checklists
            tasks_query = tasks_query.filter(checklist__isnull=True)
        
        tasks = tasks_query.all()
        
        if not tasks:
            self.stdout.write('No tasks found matching criteria')
            return

        self.stdout.write(f'Found {tasks.count()} tasks to process')

        # Get template to use
        if template_id:
            try:
                template = ChecklistTemplate.objects.get(id=template_id)
                self.stdout.write(f'Using template: {template.name}')
            except ChecklistTemplate.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Template with ID {template_id} not found'))
                return
        else:
            # Auto-match by task type
            templates_by_type = {}
            for template in ChecklistTemplate.objects.filter(is_active=True):
                if template.task_type not in templates_by_type:
                    templates_by_type[template.task_type] = []
                templates_by_type[template.task_type].append(template)
            
            self.stdout.write('Available templates by task type:')
            for ttype, templates in templates_by_type.items():
                self.stdout.write(f'  {ttype}: {len(templates)} templates')
                for template in templates:
                    self.stdout.write(f'    - {template.name} (ID: {template.id})')

        assigned_count = 0
        skipped_count = 0

        for task in tasks:
            # Determine which template to use
            if template_id:
                task_template = template
            else:
                # Find best matching template
                matching_templates = ChecklistTemplate.objects.filter(
                    task_type=task.task_type,
                    is_active=True
                ).order_by('name')
                
                if not matching_templates.exists():
                    self.stdout.write(f'  ⚠️  No template found for task type "{task.task_type}" - {task.title}')
                    skipped_count += 1
                    continue
                
                task_template = matching_templates.first()

            if dry_run:
                self.stdout.write(f'  Would assign "{task_template.name}" to "{task.title}"')
                assigned_count += 1
            else:
                try:
                    with transaction.atomic():
                        # Create task checklist
                        task_checklist, created = TaskChecklist.objects.get_or_create(
                            task=task,
                            template=task_template,
                            defaults={
                                'started_at': None,
                                'completed_at': None,
                                'completed_by': None,
                            }
                        )
                        
                        if not created and not force:
                            self.stdout.write(f'  ⚠️  Task already has checklist - {task.title}')
                            skipped_count += 1
                            continue
                        
                        # Create responses for all checklist items
                        for item in task_template.items.all():
                            ChecklistResponse.objects.get_or_create(
                                checklist=task_checklist,
                                item=item,
                                defaults={
                                    'is_completed': False,
                                    'text_response': '',
                                    'number_response': None,
                                    'completed_at': None,
                                    'completed_by': None,
                                    'notes': '',
                                }
                            )
                        
                        self.stdout.write(f'  ✅ Assigned "{task_template.name}" to "{task.title}"')
                        assigned_count += 1
                        
                except Exception as e:
                    self.stdout.write(f'  ❌ Error assigning checklist to "{task.title}": {str(e)}')
                    skipped_count += 1

        # Summary
        if dry_run:
            self.stdout.write(f'\n📊 DRY RUN SUMMARY:')
            self.stdout.write(f'  Would assign: {assigned_count} tasks')
            self.stdout.write(f'  Would skip: {skipped_count} tasks')
        else:
            self.stdout.write(f'\n📊 ASSIGNMENT SUMMARY:')
            self.stdout.write(f'  Successfully assigned: {assigned_count} tasks')
            self.stdout.write(f'  Skipped: {skipped_count} tasks')
            
            if assigned_count > 0:
                self.stdout.write(self.style.SUCCESS('✅ Checklist assignment completed!'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  No checklists were assigned'))
