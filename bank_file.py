import sqlite3, os, sys, random, time, string, hashlib
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect('user_database.db')
cursor = conn.cursor()

# Create a table to store user information if it does not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        account_number INTEGER PRIMARY KEY,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        dob TEXT NOT NULL,
        address TEXT NOT NULL,
        mobile_number INTEGER(10) NOT NULL,
        balance REAL NOT NULL
    )
''')

# Create a transaction table if it does not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY,
        account_number TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        transaction_date_time TEXT NOT NULL,
        amount REAL NOT NULL,
        balance REAL NOT NULL,
        FOREIGN KEY (account_number) REFERENCES users (account_number)
    )
''')


# Function to make changes in transaction table after withdraw, deposit and money transfer 
def  insert_transaction(account_number, transaction_type, amount, destination_account=None):
    transaction_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   
    
    if transaction_type == 'deposit':

        cursor.execute('''
            SELECT balance FROM users WHERE account_number = ?
        ''', (account_number,))
        balance_result = cursor.fetchone()
        balance=balance_result[0]

        new_balance=balance+amount

        cursor.execute('''
            UPDATE users SET balance = ? WHERE account_number = ?
        ''', (new_balance, account_number))
       
        cursor.execute('''
            INSERT INTO transactions (account_number, transaction_type, transaction_date_time, amount, balance)
            VALUES (?, ?, ?, ?,?)
        ''', (account_number, 'Deposit', transaction_date_time, amount,new_balance))
        
    elif transaction_type == 'withdraw':
        cursor.execute('''
            SELECT balance FROM users WHERE account_number = ?
        ''', (account_number,))
        balance_result = cursor.fetchone()

        if balance_result is None or balance_result[0] is None:
            print("Account not found or balance information not available.")
            return
        
        balance = balance_result[0]

        if balance >= amount:
            remaining_balance = balance - amount
            cursor.execute('''
                UPDATE users SET balance = ? WHERE account_number = ?
            ''', (remaining_balance, account_number))
            
            cursor.execute('''
                INSERT INTO transactions (account_number, transaction_type, transaction_date_time, amount,balance)
                VALUES (?, ?, ?, ?,?)
            ''', (account_number, 'Withdrawal', transaction_date_time, amount,remaining_balance))
        else:
            print("Insufficient balance for withdrawal.")
   
    elif transaction_type == 'transfer':
        cursor.execute('''
            SELECT balance FROM users WHERE account_number = ?
        ''', (account_number,))
        balance_result = cursor.fetchone()
        balance=balance_result[0]
       
        cursor.execute('SELECT balance FROM users WHERE account_number = ?', (destination_account,))
        destination_balance_result = cursor.fetchone()
        
        if destination_balance_result is None or destination_balance_result[0] is None:
            print("Destination account not found or balance information not available.")
            return
        
        destination_balance = destination_balance_result[0]
        
        if balance >= amount:
            remaining_balance = balance - amount
            new_destination_balance = destination_balance + amount
            
            cursor.execute('''
                UPDATE users SET balance = ? WHERE account_number = ?
            ''', (remaining_balance, account_number))
            
            cursor.execute('''
                UPDATE users SET balance = ? WHERE account_number = ?
            ''', (new_destination_balance, destination_account))
            
            cursor.execute('''
                INSERT INTO transactions (account_number, transaction_type, transaction_date_time, amount, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_number, 'Transfer', transaction_date_time, amount, remaining_balance))
            
            cursor.execute('''
                INSERT INTO transactions (account_number, transaction_type, transaction_date_time, amount, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (destination_account, 'Transfer', transaction_date_time, amount, new_destination_balance))
        else:
            print("Insufficient balance for transfer.")
    conn.commit()


# withdraw function
def withdraw(account_number):
    try:
        amount = float(input("Enter amount you want to withdraw: "))  
    except ValueError:
        print("Invalid amount format.")
        return

    cursor.execute('SELECT balance FROM users WHERE account_number = ?', (account_number,))
    balance_result = cursor.fetchone()

    if balance_result is None:
        print("Account not found!")
        return  # Exit the function if the account is not found

    balance = balance_result[0]

    if balance is None:
        print("Balance information not available for the account.")
        return  # Exit the function if balance is not available

    if balance >= amount:
        insert_transaction(account_number, 'withdraw', amount)
        print(f"Withdrew {amount} from account {account_number}.")
    else:
        print("Insufficient balance for withdrawal.")
    transaction(account_number)

    
# money transfer function
def transfer(source_account_number):
    try:
        amount = float(input("Enter amount you want to transfer: "))  
    except ValueError:
        print("Invalid amount format.")
        return

    destination_account_number = input("Enter destination account number: ")
    
    # Check if the destination account number exists
    cursor.execute('SELECT balance FROM users WHERE account_number = ?', (source_account_number,))
    source_balance_result = cursor.fetchone()
    
    cursor.execute('SELECT balance FROM users WHERE account_number = ?', (destination_account_number,))
    destination_balance_result = cursor.fetchone()
    
    if source_balance_result is None or destination_balance_result is None:
        print("Source or destination account not found!")
        return
    
    source_balance = source_balance_result[0]
   

    if source_balance >= amount:
        insert_transaction(source_account_number, 'transfer', amount, destination_account_number)
        print(f"Transferred {amount} from account {source_account_number} to account {destination_account_number}.")
    else:
        print("Insufficient balance for transfer.")
    
    transaction(source_account_number)


# Deposit function
def deposit(account_number):
    
    amount=float(input("Enter amount you want to deposit: "))
    insert_transaction(account_number, 'deposit', amount)
    print(f"Deposited {amount} into account {account_number}.")
    transaction(account_number)


# Transaction menu---------------------------------------
def transaction(account_number):
    print("1. Withdraw\n2. Deposit\n3. Transfer \n4. Mini bank statement\n5. Back to after login\n6. Exit to home screen")
    choice=input("Enter your choice: ")

    if choice=='1':
        withdraw(account_number)
    elif choice=='2':
        deposit(account_number)
    elif choice=='3':
        transfer(account_number)
    elif choice=='4':
        bank_statement(account_number)
    elif choice=='5':
        logged_in_menu(account_number)
    elif choice=='6':
         home() 
    else:
        print("Invalid option! Select correct option.")
    

# Display mini bank statement
def bank_statement(account_number):
    cursor.execute('SELECT transaction_type, transaction_date_time, amount, balance FROM transactions WHERE account_number = ? ORDER BY transaction_date_time DESC LIMIT 5', (account_number,))
    statements = cursor.fetchall()
    print("{:<20} {:<25} {:<10} {:<10}".format("Type", "Transaction Date/Time", "Amount", "Balance"))
    print("-" * 70)
    
    for statement in statements:
        print("{:<20} {:<25} {:<10} {:<10}".format(statement[0], statement[1], statement[2], statement[3]))

    transaction(account_number)

# account details function
def account_details(account_number):
    
    cursor.execute("select name,dob,address,mobile_number,account_number from users where account_number = ?", (account_number,))
    column_names = [description[0] for description in cursor.description]
    account_details = cursor.fetchone()
    for column_name, column_value in zip(column_names, account_details):
        print(f"{column_name}: {column_value}")

    

# Hash function to securely store passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Login function-----------------------------------------
def login():
    mobile_number = input("Enter your User ID: ")
    password = input("Enter your password: ")
    cursor.execute("SELECT account_number FROM users WHERE mobile_number=?", (mobile_number,))
    account_number=cursor.fetchone()
    
    cursor.execute("SELECT password FROM users WHERE mobile_number=?", (mobile_number,))
    result = cursor.fetchone()
    
    if result is None:
        print("User not found!")
        login()
    elif result[0] == hash_password(password):
        print("Login successful")
        time.sleep(3)
        logged_in_menu(account_number[0])
    else:
        print("Invalid credentials!")
        login()

# Log_in menu ----------------------------------
def logged_in_menu(account_number):
    print("1. Transaction\n2. Account Details\n3. Back to home")
    choice=input("Enter your choice: ")
    if choice=='1':
        transaction(account_number)
    elif choice=='2':
        account_details(account_number)
    elif choice=='3':
        home()
    else:
        print("Invalid option! Please enter correct option.")
        


# Generate password function
def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation  # Allowed characters
    password = ''.join(random.choices(characters, k=length))
    return password

# User credentials function
def user_credentials(name, date_of_birth, address, mobile_number, account_number):
  try:
    print("Your login credentials:-\n")
    print("Use your mobile number as User ID.\nUser ID:", mobile_number)
    password = generate_password()
    hashed_password = hash_password(password)
    conn.execute("INSERT INTO users(account_number,password,name,dob,address,mobile_number,balance) VALUES (?,?,?,?,?,?,?)",(account_number,hashed_password, name, date_of_birth, address,mobile_number,0))
    conn.commit()
    print("Password:", password)
    print("Your account number: ",account_number)
    input("\nPress enter to back to Home screen...")
    home()
  except Exception as e:
        print("An error occurred! Try again")


# Validating Date of Birth
def validate_dob(date_string):
    date_format = "%d-%m-%Y"
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        print("Invalid date format.")
        return False

# Generate account number
def generate_unique_account_number():  
    while True:
        account_number = random.randint(10000000000, 99999999999)
        cursor.execute("SELECT account_number FROM users WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        if result is None:
            return account_number

# Create account function
def create_account():  
    name = input("Enter your name: ")
    while True:
        date_of_birth = input("Enter your dob in format dd-mm-yyyy: ")
        if validate_dob(date_of_birth):
            break

    address = input("Enter your address: ")
    mobile_number = int(input("Enter your mobile number: "))
    # Generate a unique account number
    account_number = generate_unique_account_number()
    user_credentials(name,date_of_birth,address,mobile_number,account_number)
   
    

# Home function #########################################
def home():
  try:
    print("1. Login\n2. Create account\n3. Exit")
    choice = input("Enter your choice: ")
    if choice == '1':
        login()
    elif choice == '2':
        create_account()
    elif choice == '3':
        print("Exiting...")
        sys.exit(0)
    else:
        print("Incorrect Option! Please select a correct option.")
        home()
  except Exception as e:
        print("An error occurred! Try again")


# Entry point
if __name__ == "__main__":
    home()