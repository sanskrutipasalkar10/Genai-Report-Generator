import { useState, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { 
  UploadCloud, FileText, CheckCircle, AlertTriangle, 
  Download, Play, Loader2, BarChart3, Settings, 
  PieChart, Layers, UserCircle, ChevronRight 
} from 'lucide-react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  
  // For scrolling to report after generation
  const reportRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
      setReport(null);
    }
  };

  const handleGenerate = async () => {
    if (!file) return;

    setLoading(true);
    setError('');
    setReport(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/generate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.status === 'success') {
        setReport(response.data.markdown_content);
        setDownloadUrl(`http://localhost:8000${response.data.pdf_download_url}`);
        
        // Smooth scroll to report
        setTimeout(() => {
          reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    } catch (err) {
      console.error(err);
      setError('Connection to AI Engine failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) window.open(downloadUrl, '_blank');
  };

  return (
    <div className="dashboard-container">
      
      {/* 1. SIDEBAR */}
      <aside className="sidebar">
        <div className="logo-container">
          <Layers size={28} color="#818cf8" />
          <span className="logo-text">GenAI Engine</span>
        </div>

        <nav className="nav-menu">
          <div className="nav-item active">
            <BarChart3 size={20} />
            <span>Analysis Dashboard</span>
          </div>
          <div className="nav-item">
            <PieChart size={20} />
            <span>Past Reports</span>
          </div>
          <div className="nav-item">
            <Settings size={20} />
            <span>Configurations</span>
          </div>
        </nav>

        <div className="sidebar-footer">
          <UserCircle size={32} />
          <div>
            <div style={{fontWeight: 600, color: 'white'}}>Admin User</div>
            <div style={{fontSize: '0.75rem'}}>Enterprise Plan</div>
          </div>
        </div>
      </aside>

      {/* 2. MAIN CONTENT */}
      <main className="main-content">
        
        {/* Top Header */}
        <header className="top-bar">
          <div className="breadcrumb">Dashboard / New Analysis</div>
          <div style={{display: 'flex', gap: '15px'}}>
             <span style={{color: '#64748b', fontSize: '0.9rem'}}>v2.0 Stable</span>
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="scroll-area">
          
          {/* Hero Section */}
          <section className="hero-section">
            <h1 className="hero-title">Strategic Document Analysis</h1>
            <p className="hero-subtitle">Upload financial reports, contracts, or technical diagrams for instant AI reasoning.</p>
            
            <div className="upload-card">
              <input 
                type="file" 
                id="file-upload" 
                style={{ display: 'none' }} 
                onChange={handleFileChange}
                accept=".pdf,.csv,.xlsx,.docx,.png,.jpg,.jpeg"
              />
              
              <label 
                htmlFor="file-upload" 
                className={`drop-zone ${file ? 'has-file' : ''}`}
              >
                {file ? (
                  <>
                    <div className="icon-wrapper" style={{color: 'var(--success)'}}>
                      <CheckCircle size={32} />
                    </div>
                    <div>
                      <h3 style={{margin: '0 0 5px 0', color: '#0f172a'}}>{file.name}</h3>
                      <span style={{color: '#64748b', fontSize: '0.9rem'}}>
                        Ready for analysis • {(file.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="icon-wrapper" style={{color: 'var(--primary)'}}>
                      <UploadCloud size={32} />
                    </div>
                    <div>
                      <h3 style={{margin: '0 0 5px 0', color: '#0f172a'}}>Click to Upload File</h3>
                      <p style={{margin: 0, color: '#94a3b8', fontSize: '0.9rem'}}>
                        PDF, Excel, CSV, or Images (Max 50MB)
                      </p>
                    </div>
                  </>
                )}
              </label>
            </div>

            {error && (
              <div style={{marginTop: '20px', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'}}>
                <AlertTriangle size={18} />
                {error}
              </div>
            )}

            <button 
              className={`analyze-btn ${loading ? 'animate-pulse-shadow' : ''}`} 
              onClick={handleGenerate} 
              disabled={!file || loading}
            >
              {loading ? (
                <>
                  <Loader2 className="loader-spin" size={20} />
                  Running AI Models...
                </>
              ) : (
                <>
                  <Play size={20} fill="currentColor" />
                  Generate Strategic Report
                </>
              )}
            </button>
          </section>

          {/* Report Results */}
          {report && (
            <section className="report-wrapper" ref={reportRef}>
              <div className="report-card">
                <div className="report-toolbar">
                  <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                    <FileText size={20} color="var(--primary)" />
                    <span style={{fontWeight: 600, color: '#334155'}}>Generated Analysis</span>
                  </div>
                  <button className="analyze-btn" style={{padding: '8px 16px', marginTop: 0, fontSize: '0.9rem'}} onClick={handleDownload}>
                    <Download size={16} />
                    Download PDF
                  </button>
                </div>
                
                <div className="report-body">
                  {/* 🟢 CUSTOM IMAGE RENDERER */}
                  <ReactMarkdown
                    components={{
                      img: ({node, ...props}) => {
                        let src = props.src;
                        // Rewrite local paths to point to Backend API
                        if (src && !src.startsWith('http')) {
                          const cleanPath = src.split('artifacts/').pop(); 
                          src = `http://localhost:8000/artifacts/${cleanPath}`;
                        }
                        return (
                          <img 
                            {...props} 
                            src={src} 
                            alt={props.alt} 
                            style={{
                              maxWidth: '100%', 
                              borderRadius: '12px', 
                              border: '1px solid #e2e8f0',
                              marginTop: '20px',
                              marginBottom: '20px',
                              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                            }} 
                          />
                        );
                      }
                    }}
                  >
                    {report}
                  </ReactMarkdown>
                </div>
              </div>
            </section>
          )}

          <div style={{height: '50px'}}></div> {/* Bottom spacer */}
        </div>
      </main>
    </div>
  );
}

export default App;