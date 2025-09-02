
import React from "react";
import { Bar } from "react-chartjs-2";

const SpendingChart = ({ data }: { data: Record<string, number> }) => {
  const chartData = {
    labels: Object.keys(data),
    datasets: [
      {
        label: "Spending Breakdown",
        data: Object.values(data),
        backgroundColor: "rgba(54, 162, 235, 0.6)",
      },
    ],
  };

  return <Bar data={chartData} />;
};

export default SpendingChart;
