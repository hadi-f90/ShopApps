## Project description
project sub apps (each app can be run independently, yet uses the same databases which are accessible from within each app)

for each of the following sob apps start agile. i.e. create minimum working sample feature list, then by adding features, not only backend logic would be improved, but also, UI/UX must be changed to meet criteria.

# Sub apps description
- a simple Contact manager which can import/export from/to vcf
    - add/delete/edit and generally manage contact informations

- social media manager
    - send recieve messgages including sms, instant messengers, social media networks posts (even planning to post the in fututre)
    - manage message templates and their formats (e.g. shop ending signature foreach message )

- inventory manager
    - create/remove/modify storage warehouse
    - create invetory items i.e. goods with desired specifications by using e.g. amount, packing, purchase and sales prices, color, vendor, brand, etc.
    - create item tags to manage items specifications
    - add/remove items to inventory both initially and by submitting purchase.

- accounting reciept manager
    - making use of contact manager and invetory manager api would create cusotmer reciept
    - entering purchase events
    - calcuate sales price
    - can calculate sale price from different strategies of price calculations (discount, wholesale, retail, taxes, logestics, etc.)
    - convert between different currencies (to be easier for now consider Toman and Iranian  Rials)

## Project languages :
- right to left languages mainly Farsi
- left to right languages mainly English 2nd option

## Project technologies used:
- python,
- QT and/or pyside,
- peewee database management tools, alternatively ponyORM
- SQLite database
- C extension, cpython, cython and similar technologies if process bottle neck occurs as compensatory policy
