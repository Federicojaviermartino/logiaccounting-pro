import { useState, useEffect } from 'react';
import { currencyAPI } from '../services/api';
import toast from '../utils/toast';

export default function CurrencySettings() {
  const [currencies, setCurrencies] = useState([]);
  const [baseCurrency, setBaseCurrency] = useState('USD');
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [editingRate, setEditingRate] = useState(null);
  const [newRate, setNewRate] = useState('');

  // Converter
  const [convertAmount, setConvertAmount] = useState(100);
  const [convertFrom, setConvertFrom] = useState('USD');
  const [convertTo, setConvertTo] = useState('EUR');
  const [convertResult, setConvertResult] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [currenciesRes, ratesRes] = await Promise.all([
        currencyAPI.getAll(),
        currencyAPI.getRates()
      ]);
      setCurrencies(currenciesRes.data.currencies || []);
      setBaseCurrency(currenciesRes.data.base_currency || 'USD');
      setRates(ratesRes.data.rates || {});
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSetRate = async (code) => {
    try {
      await currencyAPI.setRate(code, parseFloat(newRate));
      setEditingRate(null);
      setNewRate('');
      loadData();
    } catch (err) {
      toast.error('Failed to update rate');
    }
  };

  const handleSetBase = async (code) => {
    try {
      await currencyAPI.setBase(code);
      setBaseCurrency(code);
      loadData();
    } catch (err) {
      toast.error('Failed to set base currency');
    }
  };

  const handleConvert = async () => {
    try {
      const res = await currencyAPI.convert(convertAmount, convertFrom, convertTo);
      setConvertResult(res.data);
    } catch (err) {
      toast.error('Conversion failed');
    }
  };

  const formatRate = (code) => {
    const rate = rates[code];
    if (!rate) return 'N/A';
    return rate < 10 ? rate.toFixed(4) : rate.toFixed(2);
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <div className="info-banner mb-6">
        Manage currencies and exchange rates for multi-currency transactions.
      </div>

      {/* Currency Converter */}
      <div className="section mb-6">
        <h3 className="section-title">Currency Converter</h3>
        <div className="converter-grid">
          <div className="form-group">
            <label className="form-label">Amount</label>
            <input
              type="number"
              className="form-input"
              value={convertAmount}
              onChange={(e) => setConvertAmount(parseFloat(e.target.value) || 0)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">From</label>
            <select
              className="form-select"
              value={convertFrom}
              onChange={(e) => setConvertFrom(e.target.value)}
            >
              {currencies.map(c => (
                <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">To</label>
            <select
              className="form-select"
              value={convertTo}
              onChange={(e) => setConvertTo(e.target.value)}
            >
              {currencies.map(c => (
                <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">&nbsp;</label>
            <button className="btn btn-primary" onClick={handleConvert}>
              Convert
            </button>
          </div>
        </div>

        {convertResult && (
          <div className="convert-result">
            <div className="convert-from">
              {currencies.find(c => c.code === convertResult.from_currency)?.symbol}
              {convertResult.original_amount?.toLocaleString()}
            </div>
            <div className="convert-arrow">-&gt;</div>
            <div className="convert-to">
              {currencies.find(c => c.code === convertResult.to_currency)?.symbol}
              {convertResult.converted_amount?.toLocaleString()}
            </div>
            <div className="convert-rate">
              Rate: {convertResult.rate?.toFixed(4)}
            </div>
          </div>
        )}
      </div>

      {/* Exchange Rates */}
      <div className="section">
        <h3 className="section-title">Exchange Rates (Base: {baseCurrency})</h3>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Currency</th>
                <th>Symbol</th>
                <th>Rate</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {currencies.map(currency => (
                <tr key={currency.code}>
                  <td>
                    <strong>{currency.code}</strong>
                    <div className="text-muted text-sm">{currency.name}</div>
                  </td>
                  <td>{currency.symbol}</td>
                  <td>
                    {editingRate === currency.code ? (
                      <div className="flex gap-2">
                        <input
                          type="number"
                          step="0.0001"
                          className="form-input"
                          style={{ width: '120px' }}
                          value={newRate}
                          onChange={(e) => setNewRate(e.target.value)}
                        />
                        <button className="btn btn-sm btn-success" onClick={() => handleSetRate(currency.code)}>
                          OK
                        </button>
                        <button className="btn btn-sm btn-secondary" onClick={() => setEditingRate(null)}>
                          X
                        </button>
                      </div>
                    ) : (
                      <span className="rate-value">{formatRate(currency.code)}</span>
                    )}
                  </td>
                  <td>
                    <div className="flex gap-2">
                      {currency.code !== baseCurrency && (
                        <>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => {
                              setEditingRate(currency.code);
                              setNewRate(rates[currency.code]?.toString() || '');
                            }}
                          >
                            Edit Rate
                          </button>
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleSetBase(currency.code)}
                          >
                            Set as Base
                          </button>
                        </>
                      )}
                      {currency.code === baseCurrency && (
                        <span className="badge badge-success">Base Currency</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
