# Billing System

This is a simple billing system built with Flask, designed for Vijaya Lakshmi Enterprises.

## Features

- User authentication
- Product management (add, edit, delete products)
- Bill creation with dynamic calculations
- GST (CGST and SGST) calculations
- Printable bill generation

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install flask flask-sqlalchemy flask-login
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Access the application in your web browser at `http://127.0.0.1:5000`

## Usage

- Login with the default admin credentials (username: admin, password: admin123)
- Add products in the admin panel
- Create bills by selecting products and quantities
- Generate and print bills

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)