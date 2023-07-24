from flask import Flask, redirect, render_template, request, jsonify, url_for
from datetime import date
import pymysql
from flask_mail import Mail, Message
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.pdfgen import canvas


app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'testhomehr@gmail.com'
app.config['MAIL_PASSWORD'] = 'idgxsmljjdnfseud'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


# MySQL database configuration
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'test@123'
DB_DATABASE = 'ecom'

# Function to create a database connection
def create_connection():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE)

# Route to render the HTML form
@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

@app.route('/back')
def go_back():
    return redirect(url_for('index'))


# Route to handle form submissions
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        data = request.form


        # Get the current date
        today = date.today()

        # Connect to the database
        connection = create_connection()
        cursor = connection.cursor()

        sql = "INSERT INTO dealdata (app_name, app_details, client_name, client_address, client_property, client_cellno, app_status, created_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (data['appname'], data['appdetails'], data['clientname'], data['clientaddress'], data['clientproperty'], data['clientcellno'], False, today))


        connection.commit()

        cursor.close()
        connection.close()

        return 'Data successfully submitted to the database!'


@app.route('/getdata', methods=['GET'])
def get_data():
    # Connect to the database
    connection = create_connection()
    cursor = connection.cursor()

    # Assuming you have a table called 'dealdata'
    sql = "SELECT * FROM dealdata"
    cursor.execute(sql)

    # Fetch all rows from the result set
    rows = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()
    

    # Pass the data to the template for rendering
    return render_template('data.html', rows=rows)


def generatepdf(data):
    # Extract information from index 1 to 6
    info = data[1:7]

    # Define the styles for the PDF content
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        'Heading1', parent=styles['Heading1'], textColor=colors.darkblue)
    data_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=12)

    # Create the PDF document
    output_filename = 'application_info.pdf'
    doc = SimpleDocTemplate(output_filename, pagesize=letter)

    # Define the content for the PDF
    content = []

    # Add the top heading to the content
    top_heading = Paragraph("Lease Verification Document", heading_style)
    content.append(top_heading)

    # Format the data and add it to the content as a table
    data_table = [[Paragraph("Application Name", data_style), info[0]],
                  [Paragraph("Client Name", data_style), info[2]],
                  [Paragraph("Client Address", data_style), info[3]],
                  [Paragraph("Client Property", data_style), info[4]],
                  [Paragraph("Client Cell No", data_style), info[5]]]

    table_style = TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                              ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                              ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                              ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                              ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                              ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    data_table = Table(data_table, style=table_style)
    content.append(data_table)

    # Build the PDF document
    doc.build(content)

    # Pass the PDF filename to sendemail() function
    return output_filename


@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    id = data['id']

    # Connect to the database
    connection = create_connection()
    cursor = connection.cursor()

    # Get the current status for the selected row
    get_status_sql = "SELECT * FROM dealdata WHERE app_id = %s"
    cursor.execute(get_status_sql, (id,))
    alldata = cursor.fetchone()
    current_status = alldata[7]

    # Toggle the status (0 to 1 or 1 to 0)
    new_status = 0 if current_status == 1 else 1

    # Update the status in the 'dealdata' table
    update_status_sql = "UPDATE dealdata SET app_status = %s WHERE app_id = %s"
    cursor.execute(update_status_sql, (new_status, id))
    connection.commit()

    cursor.close()
    connection.close()

    # Generate the PDF and get the filename
    pdf_filename = generatepdf(alldata)

    # Pass the PDF filename to sendemail() function
    sendemail(pdf_filename)

    return jsonify({'new_status': 'Approved' if new_status == 1 else 'Pending'})




def sendemail(pdf_file):
    msg = Message(subject='Approved from HomeHR!',
                  sender='testhomehr@gmail.com',
                  recipients=['yumna.rehman20@gmail.com'])
    msg.body = "Hey, Your Application is approved from HomeHR"
    with app.open_resource(pdf_file) as fp:
        msg.attach(pdf_file, "application/pdf", fp.read())
    # Send the email using the email server configured in Flask-Mail
    mail.send(msg)

    return "Message sent!"


if __name__ == '__main__':
    app.run(debug=True)

