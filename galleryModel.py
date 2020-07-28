from google.appengine.ext import ndb
from imageModel import ImageModel

class GalleryModel(ndb.Model):
    gallery_name = ndb.StringProperty()
    image_count = ndb.IntegerProperty()
    images = ndb.StructuredProperty(ImageModel, repeated = True)
