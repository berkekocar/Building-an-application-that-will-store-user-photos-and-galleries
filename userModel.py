from google.appengine.ext import ndb


class UserModel(ndb.Model):
    user_email = ndb.StringProperty()
    galleries = ndb.StringProperty(repeated = True)

    
