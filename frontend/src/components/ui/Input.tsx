import React, { FC } from 'react';
import { InputProps } from '../../types';
import './Input.css';

const Input: FC<InputProps> = ({
  label,
  id,
  error,
  className = '',
  ...props
}) => {
  return (
    <div className={`input-group ${className}`}>
      {label && (
        <label htmlFor={id} className="input-label">
          {label}
        </label>
      )}
      <input
        id={id}
        className={`custom-input ${error ? 'input-error' : ''}`}
        {...props}
      />
      {error && <span className="error-text">{error}</span>}
    </div>
  );
};

export default Input;
