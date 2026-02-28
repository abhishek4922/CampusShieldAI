"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    ShieldAlert, TrendingUp, TrendingDown, AlertTriangle,
    CheckCircle2, Activity, Users, Globe
} from "lucide-react";
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

// ── Mock data for demonstration ───────────────────────────
const TREND_DATA = [
    { day: "Mon", high: 12, medium: 28, low: 45 },
    { day: "Tue", high: 8, medium: 35, low: 52 },
    { day: "Wed", high: 22, medium: 18, low: 38 },
    { day: "Thu", high: 6, medium: 42, low: 61 },
    { day: "Fri", high: 31, medium: 24, low: 29 },
    { day: "Sat", high: 4, medium: 11, low: 22 },
    { day: "Sun", high: 9, medium: 16, low: 37 },
];
const PIE_DATA = [
    { name: "Domain Mismatch", value: 38, color: "#ef4444" },
    { name: "Urgency Language", value: 27, color: "#f59e0b" },
    { name: "Suspicious TLD", value: 18, color: "#8b5cf6" },
    { name: "Payment Keywords", value: 11, color: "#06b6d4" },
    { name: "Link Anomaly", value: 6, color: "#22c55e" },
];

// ── Metric Card ──────────────────────────────────────────
function MetricCard({ label, value, change, icon: Icon, color }: any) {
    const isUp = change > 0;
    return (
        <motion.div
            className="metric-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -2 }}
        >
            <div className="flex items-start justify-between">
                <div className="p-2 rounded-xl" style={{ background: `${color}20` }}>
                    <Icon className="w-5 h-5" style={{ color }} />
                </div>
                <div className={`flex items-center gap-1 text-xs font-semibold ${isUp ? "text-red-400" : "text-green-400"}`}>
                    {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {Math.abs(change)}%
                </div>
            </div>
            <p className="metric-value mt-3">{value}</p>
            <p className="metric-label">{label}</p>
        </motion.div>
    );
}

// ── Custom Tooltip ────────────────────────────────────────
const ChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="glass-card p-3 text-xs space-y-1 min-w-[140px]">
            <p className="font-semibold text-white mb-2">{label}</p>
            {payload.map((p: any) => (
                <div key={p.name} className="flex justify-between gap-4">
                    <span className="text-slate-400 capitalize">{p.name}:</span>
                    <span style={{ color: p.color }} className="font-bold">{p.value}</span>
                </div>
            ))}
        </div>
    );
};

export default function AdminDashboard() {
    const [vulnerability, setVulnerability] = useState(0);

    useEffect(() => {
        // Animate vulnerability gauge
        const target = 34.2;
        let current = 0;
        const step = target / 60;
        const id = setInterval(() => {
            current = Math.min(current + step, target);
            setVulnerability(parseFloat(current.toFixed(1)));
            if (current >= target) clearInterval(id);
        }, 16);
        return () => clearInterval(id);
    }, []);

    return (
        <div className="min-h-screen p-6 md:p-10 space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <div className="flex items-center gap-3 mb-1">
                    <ShieldAlert className="w-7 h-7 text-teal-400" />
                    <h1 className="section-title text-3xl">Security Dashboard</h1>
                </div>
                <p className="text-slate-400 text-sm">All data is privacy-preserving (ε-differential privacy). No individual records shown.</p>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard label="Total Scans (7d)" value="1,247" change={12} icon={Activity} color="#06b6d4" />
                <MetricCard label="High Risk Detected" value="89" change={24} icon={AlertTriangle} color="#ef4444" />
                <MetricCard label="Medium Risk" value="312" change={-8} icon={ShieldAlert} color="#f59e0b" />
                <MetricCard label="Active Students" value="4,812" change={3} icon={Users} color="#22c55e" />
            </div>

            {/* Vulnerability Score */}
            <div className="glass-card p-6 flex flex-col md:flex-row items-center gap-8">
                <div className="flex-shrink-0 text-center">
                    <p className="text-xs text-slate-400 uppercase tracking-widest mb-2">Campus Vulnerability Score</p>
                    <div className="relative w-32 h-32 mx-auto">
                        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                            <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
                            <circle
                                cx="60" cy="60" r="50" fill="none"
                                stroke={vulnerability > 60 ? "#ef4444" : vulnerability > 30 ? "#f59e0b" : "#22c55e"}
                                strokeWidth="10"
                                strokeLinecap="round"
                                strokeDasharray={`${2 * Math.PI * 50}`}
                                strokeDashoffset={`${2 * Math.PI * 50 * (1 - vulnerability / 100)}`}
                                style={{ transition: "stroke-dashoffset 0.016s linear" }}
                            />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-2xl font-bold">{vulnerability}</span>
                            <span className="text-xs text-slate-400">/ 100</span>
                        </div>
                    </div>
                    <p className="text-xs text-amber-400 font-medium mt-2">Moderate Risk</p>
                </div>
                <div className="flex-1">
                    <h3 className="font-semibold text-white mb-2">What does this mean?</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">
                        A vulnerability score of <strong className="text-amber-400">{vulnerability}</strong> indicates your campus has a
                        moderate phishing exposure this week. This score is computed from DP-noised aggregate statistics —
                        no individual student data contributed to this figure.
                        <br /><br />
                        <strong className="text-white">Priority action:</strong> Focus awareness campaigns on domain-mismatch phishing,
                        which accounts for 38% of detected threats this period.
                    </p>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Trend Chart */}
                <div className="glass-card p-6 lg:col-span-2">
                    <h3 className="font-semibold text-white mb-6">Weekly Threat Trend</h3>
                    <ResponsiveContainer width="100%" height={220}>
                        <AreaChart data={TREND_DATA}>
                            <defs>
                                <linearGradient id="gradHigh" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="gradMedium" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="gradLow" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 12 }} />
                            <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
                            <Tooltip content={<ChartTooltip />} />
                            <Area type="monotone" dataKey="high" stroke="#ef4444" fill="url(#gradHigh)" strokeWidth={2} />
                            <Area type="monotone" dataKey="medium" stroke="#f59e0b" fill="url(#gradMedium)" strokeWidth={2} />
                            <Area type="monotone" dataKey="low" stroke="#22c55e" fill="url(#gradLow)" strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Threat Categories */}
                <div className="glass-card p-6">
                    <h3 className="font-semibold text-white mb-4">Top Signal Categories</h3>
                    <ResponsiveContainer width="100%" height={160}>
                        <PieChart>
                            <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={3} dataKey="value">
                                {PIE_DATA.map((entry, i) => (
                                    <Cell key={i} fill={entry.color} opacity={0.85} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(v) => [`${v}%`, "Share"]} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 space-y-2">
                        {PIE_DATA.slice(0, 3).map(d => (
                            <div key={d.name} className="flex items-center justify-between text-xs">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                                    <span className="text-slate-400">{d.name}</span>
                                </div>
                                <span className="font-semibold" style={{ color: d.color }}>{d.value}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Privacy Notice */}
            <div className="glass-card p-4 border border-teal-500/20 flex items-start gap-3">
                <CheckCircle2 className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-slate-400">
                    <strong className="text-teal-400">Privacy guarantee:</strong> All statistics above are computed with
                    ε=1.0 differential privacy (Laplace mechanism). Individual scan records, email content, and
                    identifiable data are never exposed in analytics. DP budget consumed this period: 1.0 ε.
                </p>
            </div>
        </div>
    );
}
