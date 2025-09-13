from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from api.models import (
    Property,
    Booking,
    Task,
    Notification,
    InventoryItem,
    InventoryCategory,
    PropertyInventory,
    Profile,
)


class Command(BaseCommand):
    help = "Seed test data (users, properties, bookings, tasks, notifications, inventory). Idempotent."

    def handle(self, *args, **options):
        generator = TestDataGenerator()
        generator.run()


class TestDataGenerator:
    def __init__(self):
        self.users = {}
        self.properties = []
        self.bookings = []
        self.tasks = []

    def _ensure_profile(self, user, role='staff'):
        profile, created = Profile.objects.get_or_create(user=user)
        if created or profile.role != role:
            profile.role = role
            profile.save(update_fields=['role'])

    def create_users(self):
        self.stdout("\nCreating users and profiles...")
        User = get_user_model()

        users_def = [
            {"key": "super", "username": "admin_super", "password": "admin123", "is_superuser": True, "role": "superuser"},
            {"key": "manager", "username": "manager_alice", "password": "manager123", "is_superuser": False, "role": "manager"},
            {"key": "staff", "username": "staff_bob", "password": "staff123", "is_superuser": False, "role": "staff"},
            {"key": "crew_charlie", "username": "crew_charlie", "password": "crew123", "is_superuser": False, "role": "staff"},
            {"key": "crew_diana", "username": "crew_diana", "password": "crew123", "is_superuser": False, "role": "staff"},
            {"key": "crew_eve", "username": "crew_eve", "password": "crew123", "is_superuser": False, "role": "staff"},
        ]

        for ud in users_def:
            user, _ = User.objects.get_or_create(username=ud["username"], defaults={
                "is_superuser": ud["is_superuser"],
                "email": f"{ud['username']}@example.com",
            })
            # Always ensure password is set to known value
            user.set_password(ud["password"])  # nosec - test only
            user.save(update_fields=["password"])
            self._ensure_profile(user, ud["role"])
            self.users[ud["key"]] = user
            self.stdout(f"✅ User ready: {user.username}")

    def create_properties(self):
        self.stdout("\nCreating properties...")
        # Only include fields that exist on Property model in this project
        props = [
            {"name": "Sunset Villa", "address": "123 Beach Ave"},
            {"name": "Downtown Loft", "address": "456 City St"},
            {"name": "Mountain Cabin", "address": "789 Pine Rd"},
            {"name": "City Condo", "address": "321 Skyline Blvd"},
        ]
        for pd in props:
            prop, _ = Property.objects.get_or_create(name=pd["name"], defaults=pd)
            self.properties.append(prop)
            self.stdout(f"✅ Property ready: {prop.name}")

    def create_bookings(self):
        self.stdout("\nCreating bookings...")
        now = timezone.now()
        booking_defs = [
            {"guest_name": "John & Sarah Smith", "check_in_date": now + timedelta(days=1), "check_out_date": now + timedelta(days=5), "property": self.properties[0], "source": "airbnb", "external_code": "AB1234"},
            {"guest_name": "Maria Garcia", "check_in_date": now + timedelta(days=2), "check_out_date": now + timedelta(days=4), "property": self.properties[1], "source": "vrbo", "external_code": "VR5678"},
            {"guest_name": "Johnson Family", "check_in_date": now + timedelta(days=3), "check_out_date": now + timedelta(days=8), "property": self.properties[2], "source": "direct", "external_code": "DIR000001"},
            {"guest_name": "David Wilson", "check_in_date": now - timedelta(days=3), "check_out_date": now - timedelta(days=1), "property": self.properties[0], "source": "airbnb", "external_code": "AB9999"},
        ]
        for bd in booking_defs:
            booking, _ = Booking.objects.get_or_create(
                property=bd["property"],
                external_code=bd["external_code"],
                defaults={
                    "guest_name": bd["guest_name"],
                    "check_in_date": bd["check_in_date"],
                    "check_out_date": bd["check_out_date"],
                    "source": bd["source"],
                },
            )
            self.bookings.append(booking)
            self.stdout(f"✅ Booking ready: {booking.guest_name} @ {booking.property.name}")

    def create_tasks(self):
        self.stdout("\nCreating tasks...")
        now = timezone.now()
        task_data = [
            {
                "title": "Pre-arrival Cleaning - Sunset Villa",
                "description": "Deep clean and prepare for John & Sarah Smith arrival",
                "task_type": "cleaning",
                "property_ref": self.properties[0],
                "booking": self.bookings[0],
                "status": "pending",
                "assigned_to": self.users["staff"],
                "due_date": self.bookings[0].check_in_date - timedelta(hours=2),
                "created_by": self.users["manager"],
            },
            {
                "title": "Post-checkout Cleaning - Sunset Villa",
                "description": "Clean after David Wilson checkout",
                "task_type": "cleaning",
                "property_ref": self.properties[0],
                "booking": self.bookings[3],
                "status": "in-progress",
                "assigned_to": self.users["staff"],
                "due_date": self.bookings[3].check_out_date + timedelta(hours=1),
                "created_by": self.users["manager"],
            },
            {
                "title": "Downtown Loft - Pre-arrival Setup",
                "description": "Setup and welcome amenities for Maria Garcia",
                "task_type": "cleaning",
                "property_ref": self.properties[1],
                "booking": self.bookings[1],
                "status": "pending",
                "assigned_to": self.users["crew_diana"],
                "due_date": self.bookings[1].check_in_date - timedelta(hours=1),
                "created_by": self.users["manager"],
            },
            {
                "title": "Mountain Cabin - HVAC Maintenance",
                "description": "Check heating system before Johnson family arrival",
                "task_type": "maintenance",
                "property_ref": self.properties[2],
                "booking": self.bookings[2],
                "status": "pending",
                "assigned_to": self.users["crew_charlie"],
                "due_date": self.bookings[2].check_in_date - timedelta(days=1),
                "created_by": self.users["manager"],
            },
            {
                "title": "City Condo - Routine Inspection",
                "description": "Weekly routine inspection and maintenance check",
                "task_type": "maintenance",
                "property_ref": self.properties[3],
                "status": "completed",
                "assigned_to": self.users["crew_charlie"],
                "due_date": now - timedelta(days=2),
                "created_by": self.users["manager"],
            },
            {
                "title": "Pool Maintenance - Sunset Villa",
                "description": "Weekly pool cleaning and chemical balance",
                "task_type": "maintenance",
                "property_ref": self.properties[0],
                "status": "pending",
                "assigned_to": self.users["crew_eve"],
                "due_date": now + timedelta(days=1),
                "created_by": self.users["manager"],
            },
        ]

        for task_info in task_data:
            task, _ = Task.objects.get_or_create(
                title=task_info["title"],
                defaults=task_info,
            )
            self.tasks.append(task)
            self.stdout(f"✅ Task ready: {task.title}")

    def create_notifications(self):
        self.stdout("\nCreating notifications...")
        notification_data = [
            {"recipient": self.users["staff"], "task": self.tasks[0], "verb": "assigned", "read": False},
            {"recipient": self.users["crew_charlie"], "task": self.tasks[3], "verb": "assigned", "read": False},
            {"recipient": self.users["manager"], "task": self.tasks[4], "verb": "status_changed", "read": True},
            {"recipient": self.users["staff"], "task": self.tasks[1], "verb": "status_changed", "read": False},
        ]
        for nd in notification_data:
            notif, _ = Notification.objects.get_or_create(
                recipient=nd["recipient"], task=nd["task"], verb=nd["verb"], defaults={"read": nd["read"]}
            )
            self.stdout(f"✅ Notification ready: {notif.verb} → {notif.task.title}")

    def create_inventory_items(self):
        self.stdout("\nCreating inventory items...")
        # Ensure categories exist
        category_names = ["Cleaning", "Linens", "Maintenance", "Amenities"]
        name_to_category = {}
        for cname in category_names:
            cat, _ = InventoryCategory.objects.get_or_create(name=cname)
            name_to_category[cname] = cat

        items = [
            {"name": "All-Purpose Cleaner", "category": "Cleaning", "unit": "bottles"},
            {"name": "Toilet Paper", "category": "Cleaning", "unit": "rolls"},
            {"name": "Towels", "category": "Linens", "unit": "pieces"},
            {"name": "Bed Sheets", "category": "Linens", "unit": "sets"},
            {"name": "Light Bulbs", "category": "Maintenance", "unit": "pieces"},
            {"name": "Pool Chemicals", "category": "Maintenance", "unit": "containers"},
            {"name": "Welcome Basket", "category": "Amenities", "unit": "pieces"},
            {"name": "Coffee Pods", "category": "Amenities", "unit": "boxes"},
        ]
        for idf in items:
            defaults = {
                "unit": idf["unit"],
                "category": name_to_category[idf["category"]],
            }
            item, _ = InventoryItem.objects.get_or_create(name=idf["name"], defaults=defaults)
            for prop in self.properties:
                PropertyInventory.objects.get_or_create(
                    property_ref=prop,
                    item=item,
                    defaults={
                        "current_stock": random.randint(5, 50),
                        "par_level": random.randint(10, 60),
                    },
                )
            self.stdout(f"✅ Inventory ready: {item.name}")

    def run(self):
        self.create_users()
        self.create_properties()
        self.create_bookings()
        self.create_tasks()
        self.create_notifications()
        self.create_inventory_items()
        self.stdout("\n✅ TEST DATA GENERATION COMPLETE!")

    def stdout(self, msg: str):
        print(msg)


