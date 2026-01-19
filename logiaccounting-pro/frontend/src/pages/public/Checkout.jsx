import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { checkoutAPI } from '../../services/api';

export default function Checkout() {
  const { code } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedGateway, setSelectedGateway] = useState(null);

  const [cardForm, setCardForm] = useState({
    number: '',
    expiry: '',
    cvc: '',
    zip: ''
  });

  useEffect(() => {
    loadCheckoutData();
  }, [code]);

  const loadCheckoutData = async () => {
    try {
      const res = await checkoutAPI.getData(code);
      setData(res.data);
      if (res.data.available_gateways?.length > 0) {
        setSelectedGateway(res.data.available_gateways[0].id);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Payment link not found');
      } else if (err.response?.status === 410) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to load checkout');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    return parts.length ? parts.join(' ') : v;
  };

  const formatExpiry = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    if (v.length >= 2) {
      return v.substring(0, 2) + '/' + v.substring(2, 4);
    }
    return v;
  };

  const handlePay = async () => {
    setProcessing(true);
    setError(null);

    try {
      const res = await checkoutAPI.pay(code, {
        gateway: selectedGateway,
        card_number: cardForm.number.replace(/\s/g, ''),
        card_expiry: cardForm.expiry,
        card_cvc: cardForm.cvc,
        card_zip: cardForm.zip
      });

      if (res.data.success) {
        navigate(`/pay/${code}/success`, {
          state: {
            transaction_id: res.data.transaction_id,
            amount: res.data.amount_paid,
            currency: data.currency
          }
        });
      } else {
        setError(res.data.error);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Payment failed');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="checkout-page">
        <div className="checkout-container">
          <div className="text-center p-8">Loading...</div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="checkout-page">
        <div className="checkout-container">
          <div className="checkout-error">
            <div className="error-icon">❌</div>
            <h2>{error}</h2>
            <p>This payment link is no longer available.</p>
          </div>
        </div>
      </div>
    );
  }

  if (data?.already_paid) {
    return (
      <div className="checkout-page">
        <div className="checkout-container">
          <div className="checkout-success">
            <div className="success-icon">✅</div>
            <h2>Already Paid</h2>
            <p>This payment was completed on {new Date(data.paid_at).toLocaleDateString()}</p>
            <p>Amount: ${data.paid_amount?.toLocaleString()} {data.currency}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        {/* Header */}
        <div className="checkout-header">
          <h1>Complete Payment</h1>
          {data.invoice_number && <p>Invoice: {data.invoice_number}</p>}
        </div>

        {/* Amount */}
        <div className="checkout-amount">
          <div className="amount-value">
            ${data.amount.toLocaleString()}
          </div>
          <div className="amount-currency">{data.currency}</div>
          <div className="amount-description">{data.description}</div>
        </div>

        {/* Gateway Selection */}
        <div className="checkout-section">
          <h3>Payment Method</h3>
          <div className="gateway-options">
            {data.available_gateways?.map(gw => (
              <div
                key={gw.id}
                className={`gateway-option ${selectedGateway === gw.id ? 'selected' : ''}`}
                onClick={() => setSelectedGateway(gw.id)}
              >
                <div className="gateway-icon">{gw.icon}</div>
                <div className="gateway-name">{gw.name}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Card Form (for card-based gateways) */}
        {selectedGateway && ['stripe', 'mercadopago'].includes(selectedGateway) && (
          <div className="checkout-section">
            <h3>Card Details</h3>
            <div className="card-form">
              <div className="form-group">
                <label>Card Number</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="4242 4242 4242 4242"
                  value={cardForm.number}
                  onChange={(e) => setCardForm({ ...cardForm, number: formatCardNumber(e.target.value) })}
                  maxLength={19}
                />
              </div>
              <div className="card-row">
                <div className="form-group">
                  <label>Expiry</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="MM/YY"
                    value={cardForm.expiry}
                    onChange={(e) => setCardForm({ ...cardForm, expiry: formatExpiry(e.target.value) })}
                    maxLength={5}
                  />
                </div>
                <div className="form-group">
                  <label>CVC</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="123"
                    value={cardForm.cvc}
                    onChange={(e) => setCardForm({ ...cardForm, cvc: e.target.value.replace(/\D/g, '').slice(0, 4) })}
                    maxLength={4}
                  />
                </div>
                <div className="form-group">
                  <label>ZIP</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="10001"
                    value={cardForm.zip}
                    onChange={(e) => setCardForm({ ...cardForm, zip: e.target.value })}
                    maxLength={10}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PayPal Button */}
        {selectedGateway === 'paypal' && (
          <div className="checkout-section">
            <p className="text-center text-muted">
              You will be redirected to PayPal to complete your payment.
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="checkout-error-message">
            ❌ {error}
          </div>
        )}

        {/* Pay Button */}
        <button
          className="checkout-pay-btn"
          onClick={handlePay}
          disabled={processing || !selectedGateway}
        >
          {processing ? 'Processing...' : `Pay $${data.amount.toLocaleString()} ${data.currency}`}
        </button>

        {/* Security Badge */}
        <div className="checkout-security">
          🔒 Secured by {selectedGateway === 'stripe' ? 'Stripe' : selectedGateway === 'paypal' ? 'PayPal' : 'MercadoPago'}
        </div>

        {/* Test Cards Info */}
        <div className="checkout-test-info">
          <details>
            <summary>Test Card Numbers (Demo Mode)</summary>
            <ul>
              <li><code>4242 4242 4242 4242</code> - Success</li>
              <li><code>4000 0000 0000 0002</code> - Declined</li>
              <li><code>4000 0000 0000 9995</code> - Insufficient funds</li>
            </ul>
          </details>
        </div>
      </div>
    </div>
  );
}
