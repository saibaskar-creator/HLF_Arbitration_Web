"use client";

import { useState } from "react";
import { Save, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import CustomDateInput from "./CustomDateInput";

interface VerificationSplitViewProps {
    data: any;
    onSave: (verifiedData: any) => void;
    onCancel: () => void;
}

// Helper to safely access nested objects
const getNestedValue = (obj: any, path: string) => {
    return path.split('.').reduce((acc, part) => acc && acc[part], obj) || '';
};

// Helper to set nested objects (immutable update)
const setNestedValue = (obj: any, path: string, value: any) => {
    const newObj = JSON.parse(JSON.stringify(obj));
    const parts = path.split('.');
    let current = newObj;
    for (let i = 0; i < parts.length - 1; i++) {
        if (!current[parts[i]]) current[parts[i]] = {};
        current = current[parts[i]];
    }
    current[parts[parts.length - 1]] = value;
    return newObj;
};

// Stateless components defined outside
const SectionHeader = ({ title, id, isExpanded, onToggle }: { title: string, id: string, isExpanded: boolean, onToggle: (id: string) => void }) => (
    <div
        className="flex items-center justify-between bg-gray-100 p-3 rounded-t-lg cursor-pointer hover:bg-gray-200 transition-colors mt-6 border-b border-gray-200"
        onClick={() => onToggle(id)}
    >
        <h3 className="font-bold text-gray-700">{title}</h3>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
    </div>
);

const PureInputField = ({
    label,
    value,
    onChange,
    placeholder,
    type = "text",
    rows = 1
}: {
    label: string,
    value: string,
    onChange: (val: string) => void,
    placeholder?: string,
    type?: string,
    rows?: number
}) => {
    return (
        <div className="mb-2">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">{label}</label>
            {rows > 1 ? (
                <textarea
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder || label}
                    rows={rows}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            ) : (
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder || label}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            )}
        </div>
    );
};

