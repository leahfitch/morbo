from morbo import model, connection, relationships
from morbo.validators import *


connection.setup()


class Post(model.Model):
    author = relationships.One('morbo.example.User')
    created = DateTime(now=True)
    text = Text()


class User(model.Model):
    first_name = Text()
    last_name = Text()
    email = Email()
    phone = PhoneNumber(optional=True)
    posts = relationships.Many(Post)
