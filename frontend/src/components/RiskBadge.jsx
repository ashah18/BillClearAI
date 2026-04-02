/**
 * Displays a color-coded badge representing the risk level of a line item.
 * @param {{ risk_level: 'green' | 'yellow' | 'red' }} props
 */
export default function RiskBadge({ risk_level }) {
  const styles = {
    green: "bg-green-100 text-green-800",
    yellow: "bg-yellow-100 text-yellow-800",
    red: "bg-red-100 text-red-800",
  };

  const labels = {
    green: "Low Risk",
    yellow: "Review",
    red: "High Risk",
  };

  const level = risk_level || "green";

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[level]}`}
    >
      {labels[level]}
    </span>
  );
}
