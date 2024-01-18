from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime, date


app = Flask(__name__)
app.secret_key = 'your_secret_key'  
# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Negligence@13',
    'database': 'Sample',
}

# Establish MySQL connection
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create a table for users if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    batch VARCHAR(10) NOT NULL,
    department VARCHAR(50) NOT NULL,
    cgpa FLOAT,
    dob DATE,
    user_type VARCHAR(20) NOT NULL
);
"""
cursor.execute(create_table_query)
conn.commit()

# Create a table for additional details if it doesn't exist
create_additional_details_table_query = """
CREATE TABLE IF NOT EXISTS additional_details (
    user_id INT PRIMARY KEY,
    job VARCHAR(255),
    higher_education VARCHAR(255),
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""
cursor.execute(create_additional_details_table_query)
conn.commit()

print("Tables created successfully!")

# Utility function to calculate age based on date of birth
def calculate_age(dob):
    today = date.today()
    birth_date = datetime.strptime(str(dob), "%Y-%m-%d").date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

@app.route('/')
def index():
    return render_template('Register.html')

@app.route('/register', methods=['POST'])
def register():
    # Extract data from the registration form
    name = request.form.get('name')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('Password')  # Note the capital 'P' in 'Password'
    batch = request.form.get('Batch')
    department = request.form.get('Department')
    cgpa = request.form.get('cgpa')
    dob = request.form.get('dob')
    user_type = request.form.get('UserType')

    # Insert data into the MySQL database
    insert_query = """
    INSERT INTO users (name, email, username, password, batch, department, cgpa, dob, user_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    user_data = (name, email, username, password, batch, department, cgpa, dob, user_type)
    cursor.execute(insert_query, user_data)
    conn.commit()

    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve data from the login form
        username = request.form.get('username')
        password = request.form.get('Password')

        # Check the database for the entered credentials
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            # Successful login
            # You can store user information in the session for future use
            session['user_id'] = user[0]
            session['username'] = user[3]  # Assuming the username is in the fourth column

            # Redirect to the home page or another protected page
            return redirect(url_for('home'))
        else:
            # Incorrect username or password
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@app.route('/home')
def home():
    # Access user information from the session
    user_id = session.get('user_id')
    username = session.get('username')

    # Your home page logic goes here
    return render_template('home.html', username=username)

@app.route('/view_profile', methods=['GET', 'POST'])
def view_profile():
    if request.method == 'POST':
        user_id = session.get('user_id')  # Assuming you have a user_id in the session
        job = request.form.get('job')
        higher_education = request.form.get('higher-education')
        description = request.form.get('description')

        # Update query for the additional_details table
        update_query_additional_details = """
        INSERT INTO additional_details (user_id, job, higher_education, description)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE job = VALUES(job), higher_education = VALUES(higher_education), description = VALUES(description)
        """

        additional_details_data = (user_id, job, higher_education, description)

        cursor.execute(update_query_additional_details, additional_details_data)
        conn.commit()

        flash('Profile updated successfully', 'success')

        # Redirect to the profile page or another page after updating
        return redirect(url_for('view_profile'))

    # Fetch user data for the current logged-in user
    user_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # Fetch additional details for the current user from the additional_details table
    cursor.execute("SELECT * FROM additional_details WHERE user_id = %s", (user_id,))
    additional_details = cursor.fetchone()

    # If additional details exist, update the user object
    if additional_details:
        # Exclude the user_id from additional_details
        user += additional_details[1:] if additional_details[1:] else (None, None, None)

    print("User Data:", user)

    return render_template('viewprofile.html', user=user)


@app.route('/alumni_meets')
def alumni_meets():
    return render_template('Alumnimeet.html')


@app.route('/chat/<email>')
def chat(email):
    # You can use the 'email' parameter to fetch data for the specific user
    # and pass it to the template if needed.
    return render_template('Chat.html', email=email)

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/chatpage')
def chatpage():
    return render_template('Chatpage.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        department = request.form.get('department')
        batch = request.form.get('batch')
        name = request.form.get('name')
        cgpa_range = request.form.get('cgpa_range')
        age_group = request.form.get('age_group')

        # Process CGPA Range
        min_cgpa, max_cgpa = map(float, cgpa_range.split('-')) if cgpa_range else (None, None)

        # Process Age Group
        min_age, max_age = map(int, age_group.split('-')) if age_group else (None, None)

        # Build the query dynamically based on selected filters
        query = "SELECT * FROM users WHERE 1=1"
        values = []

        if department != 'all':
            query += " AND department = %s"
            values.append(department)

        if batch != 'all':
            query += " AND batch = %s"
            values.append(batch)

        if name:
            query += " AND name LIKE %s"
            values.append(f"%{name}%")

        if min_cgpa is not None:
            query += " AND cgpa >= %s"
            values.append(min_cgpa)

        if max_cgpa is not None:
            query += " AND cgpa <= %s"
            values.append(max_cgpa)

        if min_age is not None:
            query += " AND TIMESTAMPDIFF(YEAR, dob, CURDATE()) >= %s"
            values.append(min_age)

        if max_age is not None:
            query += " AND TIMESTAMPDIFF(YEAR, dob, CURDATE()) <= %s"
            values.append(max_age)

        cursor.execute(query, values)
        users = cursor.fetchall()

        # Calculate age and add it to the user data
        users_with_age = [(user + (calculate_age(user[8]),)) for user in users]

        # Fetch department, city, job, and batch options from the database
        cursor.execute("SELECT DISTINCT department FROM users")
        departments = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT batch FROM users")
        batches = [row[0] for row in cursor.fetchall()]

        return render_template('Search.html', departments=departments, batches=batches, users=users_with_age)

    # Fetch department, city, job, and batch options from the database
    cursor.execute("SELECT DISTINCT department FROM users")
    departments = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT batch FROM users")
    batches = [row[0] for row in cursor.fetchall()]

    return render_template('Search.html', departments=departments, batches=batches)

@app.route('/RSVP')
def RSVP():
    return render_template('RSVP.html')

@app.route('/journalpage')
def journalpage():
    return render_template('journalpage.html')

@app.route('/logout')
def logout():
    # Clear session data and redirect to the login page
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
