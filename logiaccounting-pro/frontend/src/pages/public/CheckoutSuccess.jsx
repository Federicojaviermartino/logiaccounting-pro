import { useLocation, useParams } from 'react-router-dom';

export default function CheckoutSuccess() {
  const { code } = useParams();
  const location = useLocation();
  const { transaction_id, amount, currency } = location.state || {};

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        <div className="checkout-success">
          <div className="success-icon">✅</div>
          <h1>Payment Successful!</h1>

          <div className="success-details">
            <div className="detail-row">
              <span>Amount Paid:</span>
              <strong>${amount?.toLocaleString()} {currency}</strong>
            </div>
            <div className="detail-row">
              <span>Transaction ID:</span>
              <code>{transaction_id}</code>
            </div>
            <div className="detail-row">
              <span>Date:</span>
              <span>{new Date().toLocaleDateString()}</span>
            </div>
          </div>

          <p className="success-message">
            A receipt has been sent to your email address.
          </p>

          <button className="btn btn-primary" onClick={() => window.print()}>
            🖨️ Print Receipt
          </button>
        </div>
      </div>
    </div>
  );
}
