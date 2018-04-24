import webapp2
import jinja2
import os
import hashlib
import hmac
import string
import random

from google.appengine.ext import db

user=""
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class Blog(db.Model):
	title = db.StringProperty(required = True)
	body = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
    name = db.StringProperty(required=True)
    username = db.EmailProperty(required=True)
    password = db.StringProperty(required=True)
    phone = db.StringProperty(required=True)

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    @classmethod
    def by_name(cls, name):
        return User.all().filter('name = ', name).get()

    @classmethod
    def by_username(cls, username):
        return User.all().filter('username = ',username).get()

    @classmethod
    def register(cls,name,username,password,phone):
        if User.by_username(username):
            return False
        else:
            return User(
            			name=name,
            			username=username,
            			password=password,
            			phone=phone
                        )



class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(BlogHandler):

	def get(self):
		blogs = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")
		self.render("blogs.html",blogs=blogs,signedin=False)
	
	

    	
class NewPost(BlogHandler):
	def get(self):
		self.render("newPost.html")

	def post(self):
		title = self.request.get("title")
		body = self.request.get("body")

		if title and body:
			blog = Blog(title=title, body=body)
			blog.put()

			blogs = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")
			# self.render("blogs.html",blogs=blogs)
			self.render("blogs.html",signedin=True,blogs=blogs)
		else:
			error = "Both title and body are required to post a blog!"
			self.render("newPost.html",error=error,title=title,body=body)

class Login(BlogHandler):
    def get(self):
        self.render("login.html", error=None, signedin=False)

    def post(self):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        if username and password:
            user = User.by_username(username)
            if user:
				if user.password==password:
					blogs = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")
					self.render("blogs.html",signedin=True,blogs=blogs)
					return
				else:
					error = "Invalid user/password"
            else:
                error = "No user found by that name"
        else:
            error = "Missing username/password"

        self.render("login.html", error=error, signedin=False,
                    username=username)
        return

# Handles /logout
class Logout(BlogHandler):
    def get(self):     
        self.render("login.html",signedin=False)

# Handles /signup
class Signup(BlogHandler):
    def get(self):
        self.render("signup.html", error=None, signedin=False)

    def post(self):
        error = None
        username = self.request.get('username')
        password = self.request.get('password')
        phone = self.request.get('phone')
        name = self.request.get('name')


        if username and password and phone and name:
            u = User.register(name,username,password,phone)
            if u is False:
                error = "That username already exists. Please choose another."
            else:
                u.put()
                
                self.render("login.html",signedin=False)
                return
        else:
            error = "Missing required field"

        self.render("signup.html", error=error, signedin=False,
                    username=username, name=name, phone=phone)
        return


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newpost', NewPost),
    ('/signup',Signup),
    ('/login',Login),
    ('/logout',Logout) 
], debug=True)

