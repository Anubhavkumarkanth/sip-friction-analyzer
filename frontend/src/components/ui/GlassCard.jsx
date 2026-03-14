import React from 'react';
import './GlassCard.css';

const GlassCard = ({ children, className = '', style = {}, hoverEffect = true, ...props }) => {
  return (
    <div
      className={`glass-panel ${hoverEffect ? 'hover-scale glass-card-glow' : ''} ${className}`}
      style={{ padding: '1.5rem', ...style }}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard;
