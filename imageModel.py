from google.appengine.ext import ndb

class ImageModel(ndb.Model):
    #Origin is hash code when image is uploaded
    #basicly contains origin of the image easy, to track dup
    origin = ndb.StringProperty()
    image = ndb.BlobKeyProperty()
    in_gallery_dup = ndb.BooleanProperty()
    all_gallery_dup = ndb.BooleanProperty()
