import { useState, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; 
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UploadCloud, FileText, CheckCircle, AlertOctagon, 
  Download, Sparkles, ChevronRight 
} from 'lucide-react';

const Dashboard = () => {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
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
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/generate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.status === 'success') {
        setReport(response.data.markdown_content);
        setDownloadUrl(`http://localhost:8000${response.data.pdf_download_url}`);
        setTimeout(() => reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 200);
      }
    } catch (err) {
      console.error(err);
      setError('Connection failed. Backend not running?');
    } finally {
      setLoading(false);
    }
  };

  // --- 1. AESTHETIC STYLES (Glass Tables + Gradients) ---
  const markdownStyles = `
    .report-content { color: #e2e8f0; font-size: 1.05rem; line-height: 1.7; }
    
    .report-content h1, .report-content h2, .report-content h3 {
      background: linear-gradient(to right, #ffffff, #94a3b8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-top: 2.5rem;
      margin-bottom: 1rem;
      font-weight: 700;
    }
    .report-content h1 { font-size: 2rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
    
    .report-content strong { color: #38bdf8; font-weight: 600; }
    
    /* Glass Tables */
    .report-content table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin: 2rem 0;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .report-content th {
      background: rgba(99, 102, 241, 0.1);
      color: #818cf8;
      font-weight: 600;
      padding: 16px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .report-content td {
      padding: 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #cbd5e1;
    }
  `;

  // --- 2. FULL WIDTH LAYOUT STYLES ---
  const styles = {
    appContainer: {
      display: 'flex',
      flexDirection: 'column', // Stack Header on top of Main
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      background: '#0f172a',
      backgroundImage: `radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%), 
                        radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.15) 0px, transparent 50%)`
    },
    // Header is now top-level
    header: {
      height: '80px',
      minHeight: '80px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 40px',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      background: 'rgba(15, 23, 42, 0.2)',
      zIndex: 10
    },
    // Main Area takes up all remaining space
    mainArea: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden'
    },
    // Scroll View
    contentScroll: {
      flex: 1,
      overflowY: 'auto',
      padding: '40px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      scrollBehavior: 'smooth'
    },
    glassCard: {
      background: 'rgba(30, 41, 59, 0.4)',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      borderRadius: '24px',
      padding: '40px',
      backdropFilter: 'blur(20px)',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
      width: '100%',
      maxWidth: '900px'
    }
  };

  return (
    <div style={styles.appContainer}>
      <style>{markdownStyles}</style>

      {/* HEADER (Now contains Logo + Breadcrumbs) */}
      <header style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            {/* LOGO MOVED HERE */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '24px', height: '24px', background: 'linear-gradient(135deg, #6366f1, #06b6d4)', borderRadius: '6px' }}></div>
                <span style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '-0.5px', color: 'white' }}>
                  GenAI<span style={{color: '#6366f1'}}>Engine</span>
                </span>
            </div>
            {/* Divider */}
            <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)' }}></div>
            {/* Breadcrumb */}
            <div style={{ color: '#94a3b8' }}>Workspace / Strategic Analysis</div>
        </div>

        <div style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '6px 12px', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 600, border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          ENTERPRISE V2.0
        </div>
      </header>

      {/* MAIN CONTENT (Full Width) */}
      <div style={styles.mainArea}>
        <div style={styles.contentScroll}>
          
          {/* Hero Content */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} 
            style={{ width: '100%', maxWidth: '900px', textAlign: 'center', marginBottom: '40px' }}
          >
             <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', padding: '8px 16px', borderRadius: '20px', marginBottom: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
               <Sparkles size={14} color="#6366f1" />
               <span style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>Powered by Qwen-3 Cloud AI</span>
             </div>
             
             <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '16px', background: 'linear-gradient(to right, white, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: '0 0 20px 0' }}>Strategic Document Intelligence</h1>
             
             {/* UPLOAD CARD */}
             <div style={styles.glassCard}>
                <input type="file" id="file-upload" style={{ display: 'none' }} onChange={handleFileChange} accept=".pdf,.xlsx,.csv,.docx" />
                
                <label htmlFor="file-upload" style={{ 
                  border: `2px dashed ${file ? '#10b981' : 'rgba(255, 255, 255, 0.1)'}`, 
                  borderRadius: '16px', padding: '60px', cursor: 'pointer', 
                  background: file ? 'rgba(16, 185, 129, 0.05)' : 'rgba(15, 23, 42, 0.3)', 
                  display: 'block', transition: 'all 0.3s'
                }}>
                  {file ? (
                    <div>
                      <CheckCircle size={48} color="#10b981" style={{ marginBottom: '15px', display: 'block', margin: '0 auto 15px' }} />
                      <h3 style={{ margin: 0, color: 'white' }}>{file.name}</h3>
                      <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Ready to Process</p>
                    </div>
                  ) : (
                    <div>
                      <UploadCloud size={32} color="#818cf8" style={{ display: 'block', margin: '0 auto 15px' }} />
                      <h3 style={{ margin: '0 0 8px 0', color: 'white' }}>Click to Upload Document</h3>
                      <p style={{ color: '#64748b', margin: 0 }}>PDF, Excel, CSV (Max 50MB)</p>
                    </div>
                  )}
                </label>

                {error && <div style={{ marginTop: '20px', color: '#f43f5e', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}><AlertOctagon size={18} /> {error}</div>}

                <button 
                  onClick={handleGenerate} disabled={!file || loading}
                  style={{ 
                    background: 'linear-gradient(135deg, #6366f1, #4f46e5)', color: 'white', border: 'none', 
                    padding: '18px 48px', borderRadius: '14px', fontSize: '1rem', fontWeight: 600, cursor: !file ? 'not-allowed' : 'pointer', 
                    marginTop: '30px', boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)', opacity: !file ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: '10px'
                  }}
                >
                  {loading ? 'Processing...' : 'Generate Report'} <ChevronRight size={18} />
                </button>
             </div>
          </motion.div>

          {/* REPORT SECTION */}
          <AnimatePresence>
            {report && (
              <motion.div ref={reportRef} initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} style={{ width: '100%', maxWidth: '900px' }}>
                <div style={styles.glassCard}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <FileText size={24} color="#818cf8" />
                      <h2 style={{ margin: 0, fontSize: '1.25rem', color: 'white' }}>Executive Analysis</h2>
                    </div>
                    <button onClick={() => window.open(downloadUrl, '_blank')} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Download size={16} /> PDF Export
                    </button>
                  </div>
                  
                  {/* MARKDOWN RENDERER (With Image Fixes) */}
                  <div className="report-content">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        img: ({node, ...props}) => {
                          let src = props.src;
                          if (src && !src.startsWith('http')) {
                            const filename = src.split('/').pop();
                            src = `http://localhost:8000/artifacts/${filename}`;
                          }
                          return (
                            <img 
                              {...props} 
                              src={src} 
                              style={{ maxWidth: '100%', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', margin: '20px 0', boxShadow: '0 10px 30px rgba(0,0,0,0.3)' }}
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                          );
                        }
                      }}
                    >
                      {report}
                    </ReactMarkdown>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          <div style={{ height: '100px' }}></div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;