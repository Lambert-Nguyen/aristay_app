#!/usr/bin/env python3
"""
Memory monitoring command for Heroku dynos
"""
import os
import gc
import psutil
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection


class Command(BaseCommand):
    help = 'Monitor and report memory usage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Perform memory cleanup after reporting',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.8,
            help='Memory threshold for warnings (0.0-1.0)',
        )

    def handle(self, *args, **options):
        cleanup = options['cleanup']
        threshold = options['threshold']
        
        # Get memory information
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        # Get system memory info
        system_memory = psutil.virtual_memory()
        available_mb = system_memory.available / 1024 / 1024
        
        # Get database connection info
        db_connections = len(connection.queries) if hasattr(connection, 'queries') else 0
        
        # Report memory usage
        self.stdout.write("=" * 50)
        self.stdout.write("MEMORY USAGE REPORT")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Process Memory: {memory_mb:.2f} MB ({memory_percent:.1f}%)")
        self.stdout.write(f"System Available: {available_mb:.2f} MB")
        self.stdout.write(f"Database Queries: {db_connections}")
        self.stdout.write(f"Garbage Collection: {len(gc.garbage)} objects")
        
        # Check threshold
        if memory_percent > threshold * 100:
            self.stdout.write(
                self.style.WARNING(f"⚠️  HIGH MEMORY USAGE: {memory_percent:.1f}% > {threshold*100:.1f}%")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Memory usage OK: {memory_percent:.1f}%")
            )
        
        # Perform cleanup if requested
        if cleanup:
            self.stdout.write("\n🧹 Performing memory cleanup...")
            
            # Force garbage collection
            collected = gc.collect()
            self.stdout.write(f"Garbage collected: {collected} objects")
            
            # Clear cache
            cache.clear()
            self.stdout.write("Cache cleared")
            
            # Close database connections
            connection.close()
            self.stdout.write("Database connections closed")
            
            # Report after cleanup
            memory_info_after = process.memory_info()
            memory_mb_after = memory_info_after.rss / 1024 / 1024
            memory_percent_after = process.memory_percent()
            
            self.stdout.write(f"Memory after cleanup: {memory_mb_after:.2f} MB ({memory_percent_after:.1f}%)")
            self.stdout.write(f"Memory freed: {memory_mb - memory_mb_after:.2f} MB")
            
            self.stdout.write(
                self.style.SUCCESS("✅ Memory cleanup completed")
            )
        
        self.stdout.write("=" * 50)
