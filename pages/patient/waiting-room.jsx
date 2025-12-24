import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import CircularProgress from '../../components/CircularProgress';
import useWaitingTime from '../../hooks/useWaitingTime';

const WaitingRoom = () => {
  const waitingTime = useWaitingTime(25);
  const [confirmationStatus, setConfirmationStatus] = useState(false);
  const [loadingConfirmation, setLoadingConfirmation] = useState(false);

  const handleConfirm = () => {
    if (confirmationStatus || loadingConfirmation) return;

    setLoadingConfirmation(true);
    // Simulate API call with 2s delay
    setTimeout(() => {
      setLoadingConfirmation(false);
      setConfirmationStatus(true);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col font-sans text-slate-800">

      {/* Main Content Area - Centered */}
      <div className="flex-1 flex flex-col items-center justify-center w-full px-4 pb-32">
        <CircularProgress waitingTime={waitingTime} />

        {/* Confirmation Success Message */}
        <AnimatePresence>
          {confirmationStatus && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-12 text-center"
            >
              <div className="inline-flex items-center px-5 py-3 rounded-full bg-[#E8F8F5] text-[#3DBAA2] font-semibold shadow-sm">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                </svg>
                Présence confirmée
              </div>
              <p className="mt-4 text-gray-500 text-sm">
                Le médecin a été notifié de votre arrivée.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Action Area */}
      {/* Mobile: Fixed bottom with 24px padding (p-6) */}
      {/* Desktop: Static or centered differently if needed, but keeping consistent per mobile-first request */}
      {!confirmationStatus && (
        <div className="fixed bottom-0 left-0 right-0 p-6 bg-white border-t border-gray-50 md:static md:bg-transparent md:border-0 md:flex md:justify-center md:pb-12 md:p-0">
          <RippleButton
            onClick={handleConfirm}
            isLoading={loadingConfirmation}
          >
            Je confirme ma présence
          </RippleButton>
        </div>
      )}
    </div>
  );
};

// Ripple Button Component
const RippleButton = ({ children, onClick, isLoading }) => {
  const [ripples, setRipples] = useState([]);

  const handleClick = (e) => {
    if (isLoading) return;

    // Create ripple
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const id = Date.now();

    setRipples((prev) => [...prev, { x, y, id }]);

    if (onClick) onClick(e);

    // Cleanup ripple after animation
    setTimeout(() => {
        setRipples((prev) => prev.filter(r => r.id !== id));
    }, 600);
  };

  return (
    <button
      className="relative w-full md:w-auto md:min-w-[320px] bg-[#3DBAA2] text-white font-bold text-lg py-4 px-6 rounded-2xl shadow-lg shadow-[#3DBAA2]/20 overflow-hidden disabled:opacity-70 disabled:cursor-not-allowed transition-transform active:scale-[0.98]"
      onClick={handleClick}
      disabled={isLoading}
    >
      {/* Ripples */}
      {ripples.map((ripple) => (
        <motion.span
          key={ripple.id}
          initial={{ scale: 0, opacity: 0.5 }}
          animate={{ scale: 4, opacity: 0 }}
          transition={{ duration: 0.6 }}
          className="absolute bg-white rounded-full pointer-events-none"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: 100,
            height: 100,
            x: "-50%",
            y: "-50%",
          }}
        />
      ))}

      {/* Content */}
      <div className="relative z-10 flex items-center justify-center">
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Chargement...
          </>
        ) : (
            children
        )}
      </div>
    </button>
  );
};

export default WaitingRoom;
