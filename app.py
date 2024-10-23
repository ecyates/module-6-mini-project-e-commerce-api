from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow,validate
from marshmallow import fields, ValidationError, validate
from marshmallow.fields import Nested
from mysql.connector import IntegrityError
import re

# ---------------------------------------------------- #
# HELPER FUNCTION
# ---------------------------------------------------- #

def validate_password(password):
    if (len(password) >= 8 and 
        re.search("[a-z]", password) and
        re.search("[A-Z]", password) and
        re.search("[0-9]", password) and 
        re.search(r"[!@#\$%\^&\*\(\)_\+\-=\[\]{};':\"\\|,.<>\/?]", password)):
        return password
    else:
        raise ValueError('Password must be at least 8 characters long and contain at least one lowercase letter, at least one uppercase letter, at least one digit, and at least one special character.')

def validate_email(email):
    if re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", email):
        return email
    else:
        raise ValueError('Invalid email input.')
    
def validate_phone(phone):
    if re.search(r"\b\d{3}-\d{3}-\d{4}", phone):
        return phone
    else: 
        raise ValueError('Phone number must be ###-###-####.')

# ---------------------------------------------------- #
# INSTANTIATING THE APP
# ---------------------------------------------------- #

my_password = input("Enter password to your database: ")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/ecommerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# ---------------------------------------------------- #
# DEFINING MODELS
# ---------------------------------------------------- #

class Customer(db.Model):
    '''Customers have the parameters name, email, and phone. They have a one-to-one relationship 
    with CustomerAccounts and a one-to-many relationship to Orders.'''
    __tablename__ = "Customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    orders = db.relationship('Order', backref='customer')  
    account = db.relationship('CustomerAccount', backref='customer_account', uselist=False)  # Establishes the relationship with the account

class CustomerAccount(db.Model):
    '''CustomerAccounts take the parameters username and password (which adheres to strict rules) and 
    have a one-to-one relationship with Customers.'''
    __tablename__ = "CustomerAccounts"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("Customers.id"))

# Many-to-Many Relationship between Products and Orders
# Order_Products include the order_id, product_id, and quantity.
order_product = db.Table('Order_Product', 
    db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False) 
)

class Order(db.Model): 
    '''Orders take parameters date and customer id and have a many-to-many relationship to products.'''
    __tablename__ = "Orders"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer,db.ForeignKey("Customers.id"))
    products = db.relationship('Product', secondary=order_product, back_populates='orders')

class Product(db.Model):
    '''Products take parameters for name and price and then have a many-to-many relationship to orders.'''
    __tablename__ = "Products"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    price = db.Column(db.Float(), nullable=False)
    orders = db.relationship('Order', secondary=order_product, back_populates='products')

# ---------------------------------------------------- #
# DEFINING SCHEMAS
# ---------------------------------------------------- #

class CustomerAccountSchema(ma.SQLAlchemyAutoSchema):
    '''Usernames must be >=3 characters and passwords must be >= 8 characters and include at least one uppercase letter, 
    lowercase letter, special character, and digit.'''
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3))
    password = fields.Str(
        required=True,
        validate=validate.And(
            validate.Length(min=8),  # Length validation
            validate_password        # Custom password validation
        ))

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    '''All fields are required except account which is a nested CustomerAccountSchema.'''
    id = fields.Int(dump_only=True)
    name = fields.String(required=True)
    email = fields.String(required=True, validate=validate_email)
    phone = fields.String(required=True, validate=validate_phone)
    account = Nested(CustomerAccountSchema)

class ProductSchema(ma.Schema):
    '''All fields are required and the name must be at least one character in length and the price must be 
    greater than zero.'''
    id = fields.Int(dump_only=True)
    name = fields.String(required=True,validate=validate.Length(min=1))
    price = fields.Float(required=True,validate=validate.Range(min=0.01))

class ProductIdSchema(ma.Schema):
    '''The product id schema is for receiving just the product id and quantity when creating the Orders.'''
    id = fields.Int(required=True) 
    quantity = fields.Int(required=True, validate=validate.Range(min=1))

