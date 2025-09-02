
import React, { useEffect, useState } from "react";
import { fetchInsights } from "../../services/insightsApi";
import SpendingChart from "./SpendingChart";
import CreditUtilizationGauge from "./CreditUtilizationGauge";

interface Insight {
  user_id: string;
  savings_recommendation: string;
  spending_breakdown: Record<string, number>;
  credit_utilization: number;
  narrative: string;
}

const FinancialHealth: React.FC<{ userId: string }> = ({ userId }) => {
  const [insight, setInsight] = useState<Insight | null>(null);

  useEffect(() => {
    fetchInsights(userId).then(data => setInsight(data));
  }, [userId]);

  if (!insight) return <p>Loading...</p>;

  return (
    <div className="financial-health-container">
      <h2>Financial Health</h2>
      <p><strong>Savings Recommendation:</strong> {insight.savings_recommendation}</p>
      <SpendingChart data={insight.spending_breakdown} />
      <CreditUtilizationGauge value={insight.credit_utilization} />
      <div className="narrative">
        <h3>AI-generated Advice</h3>
        <p>{insight.narrative}</p>
      </div>
    </div>
  );
};

export default FinancialHealth;
