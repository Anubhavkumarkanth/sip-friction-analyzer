import React, { FC } from 'react';
import { ButtonProps } from '../../types';
import './Button.css';

const Button: FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  ...props
}) => {
  return (
    <button
      className={`custom-btn btn-${variant} btn-${size} hover-scale ${
        loading || disabled ? 'disabled' : ''
      } ${className}`}
      disabled={loading || disabled}
      {...props}
    >
      {loading ? '⏳ Loading...' : children}
    </button>
  );
};

export default Button;