class OrderSchema(ma.Schema):
    '''Date and customer id are required. The customer id must be >=1 and the products is a list of nested product id schemas.'''
    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    customer_id = fields.Int(required=True, validate=validate.Range(min=1))
    products = fields.List(fields.Nested(ProductIdSchema))

# ---------------------------------------------------- #
# INSTANTIATING SCHEMAS
# ---------------------------------------------------- #

account_schema = CustomerAccountSchema()
accounts_schema = CustomerAccountSchema(many=True)
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
product_id_schema = ProductIdSchema()
products_id_schema = ProductIdSchema(many=True)

# ---------------------------------------------------- #
# INITIALIZING THE DATABASE 
# ---------------------------------------------------- #

with app.app_context(): # Providing all the settings/tools/etc. to start the app
    db.create_all() # Create all tables

# ---------------------------------------------------- #
# CUSTOMERS
# ---------------------------------------------------- #

# Get All Customers
@app.route("/customers", methods=["GET"])
def get_customers():
    customers = Customer.query.all() # Retrieve all customers
    customer_data = []
    # Iterate over the customers
    for customer in customers:
        if customer.account: # If the account exists, exclude the password
            account_data = {"username": customer.account.username}
        else: 
            account_data = {} # If it doesn't exists, create an empty dictionary
        customer_data.append({
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "account": account_data
        })
    return jsonify(customer_data)

# Add New Customer (and Account)
@app.route("/customers", methods=["POST"])
def add_customer():
    try:
        # Load the customer data
        customer_data = customer_schema.load(request.json)
        new_customer = Customer(name = customer_data["name"], email = customer_data["email"], phone = customer_data["phone"])
        # Add the customer to the session
        db.session.add(new_customer)
        db.session.commit()
        # Retrieve customer id and create a new account.
        customer_id=new_customer.id
        new_account = CustomerAccount(username=customer_data['account']['username'], password=customer_data['account']['password'], customer_id= customer_id)
        db.session.add(new_account)
        db.session.commit()
        return jsonify({"message": "New customer added successfully"}), 201 # Return success
    except ValueError as err:
        return jsonify({"error":str(err)}), 400 # Handle value errors
    except ValidationError as ve:
        return jsonify({"error":str(ve)}), 400  # Handle validation errors
    except IntegrityError:
        db.session.rollback()  # Rollback the session if there's an error
        return jsonify({"error": "Integrity error occurred."}), 400 # Handle integrity errors.

# Update a Customer
@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id):
    customer = db.session.get(Customer, id) # Retrieve customer data from customer id
    if customer is None:
        return jsonify({"error":"Customer not found"}), 404 # Handle 404 error
    try: 
        customer_data = customer_schema.load(request.json) # Validate data
    except ValueError as e: 
        return jsonify({"error": str(e)}), 400 # Handle value error
    except ValidationError as e: 
        return jsonify({"error": str(e)}), 400 # Handle validation error
    # Update customer information and commit
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({"message": "Customer updated successfully!"}), 201 # Return success

# Delete a Customer
@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    customer = db.session.get(Customer, id) # Retrieve customer from id
    if customer is None:
        return jsonify({"error":"Customer not found"}), 404 # Handle 404 error
    account = customer.account # Retrieve account from customer
    db.session.delete(account) # Delete account
    db.session.delete(customer) # Delete customer
    db.session.commit() # Commit
    return jsonify({"message": "Customer successfully removed!"}), 200 # Return success

# Get Customer by Email
@app.route("/customers/by-email", methods=["GET"])
def customer_by_email():
    email = request.args.get('email') # Retrieve email
    customer = Customer.query.filter_by(email=email).first() # Retrieve customer
    if customer:
        customer_data = []
        if customer.account: # If account exists, exclude the password
            account_data = {
                "username": customer.account.username,
            }
        else:  # If account doesn't exist, set up empty dictionary
            account_data = {}
        customer_data.append({
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "account": account_data
        })
        return jsonify(customer_data) # Retrieve customer data
    else:
        return jsonify({"error":"Customer not found"}), 404 # Handle 404 error

# ---------------------------------------------------- #
# CUSTOMER ACCOUNTS
# ---------------------------------------------------- #

