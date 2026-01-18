import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { saveAs } from 'file-saver';

/**
 * Export data to CSV file
 */
export const exportToCSV = (data, filename, headers = null) => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  const headerRow = headers || Object.keys(data[0]);
  const csvContent = [
    headerRow.join(','),
    ...data.map(row =>
      headerRow.map(key => {
        const value = row[key];
        // Handle values with commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value ?? '';
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  saveAs(blob, `${filename}.csv`);
};

/**
 * Export data to Excel file
 */
export const exportToExcel = (data, filename, sheetName = 'Sheet1') => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);

  // Auto-size columns
  const maxWidth = 50;
  const cols = Object.keys(data[0]).map(key => ({
    wch: Math.min(maxWidth, Math.max(key.length, ...data.map(row => String(row[key] || '').length)))
  }));
  worksheet['!cols'] = cols;

  XLSX.writeFile(workbook, `${filename}.xlsx`);
};

/**
 * Export data to PDF file
 */
export const exportToPDF = (data, filename, title, columns = null) => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  const doc = new jsPDF();

  // Add title
  doc.setFontSize(18);
  doc.text(title, 14, 22);

  // Add date
  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);

  // Prepare table data
  const headers = columns || Object.keys(data[0]);
  const tableData = data.map(row => headers.map(key => row[key] ?? ''));

  // Add table
  doc.autoTable({
    head: [headers.map(h => h.replace(/_/g, ' ').toUpperCase())],
    body: tableData,
    startY: 38,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [102, 126, 234] }
  });

  doc.save(`${filename}.pdf`);
};

/**
 * Format currency for export
 */
export const formatCurrencyForExport = (value) => {
  return typeof value === 'number' ? value.toFixed(2) : value;
};

/**
 * Format date for export
 */
export const formatDateForExport = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString();
};
