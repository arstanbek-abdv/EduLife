from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid
from apps.courses.models import Course, Task


@receiver(pre_save, sender=Course)
def handle_course_cover_upload(sender, instance, **kwargs):
    """
    Handle course cover image uploads to object storage (R2).
    When cover_image is uploaded via admin or API, populate file_key with the storage path.
    """
    if not instance.pk:  # New object
        return
    
    try:
        old = Course.objects.get(pk=instance.pk)
    except Course.DoesNotExist:
        return
    
    # Check if cover_image has changed
    if old.cover_image and instance.cover_image:
        if old.cover_image != instance.cover_image:
            # New file uploaded, delete old one from MinIO
            if old.file_key:
                try:
                    default_storage.delete(old.file_key)
                except Exception:
                    pass
            
            # Generate new file_key for object storage
            ext = os.path.splitext(instance.cover_image.name)[1]
            instance.file_key = f'course_covers/{instance.id}/{uuid.uuid4().hex}{ext}'
            instance.original_file_name = instance.cover_image.name
            instance.file_mime_type = instance.cover_image.content_type or 'image/jpeg'
            
            # Save file to MinIO if not already there
            if not default_storage.exists(instance.file_key):
                instance.cover_image.seek(0)  # Reset file pointer
                default_storage.save(instance.file_key, instance.cover_image)


@receiver(pre_save, sender=Task)
def handle_task_file_upload(sender, instance, **kwargs):
    """
    Handle task file uploads to object storage (R2).
    When file_content is uploaded via admin, populate file_key with the storage path.
    """
    if not instance.pk:  # New object
        return
    
    try:
        old = Task.objects.get(pk=instance.pk)
    except Task.DoesNotExist:
        return
    
    # Check if file_content has changed
    if old.file_content and instance.file_content:
        if old.file_content != instance.file_content:
            # New file uploaded, delete old one from MinIO
            if old.file_key:
                try:
                    default_storage.delete(old.file_key)
                except Exception:
                    pass
            
            # Generate new file_key for object storage
            ext = os.path.splitext(instance.file_content.name)[1]
            instance.file_key = f'tasks/{instance.id}/{uuid.uuid4().hex}{ext}'
            instance.original_file_name = instance.file_content.name
            instance.file_mime_type = instance.file_content.content_type or 'application/octet-stream'
            instance.file_size = instance.file_content.size
            
            # Save file to MinIO if not already there
            if not default_storage.exists(instance.file_key):
                instance.file_content.seek(0)  # Reset file pointer
                default_storage.save(instance.file_key, instance.file_content)


@receiver(post_delete, sender=Course)
def delete_course_cover_from_minio(sender, instance, **kwargs):
    """Delete course cover from object storage when course is deleted."""
    if instance.file_key:
        try:
            default_storage.delete(instance.file_key)
        except Exception:
            pass


@receiver(post_delete, sender=Task)
def delete_task_file_from_minio(sender, instance, **kwargs):
    """Delete task file from object storage when task is deleted."""
    if instance.file_key:
        try:
            default_storage.delete(instance.file_key)
        except Exception:
            pass