# Get All Accounts
@app.route("/accounts", methods=["GET"])
def get_accounts():
    accounts = CustomerAccount.query.all() # Retrieve all accounts
    customer_data = []
    # Iterate over accounts
    for account in accounts:
        # Retrieve customer information
        customer = db.session.get(Customer, account.customer_id)
        if customer:
            customer_data.append({
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "account": {
                "username": account.username,
                "password": account.password
            }})
    # Display all customer and account information
    return jsonify(customer_data)

# Add Account to Customer
@app.route("/accounts/<int:customer_id>", methods=["POST"])
def add_account(customer_id):
    try:
        customer = db.session.get(Customer, customer_id) # Retrieve customer from customer id
        if customer.account: # If the account already exists, handle error
            return jsonify({"error":"Account already exists for customer."}), 400
        account_data = account_schema.load(request.json) # Load account information from user
        # Create new account, add and commit
        new_account = CustomerAccount(username = account_data["username"], password = account_data["password"], customer_id=customer_id)
        db.session.add(new_account)
        db.session.commit()
        return jsonify({"message": "Account added successfully"}), 201 # Return success
    except ValueError as err:
        return jsonify({"error":str(err)}), 400 # Handle value error 
    except ValidationError as ve:
        return jsonify({"error":str(ve)}), 400  # Return validation errors
    except IntegrityError:
        db.session.rollback()  # Rollback the session if there's an error
        return jsonify({"error": "Integrity error occurred."}), 400 # Handle integrity error

# Get Account by Username
@app.route("/accounts/by-username", methods=["GET"])
def account_by_username():
    username = request.args.get('username') # Retrieve username from user
    account = CustomerAccount.query.filter_by(username=username).first() # Retrieve account from username
    if account: # If account exists
        customer = db.session.get(Customer, account.customer_id) # Retrieve customer from account 
        if customer:  # If customer exists
            customer_data = []
            # Display account data
            account_data = {
                "username": customer.account.username,
                "password": customer.account.password
            }
            # Display customer data
            customer_data.append({
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "account": account_data
            })
            return jsonify(customer_data) # Display all customer data
        else:
            return jsonify({"error":"Account not found"}), 404 # Handle 404 error
    else:
        return jsonify({"error":"Account not found"}), 404 # Handle 404 error

# Update an Account
@app.route("/accounts/<int:id>", methods=["PUT"])
def update_account(id):
    account = db.session.get(CustomerAccount, id) # Retrieve account from account id
    if account is None: 
        return jsonify({"error":"Account not found"}), 404 # Handle 404 error
    try: 
        account_data = account_schema.load(request.json) # Load account data
    except ValueError as e: 
        return jsonify({"error": str(e)}), 400 # Handle value error
    except ValidationError as e: 
        return jsonify({"error": str(e)}), 400 # Handle validation error
    try: 
        # Update account data and commit
        account.username = account_data['username']
        account.password = account_data['password']
        db.session.commit()
        return jsonify({"message": "Customer updated successfully!"}), 201 # Return success
    except IntegrityError:
        db.session.rollback()  # Rollback the session if there's an error
        return jsonify({"error": "Integrity error occurred."}), 400 # Handle integrity error
    except Exception as e: 
        return jsonify({"error": str(e)})

# Delete an Account
@app.route("/accounts/<int:id>", methods=["DELETE"])
def delete_account(id):
    account = db.session.get(CustomerAccount, id) # Retrieve account from id
    if account is None:
        return jsonify({"error":"Account not found"}), 404 # Handle 404 error
    # Delete account and commit
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Account successfully removed!"}), 200 # Return success

# ---------------------------------------------------- #
# PRODUCTS
# ---------------------------------------------------- #

# Get All Products
@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all() # Retrieve all products
    products_data = []
    for product in products:
        # Display price as $X.XX
        products_data.append({"id": product.id, "name":product.name, "price":f'${product.price:.2f}'})
    return jsonify(products_data) # Return product data

# Add New Product
@app.route("/products", methods=["POST"])
def add_product():
    try: 
        product_data = product_schema.load(request.json) # Load product information
    except ValidationError as e: 
        return jsonify({"error": str(e)}), 400 # Handle validation error
    # Create, add and commit new product
    new_product = Product(name = product_data["name"], price = product_data["price"])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "New product added successfully!"}), 201 # Return success

