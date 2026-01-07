"use client";

import { useState, useEffect } from "react";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";

// 👇 HARDCODED URL (We will switch to Env Vars later)
const API_URL = "https://arbitration-backend-dev-919956120010.us-central1.run.app";

interface UploadSectionProps {
    onExtractionComplete: (data: any) => void;
}

export default function UploadSection({ onExtractionComplete }: UploadSectionProps) {
    const [agreementFile, setAgreementFile] = useState<File | null>(null);
    const [soaFile, setSoaFile] = useState<File | null>(null);
    const [claimFile, setClaimFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [statusMessage, setStatusMessage] = useState("");
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 1. Health Check on Load 🟢
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch(API_URL); // Hits the root "/" endpoint
                if (res.ok) {
                    setIsConnected(true);
                    setStatusMessage("✅ Connected to Arbitration Server. Ready.");
                }
            } catch (err) {
                console.error("Backend not reachable:", err);
                setIsConnected(false);
                setStatusMessage("⚠️ Server waking up... please wait 10s.");
            }
        };
        checkHealth();
    }, []);

    const handleProcess = async () => {
        if (!agreementFile || !soaFile) {
            setError("Please upload both Agreement and SOA files.");
            return;
        }

        setIsUploading(true);
        setError(null);
        // 2. Upload Status 🚀
        setStatusMessage("🚀 Uploading documents to server...");

        const formData = new FormData();
        formData.append("agreement_file", agreementFile);
        formData.append("soa_file", soaFile);
        if (claimFile) {
            formData.append("claim_file", claimFile);
        }

        try {
            // 3. Processing Status 🧠
            // We set a timeout message because cold starts can take time
            const processingTimer = setTimeout(() => {
                setStatusMessage("🧠 Gemini is reading the contract... (This might take 45s)");
            }, 2000);

            const response = await fetch(`${API_URL}/api/extract`, {
                method: "POST",
                body: formData,
            });

            clearTimeout(processingTimer);

            if (!response.ok) {
                // Try to read the error details from the backend
                const errText = await response.text();
                throw new Error(errText || "Failed to extract data. Please check the backend logs.");
            }

            const data = await response.json();

            // 4. Success Status ✅
            setStatusMessage("✅ Extraction complete! Loading verification view...");

            // Short delay so user sees the success message
            setTimeout(() => {
                onExtractionComplete(data);
            }, 1000);

        } catch (err: any) {
            console.error(err);
            setError(err.message || "An unexpected error occurred.");
            setStatusMessage(`❌ Error: ${err.message.substring(0, 100)}...`);
            // alert(`Failed to extract data.\n\nServer said: ${err.message}`);
        } finally {
            setIsUploading(false);
        }
    };

    const FileInput = ({
        label,
        file,
        setFile,
        required = false,
    }: {
        label: string;
        file: File | null;
        setFile: (f: File | null) => void;
        required?: boolean;
    }) => (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors bg-white/5 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-2">
                {file ? (
                    <>
                        <CheckCircle className="w-10 h-10 text-green-500" />
                        <span className="font-medium text-gray-700">{file.name}</span>
                        <button
                            onClick={() => setFile(null)}
                            className="text-xs text-red-500 hover:underline"
                        >
                            Remove
                        </button>
                    </>
                ) : (
                    <>
                        <Upload className="w-10 h-10 text-gray-400" />
                        <label className="cursor-pointer block">
                            <span className="font-medium text-blue-600 hover:text-blue-500">
                                Upload {label}
                            </span>
                            <input
                                type="file"
                                className="hidden"
                                accept=".pdf"
                                onChange={(e) => {
                                    if (e.target.files?.[0]) setFile(e.target.files[0]);
                                }}
                            />
                        </label>
                        <span className="text-sm text-gray-500">
                            {required ? "(Required)" : "(Optional)"}
                        </span>
                    </>
                )}
            </div>
        </div>
    );

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8 bg-white rounded-xl shadow-sm border border-gray-200">
            {/* Connection Badge */}
            <div className="flex justify-end mb-4">
                <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${isConnected ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                    }`}>
                    {isConnected ? "🟢 System Online" : "🟠 Connecting..."}
                </span>
            </div>

            <div className="text-center">
                <h2 className="text-3xl font-bold text-gray-800">1. Upload Documents</h2>
                <p className="text-gray-600">
                    Upload the required PDF files to start the extraction process.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <FileInput
                    label="Agreement"
                    file={agreementFile}
                    setFile={setAgreementFile}
                    required={true}
                />
                <FileInput
                    label="SOA"
                    file={soaFile}
                    setFile={setSoaFile}
                    required={true}
                />
                <FileInput
                    label="Claim Statement"
                    file={claimFile}
                    setFile={setClaimFile}
                />
            </div>

            {/* 📢 The Smart Status Bar */}
            <div className={`text-center text-sm font-medium py-2 rounded-md transition-all ${statusMessage.includes("❌") ? "bg-red-50 text-red-700" :
                    statusMessage.includes("✅") ? "bg-green-50 text-green-700" :
                        statusMessage.includes("🚀") || statusMessage.includes("🧠") ? "bg-blue-50 text-blue-700 animate-pulse" :
                            "text-gray-500"
                }`}>
                {statusMessage || "Waiting for upload..."}
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            <div className="flex justify-center">
                <button
                    onClick={handleProcess}
                    disabled={isUploading || !agreementFile || !soaFile}
                    className={`px-8 py-3 rounded-full font-semibold text-white shadow-lg transition-all transform hover:scale-105 ${isUploading || !agreementFile || !soaFile
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                        }`}
                >
                    {isUploading ? (
                        <span className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            Processing...
                        </span>
                    ) : (
                        "Start Extraction"
                    )}
                </button>
            </div>
        </div>
    );
}
