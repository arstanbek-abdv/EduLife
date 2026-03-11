from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
import os
import uuid
from apps.users.models import CustomUser


@receiver(pre_save, sender=CustomUser)
def handle_user_profile_upload(sender, instance, **kwargs):
    """
    Handle user profile image uploads to object storage (R2).
    When profile_image is uploaded via admin, populate file_key with the storage path.
    """
    if not instance.pk:  # New object
        return
    
    try:
        old = CustomUser.objects.get(pk=instance.pk)
    except CustomUser.DoesNotExist:
        return
    
    # Check if profile_image has changed
    if old.profile_image and instance.profile_image:
        if old.profile_image != instance.profile_image:
            # New file uploaded, delete old one from MinIO
            if old.file_key:
                try:
                    default_storage.delete(old.file_key)
                except Exception:
                    pass
            
            # Generate new file_key for object storage
            ext = os.path.splitext(instance.profile_image.name)[1]
            if not ext:
                ext = '.jpg'  # fallback
            instance.file_key = f'profile_images/{uuid.uuid4().hex}{ext.lower()}'
            instance.original_file_name = instance.profile_image.name[:255]
            instance.file_mime_type = instance.profile_image.content_type or 'image/jpeg'
            
            # Save file to MinIO if not already there
            if not default_storage.exists(instance.file_key):
                instance.profile_image.seek(0)  # Reset file pointer
                default_storage.save(instance.file_key, instance.profile_image)


@receiver(post_delete, sender=CustomUser)
def delete_user_profile_from_minio(sender, instance, **kwargs):
    """Delete user profile image from object storage when user is deleted."""
    if instance.file_key:
        try:
            default_storage.delete(instance.file_key)
        except Exception:
            pass
