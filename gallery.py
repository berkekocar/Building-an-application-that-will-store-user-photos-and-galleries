import webapp2
import jinja2
import os

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

from google.appengine.ext.webapp import blobstore_handlers

from userModel import UserModel
from galleryModel import GalleryModel



from google.appengine.api import images

import logging


JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)


class ListGallery(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()
        f_img = []

        if len(myuser.galleries) == 0 or myuser.galleries == None:
            galleries = []
        else:
            galleries = myuser.galleries

            for gallery in galleries:
                temp_key = myuser.key.id()+'_'+ gallery
                gal_key = ndb.Key('GalleryModel',temp_key)
                gal = gal_key.get()
                if hasattr(gal,'images') and gal.images:
                    f_img.append(images.get_serving_url(gal.images[0].image, size=50, crop=True, secure_url=True))
                else:
                    f_img.append('')



        breadcrumb = ['Home','galleries']

        template_values = {
            'myuser' : myuser,
            'galleries':  galleries,
            'img': f_img,
            'galleries_len': len(galleries),
            'breadcrumb': breadcrumb
        }

        template = JINJA_ENVIRONMENT.get_template('galleryList.html')
        self.response.write(template.render(template_values))

class AddGallery(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        user_key = ndb.Key('UserModel',user.user_id())
        myuser = user_key.get()

        gallery_name = self.request.get('new_gallery')

        if not (gallery_name and gallery_name.strip()):
            return self.redirect('/')


        for gal in myuser.galleries:
            if gal == gallery_name:
                #galery already exist redirect to gallerylist
                return self.redirect('/')

        #Created gallery
        #Not: might requerie to  define image and add to model

        g_id = myuser.key.id() + "_" + gallery_name

        gallery = GalleryModel(id = g_id,gallery_name = gallery_name, image_count = 0)
        gallery.put()
        #NOT: adding only gallery name/ diffrent than galleryId
        myuser.galleries.append(gallery_name)
        myuser.put()

        #Not: change redirect to see if its working properly
        self.redirect('/galleries')


class EditGallery(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()

        gallery_name = self.request.get('gallery_name')

        is_exist = False
        for gallery in myuser.galleries:
            if gallery_name == gallery:
                is_exist = True

        if not is_exist:
            return self.redirect('/')
        breadcrumb = ['Home','galleries']

        template_values = {
            'myuser' : myuser,
            'current_name': gallery_name,
            'breadcrumb':breadcrumb
        }

        template = JINJA_ENVIRONMENT.get_template('galleryEdit.html')
        self.response.write(template.render(template_values))

    def post(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()

        #NOT: incoming name doesnt have user_key to
        #search in gallery model add user_key infront of name

        old_name = self.request.get('old_name')
        new_name = self.request.get('gallery_new_name')

        #check if input field is filled or name is same
        if not (new_name and new_name.strip()):
            return self.redirect('/')
        elif new_name == old_name:
            return self.redirect('/galleries')


        #Gallery name already in use
        for ind,gallery in enumerate(myuser.galleries):
            if new_name == gallery:
                return self.redirect('/galleries')
            elif old_name == gallery:
                index = ind

        temp_key = myuser.key.id()+"_"+old_name
        gallery_key = ndb.Key('GalleryModel', temp_key)
        gallery = gallery_key.get()


        temp_images = []
        if gallery.image_count != 0:
            temp_images = gallery.images

        #Added new gallary
        new_key = myuser.key.id()+"_"+new_name
        new_gallery = GalleryModel(id= new_key,image_count = gallery.image_count ,images = temp_images)
        new_gallery.put()

        #deleted old gallary due to key/value
        gallery.key.delete()

        #updated UserModel
        myuser.galleries[index] = new_name
        myuser.put()
        self.redirect('/galleries')


class DeleteGallery(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()

        gallery_name = self.request.get('gallery_name')

        temp_key = myuser.key.id()+"_"+gallery_name
        gallery_key = ndb.Key('GalleryModel', temp_key)
        gallery = gallery_key.get()

        logging.info(gallery)
        #contains image cannot be deleted
        if gallery.image_count != 0:
            return self.redirect('/galleries')

        #updated UserModel
        myuser.galleries.remove(gallery_name)
        myuser.put()

        #delete GaleryModel
        gallery.key.delete()

        self.redirect('/galleries')
        