# Update a Product
@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    product = db.session.get(Product, id) # Retrieve product from id
    if product is None:
        return jsonify({"error":"Product not found"}), 404 # Handle 404 error
    try: 
        product_data = product_schema.load(request.json) # Load product
    except ValueError as e: 
        return jsonify({"error": str(e)}), 400 # Handle validation error
    except ValidationError as e: 
        return jsonify({"error": str(e)}), 400 # Handle validation error
    # Update product details and commit
    product.name = product_data['name']
    product.price = product_data['price']
    db.session.commit()
    return jsonify({"message": "Product updated successfully!"}), 200 # Return success

# Delete a Product
@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.get(Product, id) # Retrieve product from id
    if product is None:
        return jsonify({"error":"Product not found"}), 404 # Handle 404 error
    # Delete product and commit
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product successfully removed!"}), 200 # Return success

# Get Product by Name
@app.route("/products/by-name", methods=["GET"])
def product_by_name():
    name = request.args.get('name') # Retrieve name from user
    search_query = f"%{name}%"
    products = Product.query.filter(Product.name.ilike(search_query)).all() # Find products with name LIKE provided
    if products is None:
        return jsonify({"error":"Product not found"}), 404 # Handle 404 error
    else:
        products_data = []
        for product in products:
            # Display with the price format: $X.XX
            products_data.append({"id": product.id, "name":product.name, "price":f'${product.price:.2f}'})
        return jsonify(products_data)

# ---------------------------------------------------- #
# ORDERS
# ---------------------------------------------------- #

# Get All Orders
@app.route("/orders", methods=["GET"])
def get_orders():
    orders = Order.query.all() # Retrieve all orders
    orders_data = []
    # Iterate over each order
    for order in orders:
        products_data = []
        # Query the products for this order along with their quantity
        order_products = db.session.query(Product, order_product.c.quantity).join(order_product).filter(order_product.c.order_id == order.id).all()
        # Keep track of the price total
        order_total = 0
        # Append product details along with the quantity
        for product, quantity in order_products:
            order_total = order_total+(product.price * quantity)
            products_data.append({
                "product_id":product.id,
                "product_name": product.name,
                "price": f"${product.price:.2f}", # $X.XX
                "quantity": quantity
            })
        # Fetch the customer associated with the order
        customer = db.session.get(Customer, order.customer_id)
        # Add together all order details
        orders_data.append({
            "id": order.id,
            "date": order.date,
            "customer_name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "products": products_data,
            "order_total":f"${order_total:.2f}"
        })
    return jsonify(orders_data)

# Add New Order
@app.route("/orders", methods=["POST"])
def add_order():
    try:
        order_data = order_schema.load(request.json) # Load order data
        products = []
        # Iterate through products and append them with quantity
        for product_item in order_data["products"]:
            product = db.session.get(Product, product_item["id"]) # Get the product from the id
            if product is None:
                return jsonify({"error": "One or more products not found."}), 404 # Handle 404 error
            # Append the product and quantity to the list
            products.append({
                "product": product,
                "quantity": product_item["quantity"]
            })
        customer = db.session.get(Customer, order_data["customer_id"])
        if customer is None:
            return jsonify({"error":"Customer not found."}), 404 # Handle 404 error
        # Create a new order with date and customer id
        new_order = Order(date=order_data["date"], customer_id=order_data["customer_id"])
        db.session.add(new_order)
        db.session.commit()
        # Add products to order_product association table
        for item in products:
            db.session.execute(order_product.insert().values(
                order_id=new_order.id,
                product_id=item["product"].id,
                quantity=item["quantity"]
            ))
        db.session.commit()
        return jsonify({"message": "New order added successfully"}), 201 # Return success
    except ValidationError as ve:
        return jsonify({"error": ve.messages}), 400  # Handle validation errors
    except IntegrityError:
        db.session.rollback()  # Rollback in case of integrity issues
        return jsonify({"error": "Integrity error occurred."}), 400 # Handle integrity errors
    except Exception as e:
        return jsonify({"error": str(e)}), 400 # Handle additional errors

