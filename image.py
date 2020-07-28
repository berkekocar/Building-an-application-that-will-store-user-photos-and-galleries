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

    

        new_image = ImageModel(image = image,origin = origin, in_gallery_dup = in_g_dup, all_gallery_dup= all_g_dup)

        #added image to gallery
        current_gallery.images.append(new_image)
        current_gallery.image_count += 1
        current_gallery.put()
        self.redirect('/galleries')



class DeleteImage(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/html'

        user = users.get_current_user()
        myuser_key = ndb.Key('UserModel', user.user_id())
        myuser = myuser_key.get()

        gallery_name = self.request.get('gallery_name')
        image_index = self.request.get('image_index')

        temp_key = myuser.key.id()+"_"+ gallery_name

        current_gallery_key = ndb.Key('GalleryModel', temp_key)
        current_gallery = current_gallery_key.get()
        current_image = current_gallery.images[int(image_index)]


        # functions used below if else statement to be easy to read
        def remove_current_image():
            current_gallery.image_count -= 1
            del current_gallery.images[int(image_index)]
            current_gallery.put()


        def in_gallery_clean():
            temp_list = []
            for i, images in enumerate(current_gallery.images):
                if images.origin == current_image.origin:
                    temp_list.append(i)

            #meaning only remaining 1
            if len(temp_list) == 1:
                current_gallery.images[(temp_list[0])].in_gallery_dup = False
                current_gallery.put()
            #else there is more than 1 dup not necessary to change

        def out_gallery_clean():
            temp_list= []

            for gallery in myuser.galleries:
                if gallery != gallery_name:
                    temp_key = myuser.key.id()+"_"+ gallery
                    gallery_key = ndb.Key('GalleryModel', temp_key)
                    gal = gallery_key.get()

                    for i,images in enumerate(gal.images):
                        if images.origin == current_image.origin:
                            temp_list.append(i)
                            found_in = gallery

            #this is the only dup remaning in entire gallery
            if len(temp_list) == 1:
                temp_key = myuser.key.id()+"_"+ found_in
                gallery_key = ndb.Key('GalleryModel', temp_key)
                gal = gallery_key.get()
                gal.images[(temp_list[0])].all_gallery_dup = False
                gal.put()


        #while this partician looks long incase it enters to if/elif statement process time will be faster
        #than average
        if (current_image.all_gallery_dup == False and current_image.in_gallery_dup == False):
            remove_current_image()
            return self.redirect('/galleries')

        elif current_image.all_gallery_dup == False and current_image.in_gallery_dup == True:
            remove_current_image()
            in_gallery_clean()
            return self.redirect('/galleries')

        elif current_image.all_gallery_dup == True and current_image.in_gallery_dup == False:
            remove_current_image()
            out_gallery_clean()
            return self.redirect('/galleries')

        elif current_image.all_gallery_dup == True and current_image.in_gallery_dup == True:
            remove_current_image()
            in_gallery_clean()
            out_gallery_clean()
            return self.redirect('/galleries')


        self.redirect('/')
