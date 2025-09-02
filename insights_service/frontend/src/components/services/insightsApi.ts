
import axios from "axios";

const BASE_URL = process.env.REACT_APP_INSIGHTS_API || "http://localhost:8080/api/v1/insights";

export const fetchInsights = async (userId: string) => {
  const response = await axios.get(`${BASE_URL}/${userId}`);
  return response.data;
};
