from peewee import Model, SqliteDatabase, CharField, TextField

db = SqliteDatabase('shopapps.db')

class BaseModel(Model):
    class Meta:
        database = db

class Contact(BaseModel):
    name = CharField(null=False)
    phone = CharField(null=True)           # Fixed phone
    mobile = CharField(null=True)          # Mobile
    email = CharField(null=True)
    organization = CharField(null=True)    # Company
    title = CharField(null=True)           # Role / Position
    address = TextField(null=True)
    contact_type = CharField(default='customer')
    tags = CharField(null=True)
    note = TextField(null=True)            # Notes
    tasks = TextField(null=True)           # Future tasks/projects