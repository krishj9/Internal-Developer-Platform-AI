import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import LoginView from './components/LoginView';
import TemplateCatalog from './components/TemplateCatalog';
import NewRequestModal from './components/NewRequestModal';
import RequestTracker from './components/RequestTracker';
import DeploymentsList from './components/DeploymentsList';
import GovernanceDashboard from './components/GovernanceDashboard';
import UserGuide from './components/UserGuide';

export default function App() {
  const { isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('catalog');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [activeRequestId, setActiveRequestId] = useState('');

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="pulse-dot" style={{ width: '20px', height: '20px' }} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  const handleRequestCreated = (requestData) => {
    setActiveRequestId(requestData.request_id);
    setActiveTab('requests');
  };

  const handleTrackRequest = (requestId) => {
    setActiveRequestId(requestId);
    setActiveTab('requests');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main style={{ flex: 1, maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'catalog' && (
          <TemplateCatalog onSelectTemplate={(tpl) => setSelectedTemplate(tpl)} />
        )}
        {activeTab === 'deployments' && (
          <DeploymentsList onTrackRequest={handleTrackRequest} />
        )}
        {activeTab === 'requests' && (
          <RequestTracker initialRequestId={activeRequestId} />
        )}
        {activeTab === 'governance' && (
          <GovernanceDashboard />
        )}
        {activeTab === 'guide' && (
          <UserGuide />
        )}
      </main>

      {/* Deploy Template Modal */}
      {selectedTemplate && (
        <NewRequestModal
          template={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
          onRequestCreated={handleRequestCreated}
        />
      )}
    </div>
  );
}
