import webapp2
import jinja2
import os

from google.appengine.ext import ndb
from google.appengine.api import users

from userModel import UserModel


JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        url = ''
        url_string = ''
        user = users.get_current_user()
        myuser = None

        if user:
            url = users.create_logout_url(self.request.uri)
            url_string = 'logout'

            myuser_key = ndb.Key('UserModel', user.user_id())
            myuser = myuser_key.get()
            welcome = 'Long time no see'
            #if user doesnt exist add to db
            if myuser == None:
                myuser = UserModel(id = user.user_id())
                myuser.put()


        else:
            url = users.create_login_url(self.request.uri)
            url_string = 'login'
            welcome = 'Hello, to see our features please login'


        breadcrumb = ['Home']

        template_values = {
            'url' : url,
            'url_string' : url_string,
            'myuser': myuser,
            'breadcrumb': breadcrumb,
            'welcome' : welcome
        }

        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(template_values))




app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug = True)
