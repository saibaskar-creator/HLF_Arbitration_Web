"use client";

import { useState } from "react";
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react";

interface UploadSectionProps {
    onExtractionComplete: (data: any) => void;
}

export default function UploadSection({ onExtractionComplete }: UploadSectionProps) {
    const [agreementFile, setAgreementFile] = useState<File | null>(null);
    const [soaFile, setSoaFile] = useState<File | null>(null);
    const [claimFile, setClaimFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleProcess = async () => {
        if (!agreementFile || !soaFile) {
            setError("Please upload both Agreement and SOA files.");
            return;
        }

        setLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append("agreement_file", agreementFile);
        formData.append("soa_file", soaFile);
        if (claimFile) {
            formData.append("claim_file", claimFile);
        }

        try {
            const response = await fetch("http://localhost:8000/api/extract", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Failed to extract data. Please check the backend logs.");
            }

            const data = await response.json();
            onExtractionComplete(data);
        } catch (err: any) {
            setError(err.message || "An unexpected error occurred.");
        } finally {
            setLoading(false);
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
        <div className="max-w-4xl mx-auto p-6 space-y-8">
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

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            <div className="flex justify-center">
                <button
                    onClick={handleProcess}
                    disabled={loading || !agreementFile || !soaFile}
                    className={`px-8 py-3 rounded-full font-semibold text-white shadow-lg transition-all transform hover:scale-105 ${loading || !agreementFile || !soaFile
                            ? "bg-gray-400 cursor-not-allowed"
                            : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                        }`}
                >
                    {loading ? (
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
