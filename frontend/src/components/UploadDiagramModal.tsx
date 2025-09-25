"use client";

import React, { useState, useCallback, useEffect } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import {
  X,
  Upload,
  FileImage,
  CheckCircle,
  AlertCircle,
  Loader2,
  Plus,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface UploadDiagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface UploadProgress {
  step: string;
  progress: number;
  message: string;
  completed: boolean;
  error?: string;
}

export const UploadDiagramModal: React.FC<UploadDiagramModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Ensure component is mounted on client side to avoid hydration issues
  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";

    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    if (i === 0) {
      return `${bytes} B`;
    } else if (i === 1) {
      return `${(bytes / k).toFixed(1)} KB`;
    } else if (i === 2) {
      return `${(bytes / (k * k)).toFixed(1)} MB`;
    } else {
      return `${(bytes / (k * k * k)).toFixed(1)} GB`;
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      const droppedFile = droppedFiles[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        setError(null);
      }
    }
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile && validateFile(selectedFile)) {
        setFile(selectedFile);
        setError(null);
      }
    },
    []
  );

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      "application/pdf",
      "image/png",
      "image/jpeg",
      "image/jpg",
    ];

    if (!allowedTypes.includes(file.type)) {
      setError(
        `Unsupported file type: ${file.type}. Please upload a PDF, PNG, or JPG file.`
      );
      return false;
    }

    const maxSize = 20 * 1024 * 1024; // 20MB
    if (file.size > maxSize) {
      setError(
        `File too large: ${(file.size / 1024 / 1024).toFixed(
          1
        )}MB. Maximum size: 20MB`
      );
      return false;
    }

    return true;
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setUploadProgress({
      step: "upload",
      progress: 0,
      message: "Uploading file...",
      completed: false,
    });

    try {
      // Step 1: Upload file
      setUploadProgress({
        step: "upload",
        progress: 25,
        message: "Uploading file...",
        completed: false,
      });

      const uploadResponse = await apiClient.uploadDiagram(file);

      setUploadProgress({
        step: "analyze",
        progress: 50,
        message: "Analyzing with LLM...",
        completed: false,
      });

      // Step 2: Analyze with LLM
      const analysisResponse = await apiClient.analyzeDiagram(
        uploadResponse.upload_id
      );

      if (!analysisResponse.success) {
        throw new Error(analysisResponse.error || "Analysis failed");
      }

      setUploadProgress({
        step: "store",
        progress: 75,
        message: "Storing in database...",
        completed: false,
      });

      // Step 3: Store in database
      const storageResponse = await apiClient.storeDiagram(
        uploadResponse.upload_id,
        analysisResponse.diagram_data
      );

      if (!storageResponse.success) {
        throw new Error(storageResponse.error || "Storage failed");
      }

      setUploadProgress({
        step: "complete",
        progress: 100,
        message: "Analysis complete!",
        completed: true,
      });

      // Success - close modal and refresh library
      setTimeout(() => {
        onSuccess();
        onClose();
        resetModal();
      }, 1500);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed";
      setError(errorMessage);
      setUploadProgress({
        step: "error",
        progress: 0,
        message: "Upload failed",
        completed: false,
        error: errorMessage,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const resetModal = () => {
    setFile(null);
    setUploadProgress(null);
    setError(null);
    setIsUploading(false);
  };

  const handleClose = () => {
    if (!isUploading) {
      resetModal();
      onClose();
    }
  };

  // Don't render until mounted to avoid hydration issues
  if (!isMounted || !isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900 bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-slate-600 flex items-center justify-center">
              <Plus className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Add New Diagram
              </h2>
              <p className="text-sm text-slate-600">
                Upload and analyze electrical diagrams
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            disabled={isUploading}
            className="h-8 w-8 p-0 hover:bg-slate-200"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex h-[500px]">
          {/* Left Column - File Upload */}
          <div className="flex-1 p-6 border-r border-slate-200 bg-slate-50">
            <div className="h-full flex flex-col">
              <div className="flex items-center gap-2 mb-6">
                <div className="h-6 w-6 rounded bg-slate-600 flex items-center justify-center">
                  <Upload className="h-3 w-3 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">
                  Upload Diagram
                </h3>
              </div>

              {/* Drop Zone */}
              <div
                className={`flex-1 border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                  isDragOver
                    ? "border-slate-400 bg-slate-100 scale-[1.02]"
                    : file
                    ? "border-slate-500 bg-slate-100"
                    : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {file ? (
                  <div
                    className="flex flex-col items-center"
                    style={{ paddingTop: "48px" }}
                  >
                    <div className="h-16 w-16 rounded-full bg-slate-600 flex items-center justify-center mb-4">
                      <CheckCircle className="h-8 w-8 text-white" />
                    </div>
                    <p className="text-lg font-semibold text-slate-900 mb-2">
                      {file.name}
                    </p>
                    <p className="text-sm text-slate-600 mb-4 bg-slate-200 px-3 py-1 rounded-full">
                      {formatFileSize(file.size)}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setFile(null)}
                      disabled={isUploading}
                      className="border-slate-300 text-slate-700 hover:bg-slate-100"
                    >
                      Remove File
                    </Button>
                  </div>
                ) : (
                  <div
                    className="flex flex-col items-center"
                    style={{ paddingTop: "48px" }}
                  >
                    <div className="h-16 w-16 rounded-full bg-slate-200 flex items-center justify-center mb-4">
                      <Upload className="h-8 w-8 text-slate-600" />
                    </div>
                    <p className="text-lg font-semibold text-slate-900 mb-2">
                      Drop your diagram here
                    </p>
                    <p className="text-sm text-slate-600 mb-4">
                      or click to browse files
                    </p>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="file-upload"
                      disabled={isUploading}
                    />
                    <label htmlFor="file-upload">
                      <Button
                        variant="outline"
                        asChild
                        disabled={isUploading}
                        className="border-slate-300 text-slate-700 hover:bg-slate-100"
                      >
                        <span>Choose File</span>
                      </Button>
                    </label>
                    <p className="text-xs text-slate-500 mt-4 bg-slate-100 px-3 py-1 rounded-full">
                      Supports PDF, PNG, JPG up to 20MB
                    </p>
                  </div>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center">
                    <div className="h-6 w-6 rounded-full bg-red-100 flex items-center justify-center mr-3">
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    </div>
                    <p className="text-sm text-red-700 font-medium">{error}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Progress */}
          <div className="flex-1 p-6 bg-white">
            <div className="h-full flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-6 w-6 rounded bg-slate-600 flex items-center justify-center">
                  <FileImage className="h-3 w-3 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">
                  Analysis Progress
                </h3>
              </div>

              <div className="flex-1 flex flex-col justify-center">
                {!uploadProgress ? (
                  <div className="text-center text-slate-500">
                    <div className="h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
                      <FileImage className="h-8 w-8 text-slate-400" />
                    </div>
                    <p className="text-slate-600 font-medium">
                      Upload a file to begin analysis
                    </p>
                    <p className="text-sm text-slate-500 mt-1">
                      Progress will appear here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Progress Steps */}
                    <div className="space-y-4">
                      {/* Upload Step */}
                      <div className="flex items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            uploadProgress.step === "upload" &&
                            !uploadProgress.completed
                              ? "bg-blue-100"
                              : uploadProgress.step === "error"
                              ? "bg-red-100"
                              : "bg-green-100"
                          }`}
                        >
                          {uploadProgress.step === "upload" &&
                          !uploadProgress.completed ? (
                            <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                          ) : uploadProgress.step === "error" ? (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          ) : (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            Upload File
                          </p>
                          <p className="text-xs text-gray-500">
                            Validating and storing file
                          </p>
                        </div>
                      </div>

                      {/* Analyze Step */}
                      <div className="flex items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            uploadProgress.step === "analyze" &&
                            !uploadProgress.completed
                              ? "bg-blue-100"
                              : uploadProgress.step === "error"
                              ? "bg-red-100"
                              : uploadProgress.step === "store" ||
                                uploadProgress.step === "complete"
                              ? "bg-green-100"
                              : "bg-gray-100"
                          }`}
                        >
                          {uploadProgress.step === "analyze" &&
                          !uploadProgress.completed ? (
                            <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                          ) : uploadProgress.step === "error" ? (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          ) : uploadProgress.step === "store" ||
                            uploadProgress.step === "complete" ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <div className="w-4 h-4 bg-gray-300 rounded-full" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            LLM Analysis
                          </p>
                          <p className="text-xs text-gray-500">
                            Extracting diagram structure
                          </p>
                        </div>
                      </div>

                      {/* Store Step */}
                      <div className="flex items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            uploadProgress.step === "store" &&
                            !uploadProgress.completed
                              ? "bg-blue-100"
                              : uploadProgress.step === "error"
                              ? "bg-red-100"
                              : uploadProgress.step === "complete"
                              ? "bg-green-100"
                              : "bg-gray-100"
                          }`}
                        >
                          {uploadProgress.step === "store" &&
                          !uploadProgress.completed ? (
                            <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                          ) : uploadProgress.step === "error" ? (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          ) : uploadProgress.step === "complete" ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <div className="w-4 h-4 bg-gray-300 rounded-full" />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            Store in Database
                          </p>
                          <p className="text-xs text-gray-500">
                            Saving to Neo4j
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-slate-600 to-slate-700 h-3 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${uploadProgress.progress}%` }}
                      />
                    </div>

                    {/* Current Status */}
                    <div className="text-center">
                      <p className="text-sm font-semibold text-slate-900">
                        {uploadProgress.message}
                      </p>
                      {uploadProgress.error && (
                        <p className="text-sm text-red-600 mt-1 font-medium">
                          {uploadProgress.error}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-200 bg-slate-50">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isUploading}
            className="border-slate-300 text-slate-700 hover:bg-slate-100"
          >
            Cancel
          </Button>
          <Button
            onClick={handleAnalyze}
            disabled={!file || isUploading}
            className="min-w-[100px] bg-slate-600 hover:bg-slate-700 text-white"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              "Analyze"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
