
import React from "react";
import { CircularProgress } from "@mui/material";

const CreditUtilizationGauge = ({ value }: { value: number }) => {
  const percent = Math.round(value * 100);
  return (
    <div>
      <p>Credit Utilization: {percent}%</p>
      <CircularProgress variant="determinate" value={percent} />
    </div>
  );
};

export default CreditUtilizationGauge;
