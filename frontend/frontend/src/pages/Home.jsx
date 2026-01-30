import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronRight, Sparkles, Layers, ShieldCheck, Zap } from 'lucide-react';

const Home = () => {
  const navigate = useNavigate();

  // Animation Variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.2, delayChildren: 0.3 }
    }
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1, 
      transition: { type: "spring", stiffness: 50 } 
    }
  };

  return (
    <div className="home-container" style={{ minHeight: '100vh', position: 'relative', overflowY: 'auto', overflowX: 'hidden' }}>
      
      {/* Background Gradients */}
      <div style={{ position: 'absolute', top: '-10%', left: '20%', width: '500px', height: '500px', background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)', filter: 'blur(80px)', zIndex: 0 }} />
      <div style={{ position: 'absolute', bottom: '-10%', right: '10%', width: '600px', height: '600px', background: 'radial-gradient(circle, rgba(6,182,212,0.15) 0%, transparent 70%)', filter: 'blur(100px)', zIndex: 0 }} />

      {/* Navbar (Clean - No Sign In Button) */}
      <nav style={{ display: 'flex', justifyContent: 'center', padding: '40px 0', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="logo-glow"></div>
          <span style={{ fontSize: '1.8rem', fontWeight: 700, letterSpacing: '-0.5px', color: 'white' }}>
            GenAI<span style={{color: '#6366f1'}}>Engine</span>
          </span>
        </div>
      </nav>

      {/* Main Hero Content */}
      <motion.div 
        className="hero-content"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{ textAlign: 'center', marginTop: '40px', position: 'relative', zIndex: 10, padding: '0 20px', paddingBottom: '100px' }}
      >
        <motion.div variants={itemVariants}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', padding: '8px 20px', borderRadius: '30px', border: '1px solid rgba(255,255,255,0.1)', marginBottom: '25px' }}>
            <Sparkles size={16} color="#06b6d4" />
            <span style={{ color: '#94a3b8', fontSize: '0.9rem', fontWeight: 500 }}>AI-Powered Strategic Intelligence</span>
          </div>
        </motion.div>

        <motion.h1 variants={itemVariants} style={{ fontSize: '4rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '20px', maxWidth: '900px', marginInline: 'auto', color: 'white' }}>
          Turn Complex Documents into <br />
          <span style={{ background: 'linear-gradient(to right, #818cf8, #22d3ee)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Clear Strategy.
          </span>
        </motion.h1>

        <motion.p variants={itemVariants} style={{ color: '#94a3b8', fontSize: '1.25rem', maxWidth: '600px', margin: '0 auto 50px auto', lineHeight: 1.6 }}>
          Upload any PDF, Excel, or technical diagram. Our Enterprise AI inspects, analyzes, and drafts professional reports in seconds.
        </motion.p>

        {/* 🟢 THE BIG START BUTTON */}
        <motion.div variants={itemVariants}>
            <button 
            onClick={() => navigate('/app')}
            className="glow-btn"
            style={{ 
                padding: '24px 60px', 
                fontSize: '1.3rem', 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: '15px',
                borderRadius: '50px',
                boxShadow: '0 0 30px rgba(99, 102, 241, 0.4)'
            }}
            >
            Start Generating Reports <ChevronRight size={24} />
            </button>
        </motion.div>

        {/* Feature Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          style={{ 
             display: 'flex', 
             flexWrap: 'wrap', 
             gap: '30px', 
             justifyContent: 'center', 
             marginTop: '80px' 
          }}
        >
          <FeatureCard icon={<Zap color="#f59e0b" />} title="Instant Analysis" desc="Process 50+ page PDFs in under 30 seconds." />
          <FeatureCard icon={<Layers color="#6366f1" />} title="Multi-Format" desc="Works with Excel, CSV, PDF, and Images." />
          <FeatureCard icon={<ShieldCheck color="#10b981" />} title="Enterprise Safe" desc="Data is processed locally on secure servers." />
        </motion.div>

      </motion.div>
    </div>
  );
};

// Mini Component for Features
const FeatureCard = ({ icon, title, desc }) => (
  <div style={{ background: 'rgba(30, 41, 59, 0.4)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.05)', padding: '30px', borderRadius: '20px', width: '300px', textAlign: 'left' }}>
    <div style={{ background: 'rgba(255,255,255,0.05)', width: '50px', height: '50px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px' }}>
      {icon}
    </div>
    <h3 style={{ fontSize: '1.2rem', marginBottom: '10px', color: 'white' }}>{title}</h3>
    <p style={{ color: '#94a3b8', lineHeight: 1.5 }}>{desc}</p>
  </div>
);

export default Home;