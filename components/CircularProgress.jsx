import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const CircularProgress = ({ waitingTime }) => {
  // SVG Configuration
  // Using viewBox 0 0 200 200. Radius 90 keeps it inside with strokeWidth 10.
  const radius = 90;
  const circumference = 2 * Math.PI * radius;

  // Animation for the progress circle
  // 0% = gray (#D1D5DB), 100% = turquoise (#3DBAA2)
  const circleVariants = {
    hidden: {
      strokeDashoffset: circumference,
      stroke: "#D1D5DB"
    },
    visible: {
      strokeDashoffset: 0, // Full circle
      stroke: "#3DBAA2",
      transition: {
        duration: 0.8,
        ease: "easeOut",
        stroke: { duration: 0.8, ease: "easeOut" }
      }
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center w-[200px] h-[200px] md:w-[280px] md:h-[280px]">
      <svg
        className="absolute w-full h-full transform -rotate-90"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Background Track */}
        <circle
          cx="100"
          cy="100"
          r={radius}
          fill="none"
          stroke="#E8F8F5"
          strokeWidth="12"
        />
        {/* Animated Progress Circle */}
        <motion.circle
          cx="100"
          cy="100"
          r={radius}
          fill="none"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial="hidden"
          animate="visible"
          variants={circleVariants}
        />
      </svg>

      {/* Central Content */}
      <div className="flex flex-col items-center justify-center z-10">
        <span className="text-sm md:text-base font-medium text-gray-500 mb-2">
          Votre tour arrive
        </span>

        <div className="flex items-baseline text-[#3DBAA2]">
          {/* Flip Animation for Number */}
          <div className="relative h-12 md:h-16 overflow-hidden flex flex-col items-center justify-center">
            <AnimatePresence mode="popLayout">
              <motion.span
                key={waitingTime}
                initial={{ y: "100%", opacity: 0 }}
                animate={{ y: "0%", opacity: 1 }}
                exit={{ y: "-100%", opacity: 0 }}
                transition={{ duration: 0.6, ease: "backOut" }}
                className="text-5xl md:text-6xl font-bold leading-none block"
              >
                {waitingTime}
              </motion.span>
            </AnimatePresence>
          </div>
          <span className="text-xl md:text-2xl font-medium ml-1">min</span>
        </div>
      </div>
    </div>
  );
};

export default CircularProgress;
