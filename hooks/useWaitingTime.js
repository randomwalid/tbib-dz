import { useState, useEffect, useRef } from 'react';

// Simple useInterval implementation for internal use
function useInterval(callback, delay) {
  const savedCallback = useRef();

  // Remember the latest callback.
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval.
  useEffect(() => {
    function tick() {
      savedCallback.current();
    }
    if (delay !== null) {
      let id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
}

const useWaitingTime = (initialTime = 25) => {
  const [waitingTime, setWaitingTime] = useState(initialTime);

  useInterval(() => {
    setWaitingTime((prev) => (prev > 0 ? prev - 1 : 0));
  }, 60000); // 60000ms = 1 minute

  return waitingTime;
};

export default useWaitingTime;
