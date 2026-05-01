import { useState, useRef } from 'react';
import axios from 'axios';
import Papa from 'papaparse';

const REQUIRED_FIELDS = [
  { key: 'name', label: 'Product Name', suggestions: ['name', 'product', 'title', 'item'] },
  { key: 'category', label: 'Category', suggestions: ['category', 'department', 'type', 'group'] },
  { key: 'stock', label: 'Stock / Qty', suggestions: ['stock', 'qty', 'quantity', 'count', 'inventory'] },
  { key: 'price', label: 'Price', suggestions: ['price', 'cost', 'mrp', 'rate'] },
];

const OPTIONAL_FIELDS = [
  { key: 'supplier', label: 'Supplier (Optional)', suggestions: ['supplier', 'vendor', 'brand', 'manufacturer'] }
];

export default function CsvUploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [parsedData, setParsedData] = useState([]);
  const [mapping, setMapping] = useState({});
  const [mode, setMode] = useState('append'); // 'append' or 'replace'
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Select File, 2: Map Fields
  
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const resetState = () => {
    setFile(null);
    setCsvHeaders([]);
    setParsedData([]);
    setMapping({});
    setMode('append');
    setConfirmReplace(false);
    setError(null);
    setStep(1);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const autoMapHeaders = (headers) => {
    const newMapping = {};
    const allFields = [...REQUIRED_FIELDS, ...OPTIONAL_FIELDS];
    
    allFields.forEach(field => {
      // Find a matching header
      const match = headers.find(h => {
        const lowerH = h.toLowerCase();
        return field.suggestions.some(s => lowerH.includes(s));
      });
      if (match) {
        newMapping[field.key] = match;
      } else {
        newMapping[field.key] = ''; // Not mapped
      }
    });
    setMapping(newMapping);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    if (selectedFile.type !== 'text/csv' && !selectedFile.name.endsWith('.csv')) {
      setError('Please upload a valid CSV file.');
      return;
    }
    
    setFile(selectedFile);
    setError(null);
    
    Papa.parse(selectedFile, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length && !results.data.length) {
          setError('Failed to parse CSV file.');
          return;
        }
        
        const headers = results.meta.fields || [];
        if (headers.length === 0) {
          setError('No headers found in the CSV file.');
          return;
        }
        
        setCsvHeaders(headers);
        setParsedData(results.data);
        autoMapHeaders(headers);
        setStep(2);
      },
      error: (err) => {
        setError(err.message);
      }
    });
  };

  const handleMappingChange = (fieldKey, headerName) => {
    setMapping(prev => ({ ...prev, [fieldKey]: headerName }));
  };

  const handleUpload = async () => {
    // Validate required fields
    for (const field of REQUIRED_FIELDS) {
      if (!mapping[field.key]) {
        setError(`Please map the required field: ${field.label}`);
        return;
      }
    }

    if (mode === 'replace' && !confirmReplace) {
      setError('Please confirm that you want to replace the existing inventory.');
      return;
    }

    setIsUploading(true);
    setError(null);

    // Transform data according to mapping
    const products = parsedData.map(row => {
      return {
        name: row[mapping['name']] || '',
        category: row[mapping['category']] || 'Uncategorized',
        stock: parseInt(row[mapping['stock']] || 0, 10),
        price: parseFloat(row[mapping['price']] || 0.0),
        supplier: mapping['supplier'] ? (row[mapping['supplier']] || 'Unknown') : 'Unknown'
      };
    }).filter(p => p.name.trim() !== '');

    try {
      const response = await axios.post('/ingest', {
        mode,
        products
      });
      
      onUploadSuccess(response.data.inserted);
      handleClose();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Upload failed.';
      setError(msg);
      setIsUploading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{step === 1 ? 'Upload Inventory Data' : 'Map Columns'}</h2>
          <button className="close-btn" onClick={handleClose}>&times;</button>
        </div>
        
        <div className="modal-body">
          {error && <div className="error-message">{error}</div>}
          
          {step === 1 && (
            <div className="upload-step">
              <p>Select a CSV file containing your inventory products.</p>
              <div className="file-drop-area" onClick={() => fileInputRef.current?.click()}>
                <span className="upload-icon">📁</span>
                <span className="upload-text">Click to Browse or Drag & Drop</span>
                <span className="upload-hint">Only .csv files are supported</span>
              </div>
              <input 
                type="file" 
                ref={fileInputRef} 
                accept=".csv" 
                onChange={handleFileChange} 
                style={{ display: 'none' }} 
              />
            </div>
          )}

          {step === 2 && (
            <div className="mapping-step">
              <p>We found <strong>{parsedData.length}</strong> rows. Please map your CSV columns to the system fields.</p>
              
              <div className="mapping-grid">
                {[...REQUIRED_FIELDS, ...OPTIONAL_FIELDS].map(field => (
                  <div key={field.key} className="mapping-row">
                    <label className={REQUIRED_FIELDS.includes(field) ? 'required' : ''}>
                      {field.label}
                    </label>
                    <select 
                      value={mapping[field.key] || ''} 
                      onChange={(e) => handleMappingChange(field.key, e.target.value)}
                    >
                      <option value="">-- Ignore / Do not map --</option>
                      {csvHeaders.map(h => (
                        <option key={h} value={h}>{h}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              <div className="mode-selection">
                <h3>Import Mode</h3>
                <label className="radio-label">
                  <input 
                    type="radio" 
                    name="import_mode" 
                    checked={mode === 'append'} 
                    onChange={() => { setMode('append'); setConfirmReplace(false); }} 
                  />
                  <span>
                    <strong>Append</strong> (Add to existing inventory)
                  </span>
                </label>
                <label className="radio-label">
                  <input 
                    type="radio" 
                    name="import_mode" 
                    checked={mode === 'replace'} 
                    onChange={() => setMode('replace')} 
                  />
                  <span>
                    <strong>Replace</strong> (Delete all existing inventory and insert new)
                  </span>
                </label>

                {mode === 'replace' && (
                  <div className="warning-box">
                    <label className="checkbox-label warning-text">
                      <input 
                        type="checkbox" 
                        checked={confirmReplace} 
                        onChange={(e) => setConfirmReplace(e.target.checked)} 
                      />
                      I understand that this will PERMANENTLY DELETE all existing data.
                    </label>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          {step === 2 && (
            <>
              <button className="secondary-btn" onClick={() => setStep(1)} disabled={isUploading}>
                Back
              </button>
              <button 
                className="primary-btn" 
                onClick={handleUpload} 
                disabled={isUploading || (mode === 'replace' && !confirmReplace)}
              >
                {isUploading ? 'Uploading...' : 'Confirm Upload'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
