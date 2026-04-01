import React, { FC } from 'react';
import { GlassCardProps } from '../../types';
import './GlassCard.css';

const GlassCard: FC<GlassCardProps> = ({
  children,
  className = '',
  hoverEffect = true,
  style = {},
  ...props
}) => {
  return (
    <div
      className={`glass-panel ${
        hoverEffect ? 'hover-scale glass-card-glow' : ''
      } ${className}`}
      style={{ padding: '1.5rem', ...style }}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard;
