"use client";

import { useState, useEffect, useRef } from "react";
import { Calendar } from "lucide-react";

interface CustomDateInputProps {
    label: string;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
}

export default function CustomDateInput({
    label,
    value,
    onChange,
    placeholder,
}: CustomDateInputProps) {
    // value is expected to be in dd-MM-yyyy format or empty
    const [inputValue, setInputValue] = useState(value || "");
    const dateInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        setInputValue(value || "");
    }, [value]);

    // Convert dd-MM-yyyy to yyyy-MM-dd for the native date picker
    const toISODate = (dateStr: string) => {
        if (!dateStr) return "";
        const parts = dateStr.split("-");
        if (parts.length === 3) {
            const [d, m, y] = parts;
            // Basic validation to ensure we have numbers
            if (!isNaN(Number(d)) && !isNaN(Number(m)) && !isNaN(Number(y))) {
                return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
            }
        }
        return "";
    };

    // Convert yyyy-MM-dd to dd-MM-yyyy for display/storage
    const fromISODate = (isoDate: string) => {
        if (!isoDate) return "";
        const [y, m, d] = isoDate.split("-");
        return `${d}-${m}-${y}`;
    };

    const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value;
        setInputValue(newVal);
        onChange(newVal);
    };

    const handleDateSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const isoDate = e.target.value;
        const formattedDate = fromISODate(isoDate);
        setInputValue(formattedDate);
        onChange(formattedDate);
    };

    const openDatePicker = () => {
        if (dateInputRef.current) {
            dateInputRef.current.showPicker();
        }
    };

    return (
        <div className="mb-2 relative">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                {label}
            </label>
            <div className="relative flex items-center">
                <input
                    type="text"
                    value={inputValue}
                    onChange={handleTextChange}
                    placeholder={placeholder || "DD-MM-YYYY"}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10"
                />
                <button
                    type="button"
                    onClick={openDatePicker}
                    className="absolute right-2 text-gray-400 hover:text-blue-500 transition-colors"
                    title="Select date"
                    aria-label="Select date"
                >
                    <Calendar size={18} />
                </button>
            </div>

            {/* Hidden native date input for the picker functionality */}
            <input
                type="date"
                ref={dateInputRef}
                onChange={handleDateSelect}
                value={toISODate(inputValue)}
                className="absolute bottom-0 right-0 w-0 h-0 opacity-0 -z-10"
                tabIndex={-1}
                title="Date picker"
                aria-label="Date picker"
                aria-hidden="true"
            />
        </div>
    );
}
