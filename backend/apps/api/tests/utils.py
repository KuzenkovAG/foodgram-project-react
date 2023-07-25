from ...recipes import models


def delete_tags():
    """Delete tags."""
    tags = models.Tag.objects.all()
    tags.delete()
