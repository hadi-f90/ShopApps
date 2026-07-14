from peewee import Model, SqliteDatabase, CharField, IntegerField, TextField

db = SqliteDatabase('shopapps.db')

class BaseModel(Model):
    class Meta:
        database = db

class Contact(BaseModel):
    name = CharField(null=False)  # Required
    phone = CharField(null=True)
    email = CharField(null=True)
    address = TextField(null=True)
    contact_type = CharField(
        default='customer', choices=[('customer', 'Customer'), ('vendor', 'Vendor')]
    )
    tags = CharField(null=True)
    notes = TextField(null=True)