import React, { useEffect } from 'react';

export function Modal({ isOpen, onClose, children, slideOver }) {
  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', onKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  if (slideOver) {
    return (
      <div
        className="fixed inset-0 z-50 flex bg-black bg-opacity-50"
        onClick={onClose}
        role="dialog"
        aria-modal="true"
      >
        <div
          className="bg-white shadow-lg w-96 max-w-full h-full fixed right-0 top-0 overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {children}
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="bg-white rounded p-6 max-w-lg w-full"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
        <button
          onClick={onClose}
          className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          aria-label="Close modal"
        >
          Close
        </button>
      </div>
    </div>
  );
}
