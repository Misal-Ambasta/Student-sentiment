import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  FileText, 
  MessageSquare, 
  TrendingUp, 
  Users, 
  Database,
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
  Upload,
  MessageCircle,
  Bell
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/UI/Card';
import { Badge, StatusBadge } from '../components/UI/Badge';
import { Progress } from '../components/UI/Progress';
import { Button } from '../components/UI/Button';
import { LineChart, BarChart, DoughnutChart, ChartContainer } from '../components/Charts';
import { useAppStore } from '../stores/useAppStore';
import { useUploadStore, getUploadStats } from '../stores/useUploadStore';
import { useChatStore } from '../stores/useChatStore';
import { api } from '../lib/api';
import { formatNumber, formatFileSize, formatRelativeTime } from '../lib/utils';
import { useNavigate } from 'react-router-dom';

interface DashboardStats {
  totalFiles: number;
  totalSize: number;
  totalChats: number;
  totalQueries: number;
  processingFiles: number;
  completedFiles: number;
  failedFiles: number;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  activeConnections: number;
}

interface Alert {
  id: string;
  type: 'warning' | 'danger' | 'info';
  message: string;
  timestamp: Date;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { theme, systemHealth, lastHealthCheck, setWebSocketMessage } = useAppStore();
  const { uploads } = useUploadStore();
  const { sessions } = useChatStore();
  const [stats, setStats] = useState<DashboardStats>({
    totalFiles: 0,
    totalSize: 0,
    totalChats: 0,
    totalQueries: 0,
    processingFiles: 0,
    completedFiles: 0,
    failedFiles: 0
  });
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    activeConnections: 0
  });
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [npsData, setNpsData] = useState({
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
    datasets: [
      {
        label: 'NPS Score',
        data: [42, 45, 48, 46, 52, 58],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true
      },
      {
        label: 'Industry Average',
        data: [40, 41, 42, 42, 43, 44],
        borderColor: 'rgb(209, 213, 219)',
        backgroundColor: 'rgba(209, 213, 219, 0.1)',
        borderDash: [5, 5],
        fill: false
      }
    ]
  });

  const isDark = theme === 'dark';
  const uploadStats = getUploadStats(Array.from(uploads.values()));

  useEffect(() => {
    loadDashboardData();
    setupWebSocketListeners();
    
    // Mock alerts for demonstration
    setAlerts([
      {
        id: '1',
        type: 'warning',
        message: 'Course A satisfaction dropped 15% this week',
        timestamp: new Date(Date.now() - 1000 * 60 * 30) // 30 minutes ago
      },
      {
        id: '2',
        type: 'danger',
        message: 'Critical: 3 students at risk in Course B',
        timestamp: new Date(Date.now() - 1000 * 60 * 5) // 5 minutes ago
      },
      {
        id: '3',
        type: 'info',
        message: 'New demographic data available for analysis',
        timestamp: new Date(Date.now() - 1000 * 60 * 120) // 2 hours ago
      }
    ]);
    
    return () => {
      // Cleanup WebSocket listeners
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Calculate stats from stores
      const totalQueries = sessions.reduce((sum, session) => sum + session.messages.length, 0);
      const totalSize = uploads.reduce((sum, upload) => sum + (upload.size || 0), 0);
      
      setStats({
        totalFiles: uploads.length,
        totalSize,
        totalChats: sessions.length,
        totalQueries,
        processingFiles: uploadStats.processing,
        completedFiles: uploadStats.completed,
        failedFiles: uploadStats.failed
      });

      // Mock system metrics (in real app, this would come from backend)
      setSystemMetrics({
        cpuUsage: Math.random() * 100,
        memoryUsage: Math.random() * 100,
        diskUsage: Math.random() * 100,
        activeConnections: Math.floor(Math.random() * 50)
      });
      
      // In a real app, we would fetch NPS data from the API
      // api.getNPSTrends().then(data => setNpsData(data));
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const setupWebSocketListeners = () => {
    // Setup WebSocket listeners for real-time updates
    const handleWebSocketMessage = (event: any) => {
      const data = JSON.parse(event.data);
      
      // Handle different event types
      if (data.event_type === 'aspect_specific_alert') {
        // Add new alert
        setAlerts(prev => [{
          id: Date.now().toString(),
          type: data.data.severity || 'info',
          message: data.data.message,
          timestamp: new Date()
        }, ...prev].slice(0, 10)); // Keep only 10 most recent alerts
      }
      
      // Update app store with the message for other components
      setWebSocketMessage(data);
    };
    
    // In a real app, we would connect to the WebSocket here
    // api.webSocketManager.subscribe('dashboard', handleWebSocketMessage);
  };

  // Chart data
  const uploadTrendData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Files Uploaded',
        data: [12, 19, 8, 15, 22, 18, 25],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true
      }
    ]
  };
  
  // Navigation handlers
  const navigateToUpload = () => navigate('/upload');
  const navigateToChat = () => navigate('/chat');

  const fileTypeData = {
    labels: ['CSV', 'Excel', 'PDF', 'Text'],
    datasets: [
      {
        data: [45, 30, 15, 10],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)'
        ],
        borderWidth: 0
      }
    ]
  };

  const queryVolumeData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    datasets: [
      {
        label: 'Queries',
        data: [5, 2, 15, 25, 20, 12],
        backgroundColor: 'rgba(16, 185, 129, 0.8)'
      }
    ]
  };

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    change?: string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, change, icon, color }) => (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
            {value}
          </p>
          {change && (
            <p className="text-sm text-green-600 dark:text-green-400 mt-1">
              {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Welcome back! Here's what's happening with your RAG system.
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <StatusBadge status={systemHealth === 'healthy' ? 'online' : 'offline'} />
          {lastHealthCheck && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Last check: {formatRelativeTime(lastHealthCheck)}
            </span>
          )}
        </div>
      </div>
      
      {/* Quick Navigation */}
      <div className="flex space-x-4">
        <Button 
          onClick={navigateToUpload}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Data</span>
        </Button>
        <Button 
          onClick={navigateToChat}
          className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700"
        >
          <MessageCircle className="w-4 h-4" />
          <span>Chat Assistant</span>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Files"
          value={formatNumber(stats.totalFiles)}
          change="+12% from last week"
          icon={<FileText className="w-6 h-6 text-white" />}
          color="bg-blue-500"
        />
        <StatCard
          title="Storage Used"
          value={formatFileSize(stats.totalSize)}
          change="+8% from last week"
          icon={<Database className="w-6 h-6 text-white" />}
          color="bg-green-500"
        />
        <StatCard
          title="Chat Sessions"
          value={formatNumber(stats.totalChats)}
          change="+23% from last week"
          icon={<MessageSquare className="w-6 h-6 text-white" />}
          color="bg-purple-500"
        />
        <StatCard
          title="Total Queries"
          value={formatNumber(stats.totalQueries)}
          change="+15% from last week"
          icon={<TrendingUp className="w-6 h-6 text-white" />}
          color="bg-orange-500"
        />
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <CardHeader title="System Performance" className="pb-4" />
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  CPU Usage
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {systemMetrics.cpuUsage.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={systemMetrics.cpuUsage} 
                variant={systemMetrics.cpuUsage > 80 ? 'danger' : 'default'}
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Memory Usage
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {systemMetrics.memoryUsage.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={systemMetrics.memoryUsage} 
                variant={systemMetrics.memoryUsage > 80 ? 'warning' : 'default'}
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Disk Usage
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {systemMetrics.diskUsage.toFixed(1)}%
                </span>
              </div>
              <Progress 
                value={systemMetrics.diskUsage} 
                variant={systemMetrics.diskUsage > 90 ? 'danger' : 'success'}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="p-6">
          <CardHeader title="File Processing Status" className="pb-4" />
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  Completed
                </span>
              </div>
              <Badge variant="success">{stats.completedFiles}</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <Clock className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Processing
                </span>
              </div>
              <Badge variant="info">{stats.processingFiles}</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span className="text-sm font-medium text-red-800 dark:text-red-200">
                  Failed
                </span>
              </div>
              <Badge variant="danger">{stats.failedFiles}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer title="NPS Trends" subtitle="Weekly NPS scores compared to industry average">
          <LineChart data={npsData} isDark={isDark} height={300} />
        </ChartContainer>

        <ChartContainer title="File Types" subtitle="Distribution of uploaded file types">
          <DoughnutChart data={fileTypeData} isDark={isDark} height={300} />
        </ChartContainer>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartContainer title="Upload Trends" subtitle="Files uploaded over the last 7 days">
          <LineChart data={uploadTrendData} isDark={isDark} height={300} />
        </ChartContainer>
        
        <ChartContainer title="Query Volume" subtitle="Queries processed throughout the day">
          <BarChart data={queryVolumeData} isDark={isDark} height={300} />
        </ChartContainer>
      </div>
      
      {/* Critical Alerts */}
      <Card className="p-6">
        <CardHeader title="Critical Alerts" className="pb-4" />
        <CardContent className="space-y-4">
          {alerts.length > 0 ? (
            alerts.map(alert => (
              <div 
                key={alert.id}
                className={`flex items-center justify-between p-3 rounded-lg ${alert.type === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20' : 
                  alert.type === 'danger' ? 'bg-red-50 dark:bg-red-900/20' : 
                  'bg-blue-50 dark:bg-blue-900/20'}`}
              >
                <div className="flex items-center space-x-3">
                  <Bell className={`w-5 h-5 ${alert.type === 'warning' ? 'text-yellow-600' : 
                    alert.type === 'danger' ? 'text-red-600' : 
                    'text-blue-600'}`} />
                  <span className={`text-sm font-medium ${alert.type === 'warning' ? 'text-yellow-800 dark:text-yellow-200' : 
                    alert.type === 'danger' ? 'text-red-800 dark:text-red-200' : 
                    'text-blue-800 dark:text-blue-200'}`}>
                    {alert.message}
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatRelativeTime(alert.timestamp)}
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-gray-500 dark:text-gray-400">
              No critical alerts at this time
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;