import React, { useState } from 'react';

export const ChaosPanel: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string>("SYSTEM NOMINAL");

  const injectFault = async (faultType: string) => {
    if (!window.confirm(`Initiate ${faultType}? Emergency shutdown will trip immediately.`)) return;
    setLoading(true);
    try {
      const res = await fetch('/api/chaos/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: faultType })
      });
      const data = await res.json();
      setStatus(`CRITICAL TRIP: ${data.action_taken}`);
    } catch {
      setStatus("Error injecting fault");
    } finally {
      setLoading(false);
    }
  };

  const resetSystem = async () => {
    setLoading(true);
    try {
      await fetch('/api/chaos/reset', { method: 'POST' });
      setStatus("SYSTEM NOMINAL");
    } catch {
      setStatus("Error resetting system");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', background: '#121212', color: '#fff', borderRadius: '8px', maxWidth: '600px', width: '100%' }}>
      <h3 style={{ margin: '0 0 16px', color: '#f44336' }}>? Chaos Testing & Fault Injection</h3>
      <div style={{ marginBottom: '16px', padding: '12px', background: '#1e1e1e', borderRadius: '4px' }}>
        <strong>System Status: </strong>
        <span style={{ color: status.includes('CRITICAL') ? '#f44336' : '#4caf50' }}>{status}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <button 
          disabled={loading} 
          onClick={() => injectFault('BEARING_SEIZURE')}
          style={{ padding: '12px', background: '#d32f2f', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Inject Bearing Seizure
        </button>
        <button 
          disabled={loading} 
          onClick={() => injectFault('TUBE_RUPTURE')}
          style={{ padding: '12px', background: '#c2185b', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Inject Tube Rupture
        </button>
        <button 
          disabled={loading} 
          onClick={() => injectFault('COMPRESSOR_SURGE')}
          style={{ padding: '12px', background: '#7b1fa2', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Inject Compressor Surge
        </button>
        <button 
          disabled={loading} 
          onClick={resetSystem}
          style={{ padding: '12px', background: '#388e3c', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Normalize & Reset ESD
        </button>
      </div>
    </div>
  );
};
