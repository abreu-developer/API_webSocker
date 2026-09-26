from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/payments/pix", methods=['POST'])
def create_payments_pix():
    return jsonify({"message": "the payment has been created"})

# webhook
@app.route('/payments/pix/confirmation', methods=['POST'])
def pix_confirmation():
    return jsonify({"message": "the payment has been confirmed"})


@app.route('/payments/pix/<int:payment_id>', methods=['GET'])
def payments_pix_page(payment_id):
    return "pagamento pix"


if __name__ == "__main__":
    app.run(debug=True)
