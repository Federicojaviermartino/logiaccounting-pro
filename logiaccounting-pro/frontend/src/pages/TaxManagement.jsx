import { useState, useEffect } from 'react';
import { taxAPI } from '../services/api';

export default function TaxManagement() {
  const [taxes, setTaxes] = useState([]);
  const [taxTypes, setTaxTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTax, setEditingTax] = useState(null);
  const [showCalculator, setShowCalculator] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [report, setReport] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    code: '',
    type: 'vat',
    rate: 0,
    applies_to: ['products', 'services'],
    is_default: false
  });

  const [calcData, setCalcData] = useState({
    amount: 0,
    tax_id: '',
    is_inclusive: false,
    result: null
  });

  const [reportPeriod, setReportPeriod] = useState({
    start: new Date().toISOString().slice(0, 7) + '-01',
    end: new Date().toISOString().slice(0, 10)
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [taxesRes, typesRes] = await Promise.all([
        taxAPI.list(false),
        taxAPI.getTypes()
      ]);
      setTaxes(taxesRes.data.taxes);
      setTaxTypes(typesRes.data.types);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      if (editingTax) {
        await taxAPI.update(editingTax.id, formData);
      } else {
        await taxAPI.create(formData);
      }
      setShowForm(false);
      setEditingTax(null);
      resetForm();
      loadInitialData();
    } catch (err) {
      alert('Failed to save tax');
    }
  };

  const handleDelete = async (taxId) => {
    if (!confirm('Delete this tax rate?')) return;
    try {
      await taxAPI.delete(taxId);
      loadInitialData();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleToggleActive = async (tax) => {
    try {
      await taxAPI.update(tax.id, { active: !tax.active });
      loadInitialData();
    } catch (err) {
      alert('Failed to toggle');
    }
  };

  const handleSetDefault = async (tax) => {
    try {
      await taxAPI.update(tax.id, { is_default: true });
      loadInitialData();
    } catch (err) {
      alert('Failed to set default');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      code: '',
      type: 'vat',
      rate: 0,
      applies_to: ['products', 'services'],
      is_default: false
    });
  };

  const handleEdit = (tax) => {
    setEditingTax(tax);
    setFormData({
      name: tax.name,
      code: tax.code,
      type: tax.type,
      rate: tax.rate,
      applies_to: tax.applies_to,
      is_default: tax.is_default
    });
    setShowForm(true);
  };

  const handleCalculate = async () => {
    try {
      const res = await taxAPI.calculate({
        amount: calcData.amount,
        tax_id: calcData.tax_id || undefined,
        is_inclusive: calcData.is_inclusive
      });
      setCalcData({ ...calcData, result: res.data });
    } catch (err) {
      alert('Calculation failed');
    }
  };

  const handleGenerateReport = async () => {
    try {
      const res = await taxAPI.getReport(reportPeriod.start, reportPeriod.end);
      setReport(res.data);
    } catch (err) {
      alert('Failed to generate report');
    }
  };

  return (
    <>
      <div className="info-banner mb-6">
        Configure tax rates and generate tax reports for compliance.
      </div>

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="page-title" style={{ margin: 0 }}>Tax Rates</h2>
        <div className="flex gap-2">
          <button className="btn btn-secondary" onClick={() => setShowCalculator(true)}>
            Tax Calculator
          </button>
          <button className="btn btn-secondary" onClick={() => setShowReport(true)}>
            Tax Report
          </button>
          <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
            + Add Tax
          </button>
        </div>
      </div>

      {/* Taxes List */}
      <div className="section">
        {loading ? (
          <div className="text-center p-8">Loading...</div>
        ) : taxes.length === 0 ? (
          <div className="text-center text-muted p-8">No tax rates configured</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Code</th>
                  <th>Type</th>
                  <th>Rate</th>
                  <th>Applies To</th>
                  <th>Default</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {taxes.map(tax => (
                  <tr key={tax.id} className={!tax.active ? 'inactive' : ''}>
                    <td className="font-bold">{tax.name}</td>
                    <td><code>{tax.code}</code></td>
                    <td>{tax.type}</td>
                    <td className="font-bold">{tax.rate}%</td>
                    <td>{tax.applies_to?.join(', ')}</td>
                    <td>
                      {tax.is_default ? (
                        <span className="badge badge-success">Default</span>
                      ) : (
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleSetDefault(tax)}
                        >
                          Set Default
                        </button>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${tax.active ? 'badge-success' : 'badge-gray'}`}>
                        {tax.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(tax)}>
                          Edit
                        </button>
                        <button
                          className={`btn btn-sm ${tax.active ? 'btn-warning' : 'btn-success'}`}
                          onClick={() => handleToggleActive(tax)}
                        >
                          {tax.active ? 'Disable' : 'Enable'}
                        </button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(tax.id)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingTax ? 'Edit Tax' : 'New Tax Rate'}</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="IVA 21%"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Code *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    placeholder="IVA21"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select
                    className="form-select"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  >
                    {taxTypes.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Rate (%)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.rate}
                    onChange={(e) => setFormData({ ...formData, rate: parseFloat(e.target.value) || 0 })}
                    step="0.1"
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  />
                  Set as default for this type
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={!formData.name || !formData.code}
              >
                {editingTax ? 'Update' : 'Create'} Tax
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Calculator Modal */}
      {showCalculator && (
        <div className="modal-overlay" onClick={() => setShowCalculator(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Tax Calculator</h3>
              <button className="modal-close" onClick={() => setShowCalculator(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Amount</label>
                <input
                  type="number"
                  className="form-input"
                  value={calcData.amount}
                  onChange={(e) => setCalcData({ ...calcData, amount: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Tax Rate</label>
                <select
                  className="form-select"
                  value={calcData.tax_id}
                  onChange={(e) => setCalcData({ ...calcData, tax_id: e.target.value })}
                >
                  <option value="">Use default</option>
                  {taxes.filter(t => t.active).map(t => (
                    <option key={t.id} value={t.id}>{t.name} ({t.rate}%)</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={calcData.is_inclusive}
                    onChange={(e) => setCalcData({ ...calcData, is_inclusive: e.target.checked })}
                  />
                  Tax is included in amount
                </label>
              </div>
              <button className="btn btn-primary" onClick={handleCalculate}>
                Calculate
              </button>

              {calcData.result && (
                <div className="result-box mt-4">
                  <div className="result-row">
                    <span>Base Amount:</span>
                    <span className="font-bold">${calcData.result.base_amount?.toLocaleString()}</span>
                  </div>
                  <div className="result-row">
                    <span>Tax ({calcData.result.tax_name} @ {calcData.result.tax_rate}%):</span>
                    <span className="font-bold">${calcData.result.tax_amount?.toLocaleString()}</span>
                  </div>
                  <div className="result-row total">
                    <span>Total:</span>
                    <span className="font-bold">${calcData.result.total?.toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReport && (
        <div className="modal-overlay" onClick={() => setShowReport(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Tax Report</h3>
              <button className="modal-close" onClick={() => setShowReport(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="flex gap-4 mb-4">
                <div className="form-group">
                  <label className="form-label">From</label>
                  <input
                    type="date"
                    className="form-input"
                    value={reportPeriod.start}
                    onChange={(e) => setReportPeriod({ ...reportPeriod, start: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">To</label>
                  <input
                    type="date"
                    className="form-input"
                    value={reportPeriod.end}
                    onChange={(e) => setReportPeriod({ ...reportPeriod, end: e.target.value })}
                  />
                </div>
                <button className="btn btn-primary" onClick={handleGenerateReport} style={{ alignSelf: 'flex-end' }}>
                  Generate
                </button>
              </div>

              {report && (
                <div className="tax-report">
                  <div className="stats-grid mb-4">
                    <div className="stat-card">
                      <div className="stat-value text-success">${report.total_collected?.toLocaleString()}</div>
                      <div className="stat-label">Tax Collected</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value text-danger">${report.total_paid?.toLocaleString()}</div>
                      <div className="stat-label">Tax Paid</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">${report.net_liability?.toLocaleString()}</div>
                      <div className="stat-label">Net Liability</div>
                    </div>
                  </div>

                  {report.collected?.length > 0 && (
                    <div className="mb-4">
                      <h4>Collected Taxes</h4>
                      <table className="data-table">
                        <thead>
                          <tr><th>Tax</th><th>Count</th><th>Amount</th></tr>
                        </thead>
                        <tbody>
                          {report.collected.map((c, i) => (
                            <tr key={i}>
                              <td>{c.tax_name}</td>
                              <td>{c.count}</td>
                              <td className="font-bold">${c.amount?.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {report.paid?.length > 0 && (
                    <div>
                      <h4>Paid Taxes</h4>
                      <table className="data-table">
                        <thead>
                          <tr><th>Tax</th><th>Count</th><th>Amount</th></tr>
                        </thead>
                        <tbody>
                          {report.paid.map((p, i) => (
                            <tr key={i}>
                              <td>{p.tax_name}</td>
                              <td>{p.count}</td>
                              <td className="font-bold">${p.amount?.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
