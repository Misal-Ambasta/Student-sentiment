import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Plus, 
  MessageSquare, 
  Trash2, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  MoreVertical,
  Search,
  Sparkles,
  TrendingUp,
  Users,
  BarChart3,
  Calendar,
  Target,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';
import { Card, CardContent } from '../components/UI/Card';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { Badge } from '../components/UI/Badge';
import { Modal, ModalFooter } from '../components/UI/Modal';
import { DotsSpinner } from '../components/UI/Spinner';
import { useChatStore } from '../stores/useChatStore';
import { useAppStore } from '../stores/useAppStore';
import { getQuerySuggestions, sendChatMessage, classifyQuery } from '../lib/api';
import { formatChatTime, cn } from '../lib/utils';
import toast from 'react-hot-toast';

const Chat: React.FC = () => {
  const {
    currentSession,
    sessions,
    isLoading,
    isStreaming,
    querySuggestions,
    currentClassification,
    createSession,
    setCurrentSession,
    deleteSession,
    addMessage,
    setLoading,
    setStreaming,
    setQuerySuggestions,
    setCurrentClassification,
    clearCurrentSession
  } = useChatStore();
  
  const { theme } = useAppStore();
  const [message, setMessage] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);

  useEffect(() => {
    loadQuerySuggestions();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadQuerySuggestions = async () => {
    try {
      const suggestions = await getQuerySuggestions();
      setQuerySuggestions(suggestions);
    } catch (error) {
      console.error('Failed to load query suggestions:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');

    // Create new session if none exists
    if (!currentSession) {
      const newSessionId = createSession();
      setCurrentSession(newSessionId);
    }

    // Add user message
    const userMsg = {
      content: userMessage,
      type: 'user' as const
    };
    addMessage(currentSession?.id || '', userMsg);

    try {
      setLoading(true);
      setStreaming(true);

      // Classify query
      const classification = await classifyQuery(userMessage);
      setCurrentClassification(classification);

      // Send message to API
      const response = await sendChatMessage({
        query: userMessage,
        session_id: currentSession?.id,
        response_format: classification.query_type,
        auto_classify: "false"
      });

      // Add assistant response
      const assistantMsg = {
        content: typeof response.response === 'string' ? response.response : JSON.stringify(response.response, null, 2),
        type: 'assistant' as const,
        queryType: response.classification,
        analysisType: response.analysis_type
      };
      addMessage(currentSession?.id || '', assistantMsg);

    } catch (error: any) {
      toast.error(`Failed to send message: ${error.message}`);
      
      // Add error message
      const errorMsg = {
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        type: 'assistant' as const,
        error: 'Request failed'
      };
      addMessage(currentSession?.id || '', errorMsg);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    const newSessionId = createSession();
    setCurrentSession(newSessionId);
  };

  const handleDeleteSession = (sessionId: string) => {
    setSessionToDelete(sessionId);
    setShowDeleteModal(true);
  };

  const confirmDeleteSession = () => {
    if (sessionToDelete) {
      deleteSession(sessionToDelete);
      if (currentSession?.id === sessionToDelete) {
        clearCurrentSession();
      }
      toast.success('Chat session deleted');
    }
    setShowDeleteModal(false);
    setSessionToDelete(null);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    textareaRef.current?.focus();
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success('Message copied to clipboard');
  };

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Helper function to parse JSON from response content
  const parseJsonResponse = (content: string) => {
    try {
      // Check if content contains JSON wrapped in markdown code blocks
      const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[1]);
      }
      // Try to parse as direct JSON
      return JSON.parse(content);
    } catch {
      return null;
    }
  };

  // Structured Response Renderer Component
  const StructuredResponseRenderer: React.FC<{ data: any }> = ({ data }) => {
    if (!data || typeof data !== 'object') return null;

    const getReportIcon = (type: string) => {
      switch (type) {
        case 'weekly_report': return <Calendar className="w-5 h-5" />;
        case 'individual_analysis': return <User className="w-5 h-5" />;
        case 'segmentation_analysis': return <Users className="w-5 h-5" />;
        case 'aspect_analysis': return <BarChart3 className="w-5 h-5" />;
        default: return <TrendingUp className="w-5 h-5" />;
      }
    };

    const getReportTitle = (type: string) => {
      switch (type) {
        case 'weekly_report': return 'Weekly Report';
        case 'individual_analysis': return 'Individual Analysis';
        case 'segmentation_analysis': return 'Segmentation Analysis';
        case 'aspect_analysis': return 'Aspect Analysis';
        default: return 'Analysis Report';
      }
    };

    const formatContent = (content: string) => {
      // Split content by sections and format
      const sections = content.split('\n\n');
      return sections.map((section, index) => {
        if (section.includes('═')) {
          // Header section
          return (
            <div key={index} className="border-b border-gray-200 dark:border-gray-700 pb-3 mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {section.replace(/[═📊📈🧠📚]/g, '').trim()}
              </h3>
            </div>
          );
        } else if (section.includes('•')) {
          // Bullet points section
          const lines = section.split('\n');
          const title = lines[0];
          const bullets = lines.slice(1).filter(line => line.includes('•'));
          return (
            <div key={index} className="mb-4">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">{title}</h4>
              <ul className="space-y-1">
                {bullets.map((bullet, i) => (
                  <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{bullet.replace('•', '').trim()}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        } else {
          // Regular paragraph
          return (
            <div key={index} className="mb-3">
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {section.trim()}
              </p>
            </div>
          );
        }
      });
    };

    return (
      <Card className="w-full max-w-4xl">
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              {getReportIcon(data.type)}
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {getReportTitle(data.type)}
              </h2>
              {data.metadata?.generated_at && (
                <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3" />
                  Generated: {new Date(data.metadata.generated_at).toLocaleString()}
                </p>
              )}
            </div>
            {data.metadata?.confidence_score && (
              <Badge 
                variant={data.metadata.confidence_score > 0.8 ? 'success' : data.metadata.confidence_score > 0.6 ? 'warning' : 'danger'}
                size="sm"
              >
                {Math.round(data.metadata.confidence_score * 100)}% Confidence
              </Badge>
            )}
          </div>

          {/* Content */}
          <div className="space-y-4">
            {formatContent(data.content)}
          </div>

          {/* Metadata Footer */}
          {data.metadata && (
            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
                {data.metadata.data_sources && (
                  <div className="flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    Sources: {data.metadata.data_sources.join(', ')}
                  </div>
                )}
                {data.metadata.aspects_analyzed && (
                  <div className="flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    Aspects: {data.metadata.aspects_analyzed}
                  </div>
                )}
                {data.metadata.response_richness && (
                  <div className="flex items-center gap-1">
                    {data.metadata.response_richness === 'high' ? (
                      <CheckCircle className="w-3 h-3 text-green-500" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-yellow-500" />
                    )}
                    Richness: {data.metadata.response_richness}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const MessageBubble: React.FC<{ message: any }> = ({ message }) => {
    const isUser = message.type === 'user';
    const isError = message.error;
    const jsonData = !isUser ? parseJsonResponse(message.content) : null;

    return (
      <div className={cn(
        'flex gap-3 p-4',
        isUser ? 'justify-end' : 'justify-start'
      )}>
        {!isUser && (
          <div className="flex-shrink-0">
            <div className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center',
              isError ? 'bg-red-100 dark:bg-red-900' : 'bg-blue-100 dark:bg-blue-900'
            )}>
              <Bot className={cn(
                'w-4 h-4',
                isError ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'
              )} />
            </div>
          </div>
        )}
        
        <div className={cn(
          'max-w-4xl w-full',
          isUser ? 'order-first' : ''
        )}>
          {/* Render structured response if JSON data is available */}
          {jsonData ? (
            <div className="space-y-4">
              <StructuredResponseRenderer data={jsonData} />
              
              {/* Query Type and Analysis Type badges */}
              <div className="flex items-center gap-2">
                {message.queryType && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      Query Type:
                    </span>
                    <Badge variant="secondary" size="sm">
                      {message.queryType}
                    </Badge>
                  </div>
                )}
                
                {message.analysisType && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      Analysis Type:
                    </span>
                    <Badge variant="info" size="sm">
                      {message.analysisType}
                    </Badge>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Fallback to regular message display */
            <div className={cn(
              'rounded-lg px-4 py-2 text-sm',
              isUser 
                ? 'bg-blue-600 text-white ml-auto'
                : isError
                  ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
            )}>
              <div className="whitespace-pre-wrap">{message.content}</div>
              
              {message.queryType && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    Query Type:
                  </span>
                  <Badge variant="secondary" size="sm">
                    {message.queryType}
                  </Badge>
                </div>
              )}
              
              {message.analysisType && (
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    Analysis Type:
                  </span>
                  <Badge variant="info" size="sm">
                    {message.analysisType}
                  </Badge>
                </div>
              )}
            </div>
          )}
          
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatChatTime(message.timestamp)}
            </span>
            {!isUser && (
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopyMessage(jsonData ? JSON.stringify(jsonData, null, 2) : message.content)}
                  className="h-6 w-6 p-0"
                >
                  <Copy className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-green-600 hover:text-green-700"
                >
                  <ThumbsUp className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
                >
                  <ThumbsDown className="w-3 h-3" />
                </Button>
              </div>
            )}
          </div>
        </div>
        
        {isUser && (
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600 dark:text-gray-300" />
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-80 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Chat Sessions
            </h2>
            <Button size="sm" onClick={handleNewChat}>
              <Plus className="w-4 h-4 mr-1" />
              New Chat
            </Button>
          </div>
          
          <Input
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
        
        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          {filteredSessions.length === 0 ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No matching chats found' : 'No chat sessions yet'}
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredSessions.map((session) => (
                <div
                  key={session.id}
                  className={cn(
                    'p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors',
                    currentSession?.id === session.id && 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-blue-500'
                  )}
                  onClick={() => setCurrentSession(session.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {session.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {session.messages.length} messages • {formatChatTime(session.updatedAt)}
                      </p>
                      {session.messages.length > 0 && (
                        <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 truncate">
                          {session.messages[session.messages.length - 1].content}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(session.id);
                      }}
                      className="ml-2 h-6 w-6 p-0 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {currentSession.title}
                  </h1>
                  {currentClassification && (
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="info" size="sm">
                        {currentClassification.query_type}
                      </Badge>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        Confidence: {Math.round(currentClassification.confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
              {currentSession.messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-8">
                  <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Start a conversation
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 text-center mb-6">
                    Ask questions about your uploaded data and get intelligent responses.
                  </p>
                  
                  {/* Query Templates */}
                  <div className="w-full max-w-2xl mb-6">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Query Templates:
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      <Button
                        variant="outline"
                        className="justify-center text-center h-auto p-3"
                        onClick={() => handleSuggestionClick("Generate weekly report for current batch")}
                      >
                        <div className="flex flex-col items-center">
                          <span className="font-medium">Weekly Report</span>
                          <span className="text-xs text-gray-500 mt-1">Batch summary</span>
                        </div>
                      </Button>
                      <Button
                        variant="outline"
                        className="justify-center text-center h-auto p-3"
                        onClick={() => handleSuggestionClick("Analyze student performance trends")}
                      >
                        <div className="flex flex-col items-center">
                          <span className="font-medium">Individual Analysis</span>
                          <span className="text-xs text-gray-500 mt-1">Student insights</span>
                        </div>
                      </Button>
                      <Button
                        variant="outline"
                        className="justify-center text-center h-auto p-3"
                        onClick={() => handleSuggestionClick("Show demographic segmentation analysis")}
                      >
                        <div className="flex flex-col items-center">
                          <span className="font-medium">Segment Analysis</span>
                          <span className="text-xs text-gray-500 mt-1">Group comparisons</span>
                        </div>
                      </Button>
                    </div>
                  </div>
                  
                  {querySuggestions.length > 0 && (
                    <div className="w-full max-w-2xl">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Try asking:
                      </p>
                      <div className="grid gap-2">
                        {querySuggestions.slice(0, 3).map((suggestion, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            className="justify-start text-left h-auto p-3"
                            onClick={() => handleSuggestionClick(suggestion)}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {currentSession.messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                  {isStreaming && (
                    <div className="flex gap-3 p-4">
                      <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                        <DotsSpinner size="sm" />
                      </div>
                    </div>
                  )}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-3">
                <div className="flex-1">
                  <textarea
                    ref={textareaRef}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask a question about your data..."
                    className="w-full resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                    rows={1}
                    disabled={isLoading}
                    style={{ minHeight: '44px', maxHeight: '120px' }}
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={!message.trim() || isLoading}
                  loading={isLoading}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              
              {/* Query Templates and Suggestions */}
              <div className="mt-3">
                {/* Common Query Templates */}
                <div className="mb-2">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Query Templates:</p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleSuggestionClick("Generate weekly report for current batch")}
                      className="text-xs"
                    >
                      Weekly Report
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleSuggestionClick("Analyze student performance trends")}
                      className="text-xs"
                    >
                      Individual Analysis
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleSuggestionClick("Show demographic segmentation analysis")}
                      className="text-xs"
                    >
                      Segment Analysis
                    </Button>
                  </div>
                </div>
                
                {/* Dynamic Suggestions */}
                {querySuggestions.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Suggestions:</p>
                    <div className="flex flex-wrap gap-2">
                      {querySuggestions.slice(0, 4).map((suggestion, index) => (
                        <Button
                          key={index}
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="text-xs"
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No chat selected
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Select a chat from the sidebar or start a new conversation.
              </p>
              <Button onClick={handleNewChat}>
                <Plus className="w-4 h-4 mr-2" />
                Start New Chat
              </Button>
            </div>
          </div>
        )}
      </div>
      
      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Chat Session"
        size="sm"
      >
        <p className="text-gray-600 dark:text-gray-400">
          Are you sure you want to delete this chat session? This action cannot be undone.
        </p>
        
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDeleteSession}>
            Delete
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default Chat;