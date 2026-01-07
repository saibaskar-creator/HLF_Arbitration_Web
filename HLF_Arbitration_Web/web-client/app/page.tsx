"use client";

import { useState } from "react";
import UploadSection from "@/components/UploadSection";
import VerificationSplitView from "@/components/VerificationSplitView";

export default function Home() {
  const [step, setStep] = useState<"upload" | "verify">("upload");
  const [extractedData, setExtractedData] = useState<any>(null);

  const handleExtractionComplete = (data: any) => {
    setExtractedData(data);
    setStep("verify");
  };

  const handleSave = async (verifiedData: any) => {
    try {
      const response = await fetch("https://arbitration-backend-dev-919956120010.us-central1.run.app/api/save-case", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(verifiedData),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to save case");
      }

      const res = await response.json();
      alert(`✅ Success! Data saved with Contract ID: ${res.contract_id}`);
      setStep("upload"); // Reset flow
      setExtractedData(null);

    } catch (err: any) {
      alert(`❌ Error saving data: ${err.message}`);
    }
  };

  return (
    <main className="min-h-screen bg-[#f8fafc]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
              S
            </div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">
              Sai Arbitration <span className="text-blue-600">Core</span>
            </h1>
          </div>
          <div className="text-sm text-gray-500">
            v2.0 (Gemini 3.0 Powered)
          </div>
        </div>
      </header>

      {/* Content */}
      {step === "upload" && (
        <div className="py-12">
          <UploadSection onExtractionComplete={handleExtractionComplete} />
        </div>
      )}

      {step === "verify" && extractedData && (
        <VerificationSplitView
          data={extractedData}
          onSave={handleSave}
          onCancel={() => setStep("upload")}
        />
      )}
    </main>
  );
}
