import oracledb
from flask import Flask, request, jsonify

# Flask app initialization
app = Flask(__name__)

# OracleDB connection configuration
dsn = oracledb.makedsn("localhost", 1521, service_name="XE")  # Update host, port, and service name
connection = oracledb.connect(user="system", password="root", dsn=dsn)

# Endpoint: Get all cars
@app.route('/cars', methods=['GET'])
def get_cars():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM cars")
    rows = cursor.fetchall()
    cursor.close()

    cars = [
        {
            "car_id": row[0],
            "model": row[1],
            "registration_number": row[2],
            "daily_rental_rate": row[3],
            "availability": row[4],
        }
        for row in rows
    ]
    return jsonify(cars)

# Endpoint: Add a new car
@app.route('/add-car', methods=['POST'])
def add_car():
    data = request.json
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO cars (car_id, model, registration_number, daily_rental_rate, availability)
            VALUES (seq_car_id.NEXTVAL, :1, :2, :3, 'Available')
            """,
            [data['model'], data['registration_number'], data['daily_rental_rate']],
        )
        connection.commit()
        return jsonify({"message": "Car added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()

# Endpoint: Get all customers
@app.route('/customers', methods=['GET'])
def get_customers():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM customers")
    rows = cursor.fetchall()
    cursor.close()

    customers = [
        {
            "customer_id": row[0],
            "name": row[1],
            "phone_number": row[2],
            "email": row[3],
        }
        for row in rows
    ]
    return jsonify(customers)

# Endpoint: Book a car
@app.route('/book-car', methods=['POST'])
def book_car():
    data = request.json
    cursor = connection.cursor()
    try:
        # Check car availability
        cursor.execute("SELECT availability FROM cars WHERE car_id = :1", [data['car_id']])
        availability = cursor.fetchone()
        if not availability or availability[0] != 'Available':
            return jsonify({"message": "Car not available for booking"}), 400

        # Insert booking
        cursor.execute(
            """
            INSERT INTO bookings (booking_id, customer_id, car_id, booking_date, return_date, total_cost)
            VALUES (bookings_seq.NEXTVAL, :1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), NULL)
            """,
            [data['customer_id'], data['car_id'], data['booking_date'], data['return_date']],
        )

        # Update car availability
        cursor.execute(
            "UPDATE cars SET availability = 'Booked' WHERE car_id = :1", [data['car_id']]
        )

        # Calculate rental cost and update the booking
        cursor.execute(
            """
            UPDATE bookings
            SET total_cost = (SELECT daily_rental_rate * (TO_DATE(:1, 'YYYY-MM-DD') - TO_DATE(:2, 'YYYY-MM-DD')) 
                              FROM cars WHERE car_id = :3)
            WHERE booking_id = (SELECT MAX(booking_id) FROM bookings)
            """,
            [data['return_date'], data['booking_date'], data['car_id']],
        )

        connection.commit()
        return jsonify({"message": "Car booked successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()

# Endpoint: Update car availability
@app.route('/update-car-availability', methods=['PUT'])
def update_car_availability():
    data = request.json
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE cars SET availability = :1 WHERE car_id = :2",
            [data['availability'], data['car_id']],
        )
        connection.commit()
        return jsonify({"message": "Car availability updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()

# Endpoint: Get all bookings
@app.route('/bookings', methods=['GET'])
def get_bookings():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM bookings")
    rows = cursor.fetchall()
    cursor.close()

    bookings = [
        {
            "booking_id": row[0],
            "customer_id": row[1],
            "car_id": row[2],
            "booking_date": row[3],
            "return_date": row[4],
            "total_cost": row[5],
        }
        for row in rows
    ]
    return jsonify(bookings)

if __name__ == '__main__':
    app.run(debug=True)
