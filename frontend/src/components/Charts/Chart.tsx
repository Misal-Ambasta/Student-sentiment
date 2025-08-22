import React from 'react';
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
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut, Pie } from 'react-chartjs-2';
import { cn } from '../../lib/utils';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface ChartContainerProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  height?: number;
}

interface ChartData {
  labels: string[];
  datasets: any[];
}

interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: any;
  scales?: any;
  [key: string]: any;
}

interface BaseChartProps {
  data: ChartData;
  options?: ChartOptions;
  className?: string;
  height?: number;
}

// Chart Container Component
export const ChartContainer: React.FC<ChartContainerProps> = ({
  children,
  title,
  className,
  height = 300
}) => {
  return (
    <div className={cn('bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 p-6 hover:shadow-xl transition-all duration-300', className)}>
      {title && (
        <h3 className="text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent mb-6">
          {title}
        </h3>
      )}
      <div style={{ height: `${height}px` }} className="relative">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 to-purple-50/30 rounded-xl -z-10" />
        {children}
      </div>
    </div>
  );
};

// Default chart options
const defaultOptions: ChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
          size: 12,
          weight: '500',
        },
        color: '#374151',
      },
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: 'white',
      bodyColor: 'white',
      borderColor: 'rgba(255, 255, 255, 0.2)',
      borderWidth: 1,
      cornerRadius: 12,
      displayColors: true,
      padding: 16,
      titleFont: {
        size: 14,
        weight: '600',
      },
      bodyFont: {
        size: 13,
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        font: {
          size: 11,
          weight: '500',
        },
        color: '#6B7280',
      },
    },
    y: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
        lineWidth: 1,
      },
      ticks: {
        font: {
          size: 11,
          weight: '500',
        },
        color: '#6B7280',
      },
    },
  },
};

// Line Chart Component
export const LineChart: React.FC<BaseChartProps> = ({ data, options, className, height }) => {
  const mergedOptions = {
    ...defaultOptions,
    ...options,
  };

  return (
    <div className={cn('w-full relative', className)} style={{ height: height ? `${height}px` : undefined }}>
      <Line data={data} options={mergedOptions} />
    </div>
  );
};

// Bar Chart Component
export const BarChart: React.FC<BaseChartProps> = ({ data, options, className, height }) => {
  const mergedOptions = {
    ...defaultOptions,
    ...options,
  };

  return (
    <div className={cn('w-full relative', className)} style={{ height: height ? `${height}px` : undefined }}>
      <Bar data={data} options={mergedOptions} />
    </div>
  );
};

// Doughnut Chart Component
export const DoughnutChart: React.FC<BaseChartProps> = ({ data, options, className, height }) => {
  const doughnutOptions = {
    ...defaultOptions,
    scales: undefined, // Remove scales for doughnut charts
    plugins: {
      ...defaultOptions.plugins,
      legend: {
        ...defaultOptions.plugins?.legend,
        position: 'bottom' as const,
      },
    },
    ...options,
  };

  return (
    <div className={cn('w-full flex justify-center items-center relative', className)} style={{ height: height ? `${height}px` : undefined }}>
      <Doughnut data={data} options={doughnutOptions} />
    </div>
  );
};

// Pie Chart Component
export const PieChart: React.FC<BaseChartProps> = ({ data, options, className, height }) => {
  const pieOptions = {
    ...defaultOptions,
    scales: undefined, // Remove scales for pie charts
    plugins: {
      ...defaultOptions.plugins,
      legend: {
        ...defaultOptions.plugins?.legend,
        position: 'bottom' as const,
      },
    },
    ...options,
  };

  return (
    <div className={cn('w-full flex justify-center items-center relative', className)} style={{ height: height ? `${height}px` : undefined }}>
      <Pie data={data} options={pieOptions} />
    </div>
  );
};