export default function VerificationSplitView({
    data,
    onSave,
    onCancel,
}: VerificationSplitViewProps) {
    const [formData, setFormData] = useState(data);
    const [activeTab, setActiveTab] = useState<"agreement" | "soa" | "claim">("agreement");
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        "contract": true,
        "entities": true,
        "assets": true,
        "financials": true,
        "claim": true
    });

    const toggleSection = (section: string) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    const handleChange = (path: string, value: string) => {
        console.log(`Updating ${path} to ${value}`);
        setFormData((prev: any) => setNestedValue(prev, path, value));
    };

    // Helpers to render fields cleaner
    const field = (label: string, path: string, options: { rows?: number, type?: string, placeholder?: string } = {}) => (
        <PureInputField
            key={path}
            label={label}
            value={getNestedValue(formData, path)}
            onChange={(val) => handleChange(path, val)}
            {...options}
        />
    );

    const dateField = (label: string, path: string) => (
        <CustomDateInput
            key={path}
            label={label}
            value={getNestedValue(formData, path)}
            onChange={(val) => handleChange(path, val)}
        />
    );

    return (
        <div className="flex h-screen bg-gray-100 font-sans">
            {/* LEFT PANEL: PDF Viewer */}
            <div className="w-1/2 flex flex-col border-r border-gray-300 bg-gray-900">
                <div className="bg-gray-800 text-white p-2 flex gap-2 shadow-md z-1">
                    {["agreement", "soa", "claim"].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab as any)}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors uppercase tracking-wide
                                ${activeTab === tab ? 'bg-blue-600 text-white shadow-sm' : 'hover:bg-gray-700 text-gray-300'}`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
                <div className="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-900/50">
                    {data.file_urls && data.file_urls[activeTab] ? (
                        <div className="w-full h-full flex flex-col">
                            <div className="bg-gray-800 text-xs text-gray-400 p-1 text-center">
                                Source: {data.file_urls[activeTab]}
                            </div>
                            <iframe
                                src={`https://arbitration-backend-dev-919956120010.us-central1.run.app${data.file_urls[activeTab]}`}
                                className="flex-1 w-full h-full border-none"
                                title="PDF Viewer"
                            />
                        </div>
                    ) : (
                        <div className="text-center p-12 border-2 border-dashed border-gray-700 rounded-xl">
                            <p className="text-xl font-semibold mb-2">No File Available</p>
                            <p className="text-sm text-gray-500">The document for <span className="text-blue-400">{activeTab.toUpperCase()}</span> was not uploaded or processed.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* RIGHT PANEL: Data Verification Form */}
            <div className="w-1/2 flex flex-col bg-white">
                <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white shadow-sm z-10 sticky top-0">
                    <div>
                        <h2 className="text-xl font-bold text-gray-800">Verify Extraction</h2>
                        <p className="text-xs text-gray-500">Edit fields below to correct any AI mistakes.</p>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={onCancel} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md text-sm font-medium">Cancel</button>
                        <button onClick={() => onSave(formData)} className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-bold flex items-center gap-2 shadow-sm transition-transform active:scale-95">
                            <Save className="w-4 h-4" /> Save Case
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 pb-32 space-y-2">
                    {/* WARNINGS */}
                    {data.warnings && data.warnings.length > 0 && (
                        <div className="bg-orange-50 border-l-4 border-orange-500 p-4 mb-6 rounded-r-md">
                            <div className="flex items-center mb-2">
                                <AlertTriangle className="h-5 w-5 text-orange-500 mr-2" />
                                <h3 className="text-orange-800 font-bold">Extraction Warnings</h3>
                            </div>
                            <ul className="list-disc list-inside text-orange-700 text-sm space-y-1">
                                {data.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                            </ul>
                        </div>
                    )}

                    {/* 1. CONTRACT DETAILS */}
                    <SectionHeader title="Contract Information" id="contract" isExpanded={expandedSections["contract"]} onToggle={toggleSection} />
                    {expandedSections["contract"] && (
                        <div className="p-4 grid grid-cols-2 gap-4 border border-t-0 rounded-b-lg border-gray-200 bg-white">
                            {field("Contract Number", "contract_no")}
                            {field("Status (L/G)", "soa.contractDetails.contractStatus")}
                            {dateField("Agreement Date", "agreement.agreementInfo.agreementDate")}
                            {dateField("SOA Contract Date", "soa.contractDetails.contractDate")}
                            {field("Tenure (Months)", "soa.contractDetails.tenure")}
                            {field("Finance Rate (%)", "soa.contractDetails.financeRate")}
                        </div>
                    )}

                    {/* 2. ENTITIES */}
                    <SectionHeader title="Entities (Respondents)" id="entities" isExpanded={expandedSections["entities"]} onToggle={toggleSection} />
                    {expandedSections["entities"] && (
                        <div className="p-4 space-y-6 border border-t-0 rounded-b-lg border-gray-200 bg-white">
                            <div className="bg-blue-50 p-3 rounded-md border border-blue-100">
                                <h4 className="font-bold text-blue-800 mb-3 text-sm">Borrower</h4>
                                <div className="grid grid-cols-1 gap-3">
                                    {field("Full Name", "agreement.borrower.name")}
                                    {field("Address", "agreement.borrower.address", { rows: 2 })}
                                    {field("Communication Address (SOA)", "soa.customerInfo.communicationAddress", { rows: 2 })}
                                </div>
                            </div>

                            <div className="bg-purple-50 p-3 rounded-md border border-purple-100">
                                <h4 className="font-bold text-purple-800 mb-3 text-sm">Co-Borrower</h4>
                                <div className="grid grid-cols-1 gap-3">
                                    {field("Full Name", "agreement.coBorrower.name")}
                                    {field("Address", "agreement.coBorrower.address", { rows: 2 })}
                                </div>
                            </div>

                            <div className="bg-green-50 p-3 rounded-md border border-green-100">
                                <h4 className="font-bold text-green-800 mb-3 text-sm">Guarantor</h4>
                                <div className="grid grid-cols-1 gap-3">
                                    {field("Full Name", "agreement.guarantor.name")}
                                    {field("Address", "agreement.guarantor.address", { rows: 2 })}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 3. ASSETS */}
                    <SectionHeader title="Asset & Arbitration" id="assets" isExpanded={expandedSections["assets"]} onToggle={toggleSection} />
                    {expandedSections["assets"] && (
                        <div className="p-4 space-y-4 border border-t-0 rounded-b-lg border-gray-200 bg-white">
                            <div className="grid grid-cols-2 gap-4">
                                {field("Product Model", "soa.productInfo.productModel")}
                                {field("Vehicle No", "soa.productInfo.vehicleNo")}
                                {field("Chassis No", "soa.productInfo.chassisNo")}
                                {field("Engine No", "soa.productInfo.engineNo")}
                            </div>
                            <div className="border-t pt-4 grid grid-cols-2 gap-4">
                                {field("Arbitration Venue", "agreement.arbitration.venue")}
                                <div></div> {/* Spacer */}
                                {field("Proof Document", "agreement.vehicleProof.documentName")}
                                {dateField("Proof Date", "agreement.vehicleProof.documentDate")}
                            </div>
                        </div>
                    )}

                    {/* 4. FINANCIALS */}
                    <SectionHeader title="Financial Details" id="financials" isExpanded={expandedSections["financials"]} onToggle={toggleSection} />
                    {expandedSections["financials"] && (
                        <div className="p-4 space-y-4 border border-t-0 rounded-b-lg border-gray-200 bg-white">
                            <div className="grid grid-cols-2 gap-4">
                                {field("Loan Amount", "soa.financials.financeAmount")}
                                {field("EMI Amount", "soa.financials.emiAmount")}
                                {field("Finance Charges", "soa.financials.financeCharges")}
                                {field("Agreement Value", "soa.financials.agreementValue")}
                            </div>

                            <div className="bg-gray-50 p-3 rounded mt-2">
                                <h4 className="font-bold text-gray-700 text-xs mb-2 uppercase">Aging Analysis (SOA)</h4>
                                <div className="grid grid-cols-3 gap-3">
                                    {field("Total Overdue", "soa.agingAnalysis.totalOverdue")}
                                    {field("Current Month", "soa.agingAnalysis.currentMonth")}
                                    {field("Future Month", "soa.agingAnalysis.futureMonth")}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 5. CLAIM CALCULATION (If Available) */}
                    {data.claim && (
                        <>
                            <SectionHeader title="Claim Calculation" id="claim" isExpanded={expandedSections["claim"]} onToggle={toggleSection} />
                            {expandedSections["claim"] && (
                                <div className="p-4 space-y-4 border border-t-0 rounded-b-lg border-gray-200 bg-white">
                                    <div className="grid grid-cols-2 gap-4">
                                        {field("Total Receivable", "claim.agreementValueCalculation.totalReceivable")}
                                        {dateField("Repo Date", "claim.meta.repoDate")}
                                        {dateField("Sale Date", "claim.meta.saleDate")}
                                        {field("Sale Amount", "claim.claimCalculation.saleAmount")}
                                        {field("Paid by Borrower", "claim.claimCalculation.paidByBorrower")}
                                        {field("Final Claim Amount", "claim.claimCalculation.finalClaimAmount")}
                                    </div>
                                    <div className="bg-red-50 p-3 rounded border border-red-100 mt-2">
                                        <h4 className="font-bold text-red-800 text-xs mb-2 uppercase">Charges</h4>
                                        <div className="grid grid-cols-2 gap-3">
                                            {field("Cheque Return Charges", "claim.claimCalculation.chequeReturnCharges")}
                                            {field("Repo Charges", "claim.claimCalculation.repoCharges")}
                                            {field("Legal Charges", "claim.claimCalculation.legalCharges")}
                                            {field("Additional Interest", "claim.claimCalculation.additionalInterest")}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
