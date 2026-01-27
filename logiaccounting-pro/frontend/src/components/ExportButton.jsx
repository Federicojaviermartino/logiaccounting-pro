import { useState } from 'react';
import { exportToCSV, exportToExcel, exportToPDF } from '../utils/exportUtils';

export default function ExportButton({
  data,
  filename,
  title = 'Report',
  columns = null
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleExport = (format) => {
    switch (format) {
      case 'csv':
        exportToCSV(data, filename, columns);
        break;
      case 'excel':
        exportToExcel(data, filename);
        break;
      case 'pdf':
        exportToPDF(data, filename, title, columns);
        break;
    }
    setIsOpen(false);
  };

  return (
    <div className="export-button-container">
      <button
        className="btn btn-secondary"
        onClick={() => setIsOpen(!isOpen)}
      >
        Export
      </button>

      {isOpen && (
        <div className="export-dropdown">
          <button onClick={() => handleExport('csv')}>
            Export CSV
          </button>
          <button onClick={() => handleExport('excel')}>
            Export Excel
          </button>
          <button onClick={() => handleExport('pdf')}>
            Export PDF
          </button>
        </div>
      )}
    </div>
  );
}
