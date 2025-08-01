import { Responsive, WidthProvider } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { useSocket } from "../../hooks/useSocket";
import { Line, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js/auto";
import { useMemo, useState } from "react";
import clsx from "clsx";
import "./dashboard.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const ResponsiveGridLayout = WidthProvider(Responsive);

export default function RealtimeDashboard() {
  const { data } = useSocket();
  const [dark, setDark] = useState(true);

  const submissionChart = useMemo(() => {
    const labels = data.submissions.map((s) =>
      new Date(s.timestamp).toLocaleTimeString()
    );
    return {
      labels,
      datasets: [
        {
          label: "Submissions",
          data: data.submissions.map((_, i) => i + 1),
          borderColor: "#6366f1",
          backgroundColor: "rgba(99,102,241,0.3)",
        },
      ],
    };
  }, [data.submissions]);

  const activityChart = useMemo(() => {
    const labels = data.activities.map((a) =>
      new Date(a.timestamp).toLocaleTimeString()
    );
    return {
      labels,
      datasets: [
        {
          label: "Activity",
          data: Array.from({ length: labels.length }, () => 1),
          backgroundColor: "#f43f5e",
        },
      ],
    };
  }, [data.activities]);

  const layout = [
    { i: "submissions", x: 0, y: 0, w: 6, h: 4 },
    { i: "activity", x: 6, y: 0, w: 6, h: 4 },
  ];

  return (
    <div
      className={clsx(
        "min-h-screen",
        dark ? "dark bg-gray-900 text-white" : "bg-gray-100 text-gray-900"
      )}
    >
      <header className="flex items-center justify-between p-4 border-b border-gray-700">
        <h1 className="text-2xl font-bold">Realtime Analytics</h1>
        <button
          onClick={() => setDark((d) => !d)}
          className="px-3 py-1 rounded bg-indigo-600 text-white text-sm"
        >
          {dark ? "Light" : "Dark"} Mode
        </button>
      </header>
      <main className="p-4">
        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: layout }}
          breakpoints={{ lg: 1200, md: 996, sm: 768 }}
          cols={{ lg: 12, md: 10, sm: 6 }}
          rowHeight={30}
        >
          <div
            key="submissions"
            className="widget p-2 rounded shadow bg-white dark:bg-gray-800"
          >
            <Line
              data={submissionChart}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
          <div
            key="activity"
            className="widget p-2 rounded shadow bg-white dark:bg-gray-800"
          >
            <Bar
              data={activityChart}
              options={{ responsive: true, maintainAspectRatio: false }}
            />
          </div>
        </ResponsiveGridLayout>
      </main>
    </div>
  );
}
