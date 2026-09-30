import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChaosPanel } from './ChaosPanel';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div style={{ display: 'flex', justifyContent: 'center', padding: '50px 20px' }}>
      <ChaosPanel />
    </div>
  </React.StrictMode>
);
