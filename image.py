import webapp2
import jinja2
import os

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.api import images

from google.appengine.ext.webapp import blobstore_handlers

from userModel import UserModel
from imageModel import ImageModel

import logging

JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)


class ListImage(webapp2.RequestHandler):
    def get(self,param):

        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()

        is_exist = False
        for i in myuser.galleries:
            if i == param:
                is_exist = True
                break
        if not is_exist:
            return self.redirect('/galleries')

        temp_key = myuser.key.id()+'_'+param
        gallery_key = ndb.Key('GalleryModel', temp_key)
        imageList = gallery_key.get().images
        gallery_size = len(imageList)

        #descrypting images
        just_img_list = []
        for img in imageList:
            just_img_list.append(images.get_serving_url( img.image, size=50, crop=True, secure_url=True))

        breadcrumb = ['Home','galleries']

        template_values = {
            'myuser' : myuser,
            'image_info' : imageList,
            'images': just_img_list,
            'gallery_name': param,
            'gallery_size': gallery_size,
            'breadcrumb':breadcrumb,
            'upload_url': blobstore.create_upload_url('/image/add')
        }

        template = JINJA_ENVIRONMENT.get_template('imageList.html')
        self.response.write(template.render(template_values))



class AddImage(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()

        current_gallery_name = self.request.get('gallery_name')

        temp_key = myuser.key.id()+'_'+current_gallery_name
        gallery_key = ndb.Key('GalleryModel', temp_key)
        current_gallery = gallery_key.get()

        image = None
        typeList = ["jpg","png","jpeg"]
        origin = None
        if self.get_uploads():
            upload = self.get_uploads()[0]
            blobinfo = blobstore.BlobInfo(upload.key())
            filetype = blobinfo.content_type
            filetype = filetype.split('/')

            origin = blobinfo.md5_hash

            if filetype[1] in typeList:
                image = upload.key()
            #image is not jpg or png
            else:
                return self.redirect('/')
        else:
            return self.redirect('/')

        ###
        in_g_dup = False
        all_g_dup = False
        #Marking existing images as dup
        for galleries in myuser.galleries:

            temp_key = myuser.key.id()+'_'+galleries
            gallery_key = ndb.Key('GalleryModel', temp_key)
            gallery = gallery_key.get()

            in_marker = []
            out_marker= []

            #looping images of opend gallery
            #after marking all images
            for i,images in enumerate(gallery.images):
                if images.origin == origin:
                    if current_gallery_name == gallery.gallery_name:
                        in_marker.append(i)
                        in_g_dup = True
                    else:
                        logging.info("i marked it fucker")
                        out_marker.append(i)
                        all_g_dup = True

            #so here we are
            #cant update while looping in entity
            logging.info(in_marker)
            logging.info(out_marker)
            for mark in in_marker:
                gallery.images[mark].in_gallery_dup = True

            for mark in out_marker:
                gallery.images[mark].all_gallery_dup = True


            #made changes in gallery in one go
            gallery.put()
                     
        new_image = ImageModel(image = image,origin = origin, in_gallery_dup = in_g_dup, all_gallery_dup= all_g_dup)

        #added image to gallery
        current_gallery.images.append(new_image)
        current_gallery.image_count += 1
        current_gallery.put()
        self.redirect('/galleries')
