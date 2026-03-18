import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings
from django.core.files.storage import Storage


class CloudinaryMediaStorage(Storage):

    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLD_CLOUD_NAME,
            api_key=settings.CLD_API_KEY,
            api_secret=settings.CLD_API_TOKEN,
        )

    def _save(self, name, content):
        result = cloudinary.uploader.upload(content, folder='products', overwrite=True)
        return result['secure_url']

    def url(self, name):
        return name

    def exists(self, name):
        return False

    def delete(self, name):
        pass
