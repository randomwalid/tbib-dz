import React, { useState, useEffect } from 'react';
import PatientList from '../../components/PatientList';
import '../../styles/dashboard.css';

const PractitionerDashboard = () => {
  const [currentMode, setCurrentMode] = useState('TICKET'); // 'TICKET' or 'SMART_RDV'
  const [accumulatedDelay, setAccumulatedDelay] = useState(45); // Minutes, >0 triggers alert
  const [patients, setPatients] = useState([
    { id: 1, time: '09:00', initials: 'AB', name: 'A. Benali', status: 'TERMINE' },
    { id: 2, time: '09:20', initials: 'MK', name: 'M. Kader', status: 'EN_COURS' },
    { id: 3, time: '09:40', initials: 'SL', name: 'S. Lamri', status: 'EN_ATTENTE' },
    { id: 4, time: '10:00', initials: 'FZ', name: 'F. Zohra', status: 'EN_ATTENTE' },
    { id: 5, time: '10:20', initials: 'RY', name: 'R. Yacine', status: 'EN_ATTENTE' },
  ]);

  const currentDate = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  const handleModeToggle = (mode) => {
    setCurrentMode(mode);
  };

  const handleShiftDelay = () => {
    // Logic to shift appointments
    console.log('Shifting all appointments by 30 mins');
    alert('Décalage de 30 minutes appliqué avec succès.');
    setAccumulatedDelay(Math.max(0, accumulatedDelay - 30));
  };

  const handleFinishPatient = async (id) => {
    // Simulate API call
    return new Promise((resolve) => {
      setTimeout(() => {
        setPatients(prev => prev.map(p => {
          if (p.id === id) return { ...p, status: 'TERMINE' };
          // Naive logic to move next patient to EN_COURS
          return p;
        }));
        // Find next waiting and make it EN_COURS
        setPatients(prev => {
          const nextIdx = prev.findIndex(p => p.id === id) + 1;
          if (nextIdx < prev.length) {
            const nextP = prev[nextIdx];
            return prev.map(p => p.id === nextP.id ? { ...p, status: 'EN_COURS' } : p);
          }
          return prev;
        });
        resolve();
      }, 1000);
    });
  };

  return (
    <div className="min-h-screen p-6 max-w-7xl mx-auto">
      {/* Header */}
      <header className="dashboard-header animate-slide-in">
        <div className="user-profile">
          <div className="avatar">Dr</div>
          <div>
            <h1 className="text-xl font-bold flex items-center">
              Dr. Ahmed Benali
              <span className="kyc-badge">
                ✓ KYC VERIFIED
              </span>
            </h1>
            <p className="text-sm text-gray-500">Cardiologue</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-medium text-gray-700 capitalize">{currentDate}</p>
        </div>
      </header>

      {/* Control Center */}
      <section className="mb-8 animate-slide-in" style={{ animationDelay: '100ms' }}>
        <div className="control-center-card glass-panel flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex bg-gray-100 p-1 rounded-lg">
            <button
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${currentMode === 'TICKET' ? 'bg-white shadow text-teal-600' : 'text-gray-500 hover:text-gray-700'}`}
              onClick={() => handleModeToggle('TICKET')}
            >
              Mode Ticket
            </button>
            <button
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${currentMode === 'SMART_RDV' ? 'bg-white shadow text-teal-600' : 'text-gray-500 hover:text-gray-700'}`}
              onClick={() => handleModeToggle('SMART_RDV')}
            >
              Mode RDV Smart
            </button>
          </div>

          <div className="flex items-center gap-3 text-sm text-gray-600 bg-blue-50 px-4 py-2 rounded-lg border border-blue-100">
            <div className="w-5 h-5 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center font-bold text-xs">i</div>
            <p>
              {currentMode === 'TICKET'
                ? 'Les patients entrent par ordre d\'arrivée.'
                : 'Les patients suivent l\'agenda prédictif.'}
            </p>
          </div>
        </div>
      </section>

      {/* Accumulated Delay Section (Conditional) */}
      {accumulatedDelay > 0 && (
        <section className="mb-8 animate-slide-in" style={{ animationDelay: '200ms' }}>
          <div className="glass-alert p-4 rounded-xl flex flex-col md:flex-row justify-between items-center animate-shake gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-full text-red-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="font-bold text-lg text-red-600">Retard Accumulé : {accumulatedDelay} min</h3>
                <p className="text-sm text-red-400">Impact estimé sur les 3 prochains RDV</p>
              </div>
            </div>
            <button
              onClick={handleShiftDelay}
              className="btn-danger-outline bg-white hover:bg-red-50"
            >
              Urgence : Décaler tout de 30min
            </button>
          </div>
        </section>
      )}

      {/* Patient List */}
      <section className="animate-slide-in" style={{ animationDelay: '300ms' }}>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
            <h2 className="font-bold text-gray-700">File d'attente du jour</h2>
            <span className="text-sm text-gray-500 bg-white px-2 py-1 rounded border">
              {patients.filter(p => p.status === 'EN_ATTENTE').length} en attente
            </span>
          </div>
          <div className="p-4">
            <PatientList
              patients={patients}
              onFinishPatient={handleFinishPatient}
            />
          </div>
        </div>
      </section>
    </div>
  );
};

export default PractitionerDashboard;
