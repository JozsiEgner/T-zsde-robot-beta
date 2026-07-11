import React from "react";
import "./DollarThermometer.css";

export type DollarDirection = "UP" | "DOWN" | "NEUTRAL";

export interface DollarThermometerProps {
  direction: DollarDirection;
  signalScore: number;
  intensityScore: number;
  intensityLevel: string;
  confidenceScore: number;
  difficultyFactor: number;
  difficultyLevel: string;
  sourceHealthScore: number;
  title?: string;
}

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

function MetricBar({ label, value, text }: { label: string; value: number; text: string }) {
  return (
    <div className="dt-metric">
      <div className="dt-metric-row">
        <span>{label}</span>
        <strong>{text}</strong>
      </div>
      <div className="dt-track" aria-hidden="true">
        <div className="dt-fill" style={{ width: `${clamp01(value) * 100}%` }} />
      </div>
    </div>
  );
}

export function DollarThermometer({
  direction,
  signalScore,
  intensityScore,
  intensityLevel,
  confidenceScore,
  difficultyFactor,
  difficultyLevel,
  sourceHealthScore,
  title = "Dollar Thermometer",
}: DollarThermometerProps) {
  const normalizedSignal = clamp01((signalScore + 1) / 2);
  const directionClass = direction.toLowerCase();

  return (
    <section className={`dollar-thermometer dt-${directionClass}`}>
      <header className="dt-header">
        <div>
          <span className="dt-eyebrow">Civil Axis Output</span>
          <h2>{title}</h2>
        </div>
        <span className={`dt-direction dt-direction-${directionClass}`}>{direction}</span>
      </header>

      <div className="dt-gauge" role="img" aria-label={`Dollar direction ${direction}, score ${signalScore.toFixed(4)}`}>
        <div className="dt-scale">
          <span>DOWN</span>
          <span>NEUTRAL</span>
          <span>UP</span>
        </div>
        <div className="dt-gauge-track">
          <div className="dt-gauge-gradient" />
          <div className="dt-needle" style={{ left: `${normalizedSignal * 100}%` }} />
        </div>
        <div className="dt-score">Signal score: {signalScore.toFixed(4)}</div>
      </div>

      <div className="dt-metrics">
        <MetricBar label="Intensity" value={intensityScore} text={intensityLevel} />
        <MetricBar label="Confidence" value={confidenceScore} text={`${(clamp01(confidenceScore) * 100).toFixed(1)}%`} />
        <MetricBar label="Difficulty" value={difficultyFactor} text={difficultyLevel} />
        <MetricBar label="Source health" value={sourceHealthScore} text={`${(clamp01(sourceHealthScore) * 100).toFixed(1)}%`} />
      </div>
    </section>
  );
}

export default DollarThermometer;
