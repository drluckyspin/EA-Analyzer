"use client";

import React from "react";
import { Button } from "./ui/button";
import { X, Download, ZoomIn, ZoomOut, RotateCw } from "lucide-react";

interface ImageViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageData: string; // Base64 image data
  filename?: string;
}

export const ImageViewerModal: React.FC<ImageViewerModalProps> = ({
  isOpen,
  onClose,
  imageData,
  filename = "diagram",
}) => {
  const [scale, setScale] = React.useState(1);
  const [rotation, setRotation] = React.useState(0);

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev / 1.2, 0.1));
  };

  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${imageData}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setScale(1);
    setRotation(0);
  };

  React.useEffect(() => {
    if (isOpen) {
      handleReset();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
      <div className="w-full h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-black bg-opacity-50 text-white">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">{filename}</h2>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomOut}
                className="text-white hover:bg-white hover:bg-opacity-20"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-sm min-w-[60px] text-center">
                {Math.round(scale * 100)}%
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomIn}
                className="text-white hover:bg-white hover:bg-opacity-20"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRotate}
                className="text-white hover:bg-white hover:bg-opacity-20"
              >
                <RotateCw className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDownload}
                className="text-white hover:bg-white hover:bg-opacity-20"
              >
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Image Container */}
        <div className="flex-1 flex items-center justify-center p-4 overflow-hidden">
          <div className="max-w-full max-h-full">
            <img
              src={`data:image/png;base64,${imageData}`}
              alt={filename}
              className="max-w-full max-h-full object-contain transition-transform duration-200"
              style={{
                transform: `scale(${scale}) rotate(${rotation}deg)`,
              }}
              draggable={false}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-black bg-opacity-50 text-white text-center">
          <p className="text-sm text-gray-300">
            Use mouse wheel to zoom, drag to pan, or use the controls above
          </p>
        </div>
      </div>
    </div>
  );
};
