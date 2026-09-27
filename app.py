from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request, send_file
from flask_socketio import SocketIO

from db_models.payment import Payment
from payments.pix import Pix
from repository.database import db


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["SECRET_KEY"] = 'SECRET_KEY_WEBSOCKET'

db.init_app(app)

socketIO = SocketIO(app)


@app.route("/payments/pix", methods=['POST'])
def create_payments_pix():

    data = request.get_json()

    if 'value' not in data:
        return jsonify({"message": "invalid value"}), 400

    expiration_date = datetime.now() + timedelta(minutes=30)

    new_payment = Payment(
        value=data['value'],
        expiration_date=expiration_date
    )

    pix_obj = Pix()

    data_payment_pix = pix_obj.create_payment()

    new_payment.bank_payment_id = data_payment_pix["bank_payment_id"]
    new_payment.qr_code = data_payment_pix["qr_code_path"]

    db.session.add(new_payment)
    db.session.commit()

    return jsonify({
        "message": "the payment has been created",
        "payments": new_payment.to_dict()
    })


@app.route('/payments/pix/qr_code/<file_name>', methods=['GET'])
def get_image(file_name):

    return send_file(
        f"static/img/{file_name}.png",
        mimetype='image/png'
    )


@app.route('/payments/pix/confirmation', methods=['POST'])
def pix_confirmation():

    data = request.get_json()

    # validacion
    if "bank_payment_id" not in data or "value" not in data:
        return jsonify({"message": "invalid payment data"}), 400

    payment = Payment.query.filter_by(
        bank_payment_id=data.get("bank_payment_id")
    ).first()

    if not payment or payment.paid == True:
        return jsonify({"message": "payment not found"}), 404

    if data.get("value") != payment.value:
        return jsonify({"message": "invalid payment data"}), 400

    payment.paid = True
    db.session.commit()
    
    socketIO.emit(f'payment_confirmed-{payment.id}')
    return jsonify({"message": "the payment has been confirmed"})


@app.route('/payments/pix/<int:payment_id>', methods=['GET'])
def payments_pix_page(payment_id):

    payment = Payment.query.get(payment_id)
    
    if not payment:
        return render_template('404.html')

    if payment.paid == True:
        return render_template(
            'confirmed_payment.html',
            payment_id=payment.id,
            value=payment.value,
            host="http://127.0.0.1:5000"
        )

    return render_template(
        'payment.html',
        payment_id=payment.id,
        value=payment.value,
        host="http://127.0.0.1:5000",
        qr_code=payment.qr_code
    )


# webSocket
@socketIO.on('connect')
def handler_connect():
    print("client connect this server")
    
@socketIO.on('disconnect')
def handler_disconnect():
    print("client has disconnect to the server")

if __name__ == "__main__":
    socketIO.run(app, debug=True)