import React, { useState } from 'react';
import StatusBadge from './StatusBadge';

const PatientList = ({ patients, onFinishPatient }) => {
  const [loadingId, setLoadingId] = useState(null);

  const handleFinish = async (e, patientId) => {
    e.stopPropagation(); // Prevent row click
    setLoadingId(patientId);
    await onFinishPatient(patientId);
    setLoadingId(null);
  };

  return (
    <div className="patient-list-container">
      <table className="patient-list-table">
        <thead>
          <tr className="text-left text-gray-500 text-sm">
            <th className="pb-2 pl-4">Heure</th>
            <th className="pb-2">Patient</th>
            <th className="pb-2">Statut</th>
            <th className="pb-2 pr-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient, index) => (
            <tr
              key={patient.id}
              className="patient-row animate-slide-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <td className="font-mono text-gray-600 font-medium">
                {patient.time}
              </td>
              <td>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600">
                    {patient.initials}
                  </div>
                  <span className="font-medium text-gray-800">{patient.name}</span>
                </div>
              </td>
              <td>
                <StatusBadge status={patient.status} />
              </td>
              <td className="text-right">
                {patient.status === 'EN_COURS' && (
                  <button
                    className="btn-primary text-sm py-1 px-3"
                    onClick={(e) => handleFinish(e, patient.id)}
                    disabled={loadingId === patient.id}
                  >
                    {loadingId === patient.id ? (
                      <span className="flex items-center gap-2">
                        <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        ...
                      </span>
                    ) : (
                      'Terminer'
                    )}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PatientList;
