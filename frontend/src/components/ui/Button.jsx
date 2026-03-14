import React from 'react';
import './Button.css';

const Button = ({ children, variant = 'primary', className = '', ...props }) => {
  return (
    <button className={`custom-btn btn-${variant} hover-scale ${className}`} {...props}>
      {children}
    </button>
  );
};

export default Button;
