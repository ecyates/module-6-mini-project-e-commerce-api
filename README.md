# Module 6 - Mini-Project - E-commerce API
Author: Elizabeth Yates

## Objective
- To build out an e-commerce application utilizing Flask-SQLAlchemy to integrate a MySQL database (ecommerce_db) and Postman as the user interface. 

## Tables
- **Customers**: With the parameters of name, email, phone, the `Customers` table captures the information from each customer of the e-commerce app.  
- **CustomerAccounts**: With a one-to-one relationship to the `Customers` table, the `CustomerAccounts` table just captures the username and password and validates that they are following specific requirements. 
- **Products**: With the parameters of name and price, the `Products` table captures the information for each product available on the e-commerce app.
- **Orders**: With a many-to-many relationship to the `Products` table and a one-to-many relationship to the `Customers` table, the `Orders` table keeps track of the date the order was placed, the customer who placed the order, and the products included on the order, as well as the quantity of said products. 

## Functionality

### Customers 

- **Create Customer**: Add a new customer to the database, capturing essential customer information, including name, email, and phone number, username, and password.
- **Read Customer**: Retrieve customer details based on their unique identifier (ID), displaying essential customer information, including name, email, phone number and username (but not password).
- **Update Customer**: Update customer details, allowing modifications to the customer's name, email, and phone number.
- **Delete Customer**: Delete a customer and their associated account from the system based on their ID.
- **Customer by Email**: Retrieve customer details based on their email, displaying name, email, phone number, and username (but not password).

### CustomerAccounts

- **Create CustomerAccount**: Create a new customer account for a provided customer, including fields for a unique username and a secure password. If the customer already has an account, it will inform the user. If the customer doesn't exist, it will inform the user. 
- **Read CustomerAccount**: Retrieve customer account details, including the associated customer's information, using the username.
- **Update CustomerAccount**: Update customer account information, including the username and password.
- **Delete CustomerAccount**: Delete a customer account, given the account id.

### Products 

- **Create Product**: Add a new product to the e-commerce database, capturing essential product details, such as the product name and price.
- **Read Product**: Retrieve product details based on the product's unique identifier (ID), displaying product name and price.
- **Search Products**: Retrieve product details based on a search function, displaying product name and price.
- **Update Product**: Update product details, allowing modifications to the product name and price.
- **Delete Product**: Delete a product from the system based on its unique ID.
- **List Products**: List all available products in the e-commerce platform. Ensure that the list provides essential product information.

### Orders 

- **Place Order**: Place new order, specifying the products they wish to purchase and providing essential order details. Each order captures the order date, the customer id, and the associated products and quantity of products.
- **Retrieve Order**: Customers can retrieve details of a specific order based on its unique identifier (ID) with a clear overview of the order, including the order date, customer details, associated products, quantity of products, and the order total.
- **Manage Order History**: Customers can access their order history by their username, listing all previous orders placed. Each order entry should provide comprehensive information, including the order date, associated products, and quantity of products.
- **Cancel Order**: Customers can cancel an order.
- **Add Product to Order**: Customers can add a quantity of a product to an order. 
- **Remove Product from Order**: Customers can remove all of a product from an order. 




*This code can be found in this repository:*
*https://github.com/ecyates/module-6-mini-project-e-commerce-api.git*