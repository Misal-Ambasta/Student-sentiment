import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload as UploadIcon, 
  File, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Trash2,
  Eye,
  Download
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/UI/Card';
import { Button } from '../components/UI/Button';
import { Progress } from '../components/UI/Progress';
import { Badge, StatusBadge } from '../components/UI/Badge';
import { Modal, ModalFooter } from '../components/UI/Modal';
import { useUploadStore } from '../stores/useUploadStore';
import { isValidFileType, uploadFile, uploadMultipleFiles, uploadBothFiles, getUploadStatus, deleteUpload as deleteFile, getFilePreview } from '../lib/api';
import { formatFileSize, formatRelativeTime, cn } from '../lib/utils';
import toast from 'react-hot-toast';

const Upload: React.FC = () => {
  const {
    uploads,
    isDragging,
    setIsDragging,
    startUpload,
    updateUpload,
    completeUpload,
    removeUpload,
    getUploadStats
  } = useUploadStore();
  
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [filePreview, setFilePreview] = useState<{headers: string[], rows: any[]}>({headers: [], rows: []});
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileType, setFileType] = useState<'survey' | 'demographics'>('survey');
  const [multipleFiles, setMultipleFiles] = useState<{file: File, type: 'survey' | 'demographics'}[]>([]);
  const [showMultiUploadModal, setShowMultiUploadModal] = useState(false);
  const [npsFile, setNpsFile] = useState<File | null>(null);
  const [demographicsFile, setDemographicsFile] = useState<File | null>(null);
  const [showBothFilesModal, setShowBothFilesModal] = useState(false);

  const npsInputRef = React.useRef<HTMLInputElement>(null);
  const demographicsInputRef = React.useRef<HTMLInputElement>(null);

  const stats = getUploadStats();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsDragging(false);
    
    // Check if multiple files are dropped
    if (acceptedFiles.length > 1) {
      // Filter valid files
      const validFiles = acceptedFiles.filter(file => {
        // Validate file type
        if (!isValidFileType(file)) {
          toast.error(`${file.name}: Unsupported file type. Please upload CSV, XLS, or XLSX files.`);
          return false;
        }

        // Validate file size (50MB limit)
        if (file.size > 50 * 1024 * 1024) {
          toast.error(`${file.name}: File size exceeds 50MB limit.`);
          return false;
        }
        
        return true;
      });
      
      if (validFiles.length > 1) {
        // Set files for multi-upload modal
        setMultipleFiles(validFiles.map(file => ({ file, type: 'survey' })));
        setShowMultiUploadModal(true);
        return;
      }
    }
    
    // Handle single file upload
    for (const file of acceptedFiles) {
      // Validate file type
      if (!isValidFileType(file)) {
        toast.error(`${file.name}: Unsupported file type. Please upload CSV, XLS, or XLSX files.`);
        continue;
      }

      // Validate file size (50MB limit)
      if (file.size > 50 * 1024 * 1024) {
        toast.error(`${file.name}: File size exceeds 50MB limit.`);
        continue;
      }

      await uploadSingleFile(file, fileType);
    }
  }, [startUpload, updateUpload, completeUpload, setIsDragging, fileType]);

  const handleNpsFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && isValidFileType(file)) {
      setNpsFile(file);
    } else if (file) {
      toast.error('Unsupported file type. Please upload CSV, XLS, or XLSX files.');
    }
    if (e.target) e.target.value = '';
  };

  const handleDemographicsFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && isValidFileType(file)) {
      setDemographicsFile(file);
    } else if (file) {
      toast.error('Unsupported file type. Please upload CSV, XLS, or XLSX files.');
    }
    if (e.target) e.target.value = '';
  };
  
  const uploadSingleFile = async (file: File, type: 'survey' | 'demographics') => {
    const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Start upload
    startUpload({
      id: uploadId,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
      uploadedAt: new Date()
    });

    try {
      setUploading(true);
      
      // Upload file with progress tracking and file type
      const response = await isValidFileTypeuploadFile(file, type, (progress) => {
        updateUpload(uploadId, { progress });
      });

      // Update with server response
      completeUpload(uploadId, {
        status: 'processing',
        fileId: response.file_id,
        message: 'File uploaded successfully, processing...'
      });

      toast.success(`${file.name} uploaded successfully!`);

      // Poll for processing status
      pollProcessingStatus(uploadId, response.file_id);
      
      return response;
    } catch (error: any) {
      completeUpload(uploadId, {
        status: 'failed',
        error: error.message || 'Upload failed'
      });
      toast.error(`Failed to upload ${file.name}: ${error.message}`);
      throw error;
    } finally {
      setUploading(false);
    }
  };
  
  const handleMultipleFilesUpload = async () => {
    if (multipleFiles.length < 2) {
      toast.error('Please select at least two files for simultaneous upload');
      return;
    }
    
    setUploading(true);
    setShowMultiUploadModal(false);
    
    try {
      // Create upload IDs for each file
      const uploadIds = multipleFiles.map(fileData => {
        const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // Start upload
        startUpload({
          id: uploadId,
          name: fileData.file.name,
          size: fileData.file.size,
          type: fileData.file.type,
          status: 'uploading',
          progress: 0,
          uploadedAt: new Date()
        });
        
        return { uploadId, fileData };
      });
      
      // Extract files and types
      const files = multipleFiles.map(fileData => fileData.file);
      const fileTypes = multipleFiles.map(fileData => fileData.type);
      
      // Upload multiple files simultaneously
      const responses = await isValidFileTypeuploadMultipleFiles(files, fileTypes, (progress) => {
        // Update progress for all files
        uploadIds.forEach(({ uploadId }) => {
          updateUpload(uploadId, { progress });
        });
      });
      
      // Update status for each file
      responses.forEach((response, index) => {
        const { uploadId } = uploadIds[index];
        
        completeUpload(uploadId, {
          status: 'processing',
          fileId: response.file_id,
          message: 'File uploaded successfully, processing...'
        });
        
        // Poll for processing status
        pollProcessingStatus(uploadId, response.file_id);
      });
      
      toast.success(`${files.length} files uploaded successfully!`);
    } catch (error: any) {
      toast.error(`Failed to upload multiple files: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };
  
  const handleBothFilesUpload = async () => {
    if (!npsFile || !demographicsFile) {
      toast.error('Please select both NPS and demographics files');
      return;
    }
    
    setUploading(true);
    setShowBothFilesModal(false);
    
    try {
      // Create upload IDs for each file
      const npsUploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const demographicsUploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Start upload for NPS file
      startUpload({
        id: npsUploadId,
        name: npsFile.name,
        size: npsFile.size,
        type: npsFile.type,
        status: 'uploading',
        progress: 0,
        uploadedAt: new Date()
      });
      
      // Start upload for demographics file
      startUpload({
        id: demographicsUploadId,
        name: demographicsFile.name,
        size: demographicsFile.size,
        type: demographicsFile.type,
        status: 'uploading',
        progress: 0,
        uploadedAt: new Date()
      });
      
      // Upload both files simultaneously
      const responses = await uploadBothFiles(npsFile, demographicsFile, (progress) => {
        // Update progress for both files
        updateUpload(npsUploadId, { progress });
        updateUpload(demographicsUploadId, { progress });
      });
      
      // Update status for each file
      if (responses && responses.length === 2) {
        // Update NPS file status
        completeUpload(npsUploadId, {
          status: 'processing',
          fileId: responses[0].file_id,
          message: 'File uploaded successfully, processing...'
        });
        
        // Update demographics file status
        completeUpload(demographicsUploadId, {
          status: 'processing',
          fileId: responses[1].file_id,
          message: 'File uploaded successfully, processing...'
        });
        
        // Poll for processing status
        pollProcessingStatus(npsUploadId, responses[0].file_id);
        pollProcessingStatus(demographicsUploadId, responses[1].file_id);
      }
      
      toast.success('Both files uploaded successfully!');
      
      // Reset file states
      setNpsFile(null);
      setDemographicsFile(null);
    } catch (error: any) {
      toast.error(`Failed to upload files: ${error.message}`);
    } finally {
      setUploading(false);
      setMultipleFiles([]);
    }
  };

  const pollProcessingStatus = async (uploadId: string, fileId: string) => {
    const maxAttempts = 30; // 5 minutes with 10-second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await isValidFileTypegetUploadStatus(fileId);
        
        updateUpload(uploadId, {
          status: status.status,
          progress: status.progress || 100,
          message: status.message,
          error: status.error,
          headerMapping: status.headerMapping
        });

        if (status.status === 'completed') {
          toast.success('File processing completed!');
          return;
        }
        
        if (status.status === 'failed') {
          toast.error(`Processing failed: ${status.error}`);
          return;
        }

        attempts++;
        if (attempts < maxAttempts && status.status === 'processing') {
          setTimeout(poll, 10000); // Poll every 10 seconds
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    poll();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDragEnter: () => setIsDragging(true),
    onDragLeave: () => setIsDragging(false),
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: true,
    disabled: uploading
  });

  const handleDeleteFile = async (uploadId: string, fileId?: string) => {
    try {
      if (fileId) {
        await isValidFileTypedeleteFile(fileId);
      }
      removeUpload(uploadId);
      toast.success('File deleted successfully');
    } catch (error: any) {
      toast.error(`Failed to delete file: ${error.message}`);
    }
  };

  const handleViewDetails = async (upload: any) => {
    setSelectedFile(upload);
    setShowDetailsModal(true);
    
    // Fetch file preview data if file is completed or processing
    if (upload.fileId && (upload.status === 'completed' || upload.status === 'processing')) {
      setIsLoadingPreview(true);
      try {
        const previewData = await isValidFileTypegetFilePreview(upload.fileId);
        setFilePreview(previewData);
      } catch (error: any) {
        console.error('Error fetching file preview:', error);
        setFilePreview({headers: [], rows: []});
        toast.error(`Failed to load file preview: ${error.message}`);
      } finally {
        setIsLoadingPreview(false);
      }
    } else {
      setFilePreview({headers: [], rows: []});
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'processing':
      case 'uploading':
        return <Clock className="w-5 h-5 text-blue-600" />;
      default:
        return <File className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'danger';
      case 'processing':
      case 'uploading':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Upload Data
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Upload your CSV, Excel files to build your knowledge base.
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {stats.total} files • {stats.completed} completed • {stats.processing} processing
          </div>
        </div>
      </div>
      
      {/* File Type Selection */}
      <div className="flex items-center space-x-4 mb-4">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300">File Type:</div>
        <div className="flex items-center space-x-2">
          <Button 
            variant={fileType === 'survey' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFileType('survey')}
          >
            Survey Data
          </Button>
          <Button 
            variant={fileType === 'demographics' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFileType('demographics')}
          >
            Demographics Data
          </Button>
        </div>
      </div>

      {/* Upload Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Files</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
            </div>
            <File className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Processing</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.processing}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
              <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </Card>
      </div>

      {/* Upload Area */}
      <Card className="p-8">
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer",
            isDragActive || isDragging
              ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
              : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500",
            uploading && "opacity-50 cursor-not-allowed"
          )}
        >
          <input {...getInputProps()} />
          <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {isDragActive ? "Drop files here" : "Upload your data files"}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Drag and drop your CSV or Excel files here, or click to browse
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
            <span>Supported formats: CSV, XLS, XLSX</span>
            <span>•</span>
            <span>Max size: 50MB</span>
          </div>
          {!uploading && (
            <div className="flex space-x-3 justify-center mt-4">
              <Button 
                variant="secondary" 
                disabled={uploading}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowBothFilesModal(true);
                }}
              >
                Upload NPS & Demographics
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Upload History */}
      {uploads.length > 0 && (
        <Card>
          <CardHeader title="Upload History" />
          <CardContent className="p-0">
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {uploads.map((upload) => (
                <div key={upload.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      {upload.status === 'processing' && (
                        <div className="absolute right-8 top-4">
                          <Badge variant="outline" className="animate-pulse bg-yellow-50 text-yellow-700 border-yellow-300">
                            Processing: {upload.progress}%
                          </Badge>
                        </div>
                      )}
                      {getStatusIcon(upload.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {upload.name}
                        </p>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatFileSize(upload.size)}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatRelativeTime(upload.uploadedAt)}
                          </span>
                          {upload.message && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {upload.message}
                            </span>
                          )}
                        </div>
                        {(upload.status === 'uploading' || upload.status === 'processing') && (
                          <div className="mt-2">
                            <Progress 
                              value={upload.progress} 
                              size="sm" 
                              variant={upload.status === 'uploading' ? 'default' : 'warning'}
                            />
                          </div>
                        )}
                        {upload.error && (
                          <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                            {upload.error}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={getStatusVariant(upload.status)} size="sm">
                        {upload.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetails(upload)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteFile(upload.id, upload.fileId)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Multiple Files Upload Modal */}
      <Modal
        isOpen={showMultiUploadModal}
        onClose={() => setShowMultiUploadModal(false)}
        title="Upload Multiple Files"
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            You are about to upload {multipleFiles.length} files. Please select the file type for each file.
          </p>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {multipleFiles.map((fileData, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-md">
                <div className="flex items-center space-x-3">
                  <File className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{fileData.file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(fileData.file.size)}</p>
                  </div>
                </div>
                
                <select
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                  value={fileData.type}
                  onChange={(e) => {
                    const newFiles = [...multipleFiles];
                    newFiles[index].type = e.target.value as 'survey' | 'demographics';
                    setMultipleFiles(newFiles);
                  }}
                >
                  <option value="survey">Survey Data</option>
                  <option value="demographics">Demographics Data</option>
                </select>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <Button variant="outline" onClick={() => setShowMultiUploadModal(false)}>
            Cancel
          </Button>
          <Button onClick={handleMultipleFilesUpload} disabled={uploading}>
            {uploading ? 'Uploading...' : 'Upload All Files'}
          </Button>
        </div>
      </Modal>
      
      {/* NPS & Demographics Upload Modal */}
      <Modal
        isOpen={showBothFilesModal}
        onClose={() => setShowBothFilesModal(false)}
        title="Upload NPS & Demographics Files"
        size="lg"
      >
        <div className="space-y-6">
          <p className="text-gray-600 dark:text-gray-400">
            Please select both the NPS survey file and demographics file to upload them simultaneously.
          </p>
          
          {/* NPS File Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">NPS Survey File:</label>
            <div className="flex items-center space-x-2">
              <div className="flex-1 border rounded-md p-3 bg-gray-50 dark:bg-gray-800">
                {npsFile ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <File className="w-5 h-5 text-blue-500" />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{npsFile.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(npsFile.size)}</p>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setNpsFile(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">No file selected</span>
                )}
              </div>
              <input
                type="file"
                ref={npsInputRef}
                className="hidden"
                accept=".csv,.xls,.xlsx"
                onChange={handleNpsFileChange}
              />
              <Button 
                variant="outline" 
                onClick={() => npsInputRef.current?.click()}
              >
                Browse
              </Button>
            </div>
          </div>
          
          {/* Demographics File Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Demographics File:</label>
            <div className="flex items-center space-x-2">
              <div className="flex-1 border rounded-md p-3 bg-gray-50 dark:bg-gray-800">
                {demographicsFile ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <File className="w-5 h-5 text-blue-500" />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{demographicsFile.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(demographicsFile.size)}</p>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setDemographicsFile(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">No file selected</span>
                )}
              </div>
              <input
                type="file"
                ref={demographicsInputRef}
                className="hidden"
                accept=".csv,.xls,.xlsx"
                onChange={handleDemographicsFileChange}
              />
              <Button 
                variant="outline" 
                onClick={() => demographicsInputRef.current?.click()}
              >
                Browse
              </Button>
            </div>
          </div>
        </div>
        
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowBothFilesModal(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleBothFilesUpload} 
            disabled={uploading || !npsFile || !demographicsFile}
          >
            Upload Both Files
          </Button>
        </ModalFooter>
      </Modal>
      
      {/* File Details Modal */}
      <Modal
        isOpen={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        title="File Details"
        size="lg"
      >
        {selectedFile && (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              {getStatusIcon(selectedFile.status)}
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {selectedFile.name}
                </h3>
                <Badge variant={getStatusVariant(selectedFile.status)} size="sm">
                  {selectedFile.status}
                </Badge>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Size:</span>
                <span className="ml-2 text-gray-900 dark:text-white">
                  {formatFileSize(selectedFile.size)}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Type:</span>
                <span className="ml-2 text-gray-900 dark:text-white">
                  {selectedFile.type}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Uploaded:</span>
                <span className="ml-2 text-gray-900 dark:text-white">
                  {formatRelativeTime(selectedFile.uploadedAt)}
                </span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Progress:</span>
                <span className="ml-2 text-gray-900 dark:text-white">
                  {selectedFile.progress}%
                </span>
              </div>
            </div>

            {selectedFile.message && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Message:</span>
                <p className="mt-1 text-gray-900 dark:text-white">
                  {selectedFile.message}
                </p>
              </div>
            )}

            {selectedFile.error && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Error:</span>
                <p className="mt-1 text-red-600 dark:text-red-400">
                  {selectedFile.error}
                </p>
              </div>
            )}
            
            {/* File Preview */}
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">File Preview</h3>
              {isLoadingPreview ? (
                <div className="flex items-center justify-center h-40">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : filePreview.headers.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        {filePreview.headers.map((header, index) => (
                          <th 
                            key={index}
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                      {filePreview.rows.slice(0, 5).map((row, rowIndex) => (
                        <tr key={rowIndex}>
                          {Object.values(row).map((cell: any, cellIndex) => (
                            <td 
                              key={cellIndex}
                              className="px-3 py-2 text-sm text-gray-900 dark:text-gray-300 whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px]"
                            >
                              {cell?.toString() || ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="text-xs text-gray-500 mt-2">Showing first 5 rows</p>
                </div>
              ) : (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  No preview available for this file.
                </p>
              )}
            </div>
            
            {/* Header Mapping (for completed files) */}
            {selectedFile.status === 'completed' && selectedFile.headerMapping && (
              <div className="mt-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Intelligent Header Mapping</h3>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(selectedFile.headerMapping).map(([targetField, sourceField]) => (
                      <div key={targetField} className="flex items-center">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-2">{targetField}:</span>
                        <Badge variant="outline">{sourceField}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowDetailsModal(false)}>
            Close
          </Button>
          <Button 
            variant="destructive" 
            onClick={() => {
              handleDeleteFile(selectedFile.id, selectedFile.fileId);
              setShowDetailsModal(false);
            }}
          >
            Delete
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default Upload;