# Add Product to an Order
@app.route("/orders/<int:order_id>/add-product", methods=["PUT"])
def add_product_to_order(order_id):
    product_id = request.args.get('product_id', type=int) # Retrieve product id from user
    quantity = request.args.get('quantity', type=int) # Retrieve quantity from user

    if product_id is None or quantity is None:
        return jsonify({"error": "Missing product_id or quantity"}), 400 # Validate input
    # Fetch the product
    product = db.session.get(Product, product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404 # Handle 404 error
    # Fetch the order
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify({"error": "Order not found."}), 404 # Handle 404 error
    # Check if the product already exists in the order
    order_product_entry = db.session.query(order_product).filter_by(order_id=order_id, product_id=product_id).first()
    if order_product_entry:
        # If it exists, update the quantity
        new_quantity = order_product_entry.quantity + quantity
        db.session.execute(order_product.update().where(
            (order_product.c.order_id == order_id) & 
            (order_product.c.product_id == product_id)
        ).values(quantity=new_quantity))
    else:
        # If it doesn't exist, create a new entry
        new_order_product = order_product.insert().values(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.execute(new_order_product)
    db.session.commit()
    return jsonify({"message": "Product successfully added to order!"}), 200 # Return success

# Add Product to an Order
@app.route("/orders/<int:order_id>/remove-product", methods=["DELETE"])
def remove_product_from_order(order_id):
    product_id = request.args.get('product_id', type=int)  # Retrieve product id from user
    # Validate input
    if product_id is None:
        return jsonify({"error": "Missing product_id."}), 400
    # Fetch the order
    order = db.session.get(Order, order_id)
    if order is None:
        return jsonify({"error": "Order not found."}), 404 # Handle 404 error
    found = False
    # Iterate over products in order, if found, remove and commit
    for product in order.products:
        if product.id ==product_id:
            order.products.remove(product)
            db.session.commit()
            found = True
    if found:
        return jsonify({"message": "Product successfully removed from order!"}), 200 # Return success
    else: 
        return jsonify({"error": "Product not found in order."}), 404 # Handle 404 error

# Delete an Order
@app.route("/orders/<int:id>", methods=["DELETE"])
def delete_order(id):
    order = db.session.get(Order, id) # Retrieve order from id
    if order is None:  
        return jsonify({"error": "Order not found"}), 404 # Handle 404 error
    # Remove order_products from the association table.
    for product in order.products:
        order.products.remove(product)
    db.session.delete(order)  # Delete the order
    db.session.commit()  # Commit the changes to the database
    return jsonify({"message": "Order successfully removed!"}), 200 # Return success

# Get Orders By Customer Username
@app.route("/orders/by-customer", methods=["GET"])
def get_orders_by_customer():
    username = request.args.get('username', type=str) # Retrieve username from user
    account = CustomerAccount.query.filter_by(username=username).first() # Retrieve account from username
    if account is None:
        return jsonify({"error": "Customer not found."}), 404 # Handle 404 error
    customer = Customer.query.filter_by(account=account).first() # Retrieve customer from account
    if customer is None:
        return jsonify({"error": "Customer not found."}), 404 # Handle 404 error
    orders = Order.query.filter_by(customer_id=customer.id) # Retrieve orders from customer id
    if orders is None:
        return jsonify({"message": "Customer has no orders."}), 200 
    orders_data = []
    for order in orders:
        products_data = []
        # Query the products for this order along with their quantity
        order_products = db.session.query(Product, order_product.c.quantity).join(order_product).filter(order_product.c.order_id == order.id).all()
        # Append product details along with the quantity
        for product, quantity in order_products:
            products_data.append({
                "product_id":product.id,
                "product_name": product.name,
                "price": f"${product.price:.2f}",
                "quantity": quantity
            })
        # Add order details to the response
        orders_data.append({
            "order_id": order.id,
            "date": order.date,
            "customer_name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "products": products_data
        })
    return jsonify(orders_data) # Display all orders with their details

if __name__ == "__main__":
    app.run(debug=True)