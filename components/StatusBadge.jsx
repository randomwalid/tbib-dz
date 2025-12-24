import React from 'react';

const StatusBadge = ({ status }) => {
  const getBadgeConfig = (status) => {
    switch (status) {
      case 'EN_COURS':
        return {
          className: 'in-progress',
          label: 'En cours',
          icon: <span className="pulsing-dot"></span>
        };
      case 'EN_ATTENTE':
        return {
          className: 'waiting',
          label: 'En attente',
          icon: null
        };
      case 'TERMINE':
        return {
          className: 'completed',
          label: 'Terminé',
          icon: <span>✓</span>
        };
      default:
        return {
          className: 'waiting',
          label: status,
          icon: null
        };
    }
  };

  const config = getBadgeConfig(status);

  return (
    <div className={`status-badge ${config.className} fade-transition`}>
      {config.icon}
      <span>{config.label}</span>
    </div>
  );
};

export default StatusBadge;
