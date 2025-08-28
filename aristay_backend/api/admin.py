from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import (
    Property, Task, TaskImage, Notification, Booking, PropertyOwnership, Profile,
    ChecklistTemplate, ChecklistItem, TaskChecklist, ChecklistResponse, ChecklistPhoto,
    InventoryCategory, InventoryItem, PropertyInventory, InventoryTransaction,
    LostFoundItem, LostFoundPhoto, ScheduleTemplate, GeneratedTask,
    BookingImportTemplate, BookingImportLog
)
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

class CustomAdminSite(admin.AdminSite):
    site_header = "AriStay Administration"
    site_title = "AriStay Admin"
    index_title = "Welcome to AriStay Administration"
    
    def has_permission(self, request):
        # Restrict Superuser admin to Superusers only
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='admin_analytics'),
        ]
        return custom_urls + urls
    
    def analytics_view(self, request):
        # Redirect to our charts dashboard
        return HttpResponseRedirect('/api/admin/charts/')

# Use the custom admin site
admin_site = CustomAdminSite(name='admin')

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 0
    readonly_fields = ('uploaded_at', 'preview')
    fields = ('image', 'preview', 'uploaded_at')

    def preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />'
        return "No image"
    preview.allow_tags = True
    preview.short_description = 'Image Preview'

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'task_type', 'status', 'property', 'booking', 'assigned_to', 'created_at', 'due_date')
    list_filter = ('status', 'task_type', 'created_at', 'property', 'booking', 'assigned_to')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'modified_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'task_type', 'property', 'booking', 'status', 'assigned_to', 'due_date', 'depends_on')
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'modified_by', 'modified_at'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskImageInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'created_at', 'created_by')
    search_fields = ('name', 'address')
    readonly_fields = ('created_at', 'modified_at')

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
        
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'check_in_date', 'check_out_date', 'status', 'guest_name', 'guest_contact')
    list_filter = ('status', 'check_in_date', 'check_out_date', 'property')
    search_fields = ('property__name', 'guest_name', 'guest_contact')
    readonly_fields = ('created_at', 'modified_at')

class PropertyOwnershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'user', 'ownership_type', 'can_edit', 'created_at')
    list_filter = ('ownership_type', 'can_edit', 'property')
    search_fields = ('property__name', 'user__username', 'user__email')
    readonly_fields = ('created_at',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'task_title', 'verb', 'read', 'timestamp', 'read_at', 'push_sent')
    list_filter = ('read', 'verb', 'push_sent', 'timestamp')
    search_fields = ('recipient__username', 'task__title')
    readonly_fields = ('timestamp', 'push_sent')
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('recipient', 'task', 'verb', 'read', 'read_at')
        }),
        ('System Info', {
            'fields': ('timestamp', 'push_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def task_title(self, obj):
        return obj.task.title if obj.task else 'N/A'
    task_title.short_description = 'Task Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'task')

# Register models with the custom admin site
admin_site.register(Task, TaskAdmin)
admin_site.register(Property, PropertyAdmin)
admin_site.register(Notification, NotificationAdmin)
admin_site.register(Booking, BookingAdmin)
admin_site.register(PropertyOwnership, PropertyOwnershipAdmin)

# Also register with default admin for backward compatibility
admin.site.register(Task, TaskAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(PropertyOwnership, PropertyOwnershipAdmin)

# -------------------- User admin with Profile inline (Superuser admin and default admin) --------------------

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'
    fields = ('role', 'timezone', 'digest_opt_out')
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['help_text'] = 'Select user role: Administration/Cleaning/Maintenance/Laundry/Lawn Pool'
        return super().formfield_for_choice_field(db_field, request, **kwargs)

class SuperuserUserAdmin(DjangoUserAdmin):
    inlines = [ProfileInline]
    exclude = ('password',)  # hide hashed password from change form
    list_display = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined')

# Register on default admin site with profile inline
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, SuperuserUserAdmin)

# Register on custom admin site as well
try:
    admin_site.unregister(User)
except Exception:
    pass
admin_site.register(User, SuperuserUserAdmin)


# ============================================================================
# MVP Phase 1: Checklists, Inventory, Lost & Found Admin
# ============================================================================

# Checklist Admin
class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = ('title', 'item_type', 'is_required', 'order', 'room_type')
    ordering = ['order', 'room_type']

class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'is_active', 'created_at', 'created_by')
    list_filter = ('task_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ChecklistItemInline]
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class ChecklistPhotoInline(admin.TabularInline):
    model = ChecklistPhoto
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by')

class ChecklistResponseAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'item', 'is_completed', 'completed_at', 'completed_by')
    list_filter = ('is_completed', 'completed_at', 'item__item_type')
    search_fields = ('checklist__task__title', 'item__title')
    readonly_fields = ('completed_at',)
    inlines = [ChecklistPhotoInline]

class TaskChecklistAdmin(admin.ModelAdmin):
    list_display = ('task', 'template', 'completion_percentage', 'started_at', 'completed_at', 'completed_by')
    list_filter = ('template', 'started_at', 'completed_at')
    search_fields = ('task__title', 'template__name')
    readonly_fields = ('completion_percentage',)

# Inventory Admin
class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 0
    fields = ('name', 'unit', 'estimated_cost', 'is_active')

class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon')
    search_fields = ('name', 'description')
    inlines = [InventoryItemInline]

class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'estimated_cost', 'is_active', 'created_at')
    list_filter = ('category', 'unit', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'brand', 'sku')
    readonly_fields = ('created_at',)

class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 0
    readonly_fields = ('created_at', 'created_by')
    fields = ('transaction_type', 'quantity', 'task', 'notes', 'reference')

class PropertyInventoryAdmin(admin.ModelAdmin):
    list_display = ('property_ref', 'item', 'current_stock', 'par_level', 'stock_status', 'last_updated')
    list_filter = ('item__category', 'last_updated')
    search_fields = ('property_ref__name', 'item__name')
    readonly_fields = ('stock_status', 'last_updated')
    inlines = [InventoryTransactionInline]
    
    def stock_status(self, obj):
        status = obj.stock_status
        colors = {
            'out_of_stock': 'red',
            'low_stock': 'orange', 
            'normal': 'green',
            'overstocked': 'blue'
        }
        return f'<span style="color: {colors.get(status, "black")}">{status.replace("_", " ").title()}</span>'
    stock_status.allow_tags = True
    stock_status.short_description = 'Stock Status'

class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('property_inventory', 'transaction_type', 'quantity', 'task', 'created_at', 'created_by')
    list_filter = ('transaction_type', 'created_at', 'property_inventory__property_ref')
    search_fields = ('property_inventory__property_ref__name', 'property_inventory__item__name', 'notes')
    readonly_fields = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Lost & Found Admin
class LostFoundPhotoInline(admin.TabularInline):
    model = LostFoundPhoto
    extra = 0
    readonly_fields = ('uploaded_at', 'uploaded_by')

class LostFoundItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_ref', 'status', 'found_date', 'found_by', 'estimated_value')
    list_filter = ('status', 'found_date', 'property_ref', 'category')
    search_fields = ('title', 'description', 'property_ref__name', 'found_location')
    readonly_fields = ('found_date',)
    inlines = [LostFoundPhotoInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'estimated_value', 'property_ref', 'task', 'booking')
        }),
        ('Location & Status', {
            'fields': ('found_location', 'status', 'storage_location')
        }),
        ('Found Info', {
            'fields': ('found_date', 'found_by'),
            'classes': ('collapse',)
        }),
        ('Claimed Info', {
            'fields': ('claimed_date', 'claimed_by'),
            'classes': ('collapse',)
        }),
        ('Disposal Info', {
            'fields': ('disposal_date', 'disposal_method'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

# Recurring Schedules Admin
class GeneratedTaskInline(admin.TabularInline):
    model = GeneratedTask
    extra = 0
    readonly_fields = ('task', 'generated_at', 'generated_for_date')
    can_delete = False

class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'property_ref', 'frequency', 'is_active', 'last_generated', 'created_at')
    list_filter = ('task_type', 'frequency', 'is_active', 'property_ref')
    search_fields = ('name', 'task_title_template', 'property_ref__name')
    readonly_fields = ('created_at', 'last_generated')
    inlines = [GeneratedTaskInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'task_type', 'property_ref', 'is_active')
        }),
        ('Task Template', {
            'fields': ('task_title_template', 'task_description_template', 'default_assignee', 'checklist_template')
        }),
        ('Schedule', {
            'fields': ('frequency', 'interval', 'weekday', 'day_of_month', 'start_date', 'end_date')
        }),
        ('Timing', {
            'fields': ('time_of_day', 'advance_days')
        }),
        ('System Info', {
            'fields': ('created_at', 'last_generated'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class GeneratedTaskAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'task', 'generated_for_date', 'generated_at')
    list_filter = ('generated_for_date', 'generated_at', 'schedule__task_type')
    search_fields = ('schedule__name', 'task__title')
    readonly_fields = ('generated_at',)

# Booking Import Admin
class BookingImportLogInline(admin.TabularInline):
    model = BookingImportLog
    extra = 0
    readonly_fields = ('imported_at', 'imported_by', 'total_rows', 'successful_imports', 'errors_count')
    can_delete = False

class BookingImportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'property_ref', 'import_type', 'is_active', 'last_import', 'created_at')
    list_filter = ('import_type', 'is_active', 'property_ref')
    search_fields = ('name', 'property_ref__name')
    readonly_fields = ('created_at', 'last_import')
    inlines = [BookingImportLogInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'property_ref', 'import_type', 'is_active')
        }),
        ('CSV Field Mapping', {
            'fields': ('date_format', 'checkin_field', 'checkout_field', 'guest_name_field', 'guest_contact_field'),
            'classes': ('collapse',)
        }),
        ('Auto-Task Generation', {
            'fields': ('auto_create_tasks', 'cleaning_schedule')
        }),
        ('System Info', {
            'fields': ('created_at', 'last_import'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class BookingImportLogAdmin(admin.ModelAdmin):
    list_display = ('template', 'imported_at', 'imported_by', 'total_rows', 'successful_imports', 'errors_count')
    list_filter = ('imported_at', 'template')
    search_fields = ('template__name',)
    readonly_fields = ('imported_at',)

# Register all new models with custom admin site
admin_site.register(ChecklistTemplate, ChecklistTemplateAdmin)
admin_site.register(ChecklistResponse, ChecklistResponseAdmin)
admin_site.register(TaskChecklist, TaskChecklistAdmin)
admin_site.register(InventoryCategory, InventoryCategoryAdmin)
admin_site.register(InventoryItem, InventoryItemAdmin)
admin_site.register(PropertyInventory, PropertyInventoryAdmin)
admin_site.register(InventoryTransaction, InventoryTransactionAdmin)
admin_site.register(LostFoundItem, LostFoundItemAdmin)
admin_site.register(ScheduleTemplate, ScheduleTemplateAdmin)
admin_site.register(GeneratedTask, GeneratedTaskAdmin)
admin_site.register(BookingImportTemplate, BookingImportTemplateAdmin)
admin_site.register(BookingImportLog, BookingImportLogAdmin)

# Also register with default admin for backward compatibility
admin.site.register(ChecklistTemplate, ChecklistTemplateAdmin)
admin.site.register(ChecklistResponse, ChecklistResponseAdmin)
admin.site.register(TaskChecklist, TaskChecklistAdmin)
admin.site.register(InventoryCategory, InventoryCategoryAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(PropertyInventory, PropertyInventoryAdmin)
admin.site.register(InventoryTransaction, InventoryTransactionAdmin)
admin.site.register(LostFoundItem, LostFoundItemAdmin)
admin.site.register(ScheduleTemplate, ScheduleTemplateAdmin)
admin.site.register(GeneratedTask, GeneratedTaskAdmin)
admin.site.register(BookingImportTemplate, BookingImportTemplateAdmin)
admin.site.register(BookingImportLog, BookingImportLogAdmin)