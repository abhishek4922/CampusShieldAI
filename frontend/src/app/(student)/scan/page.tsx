"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    ShieldCheck, AlertTriangle, Info, Link2, Send,
    ChevronRight, Loader2, CheckCircle2, XCircle
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────
interface RiskSignal {
    name: string;
    triggered: boolean;
    weight: number;
    value: string;
    description: string;
}

interface ScanResult {
    scan_id: string;
    risk_score: number;
    risk_level: "Low" | "Medium" | "High";
    signals_triggered: RiskSignal[];
    plain_explanation: string;
    recommended_action: string;
    confidence: number;
    processing_ms: number;
}

// ── Risk colour map ──────────────────────────────────────────
const RISK_CONFIG = {
    Low: { cls: "risk-low", icon: CheckCircle2, bar: "#22c55e", glow: "rgba(34,197,94,0.3)" },
    Medium: { cls: "risk-medium", icon: AlertTriangle, bar: "#f59e0b", glow: "rgba(245,158,11,0.3)" },
    High: { cls: "risk-high", icon: XCircle, bar: "#ef4444", glow: "rgba(239,68,68,0.3)" },
};

// ── Risk Score Bar ───────────────────────────────────────────
function RiskBar({ score, level }: { score: number; level: string }) {
    const cfg = RISK_CONFIG[level as keyof typeof RISK_CONFIG] ?? RISK_CONFIG.Low;
    return (
        <div className="space-y-2">
            <div className="flex justify-between text-sm">
                <span className="text-slate-400">Risk Score</span>
                <span className="font-bold" style={{ color: cfg.bar }}>{score.toFixed(0)} / 100</span>
            </div>
            <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${score}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="h-full rounded-full"
                    style={{ background: cfg.bar, boxShadow: `0 0 12px ${cfg.glow}` }}
                />
            </div>
        </div>
    );
}

// ── Signal Card ──────────────────────────────────────────────
function SignalCard({ signal }: { signal: RiskSignal }) {
    const [expanded, setExpanded] = useState(false);
    return (
        <motion.div
            layout
            className="glass-card p-4 cursor-pointer select-none"
            onClick={() => setExpanded(!expanded)}
            whileHover={{ scale: 1.01 }}
        >
            <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div
                        className="w-2 h-2 rounded-full flex-shrink-0 mt-1"
                        style={{ background: signal.triggered ? "#ef4444" : "#22c55e" }}
                    />
                    <div>
                        <p className="text-sm font-semibold text-white capitalize">
                            {signal.name.replace(/_/g, " ")}
                        </p>
                        <p className="text-xs text-slate-400 font-mono">{signal.value}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs text-slate-500">weight {(signal.weight * 100).toFixed(0)}%</span>
                    <ChevronRight
                        className="w-4 h-4 text-slate-500 transition-transform"
                        style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}
                    />
                </div>
            </div>
            <AnimatePresence>
                {expanded && (
                    <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-xs text-slate-400 mt-3 leading-relaxed"
                    >
                        {signal.description}
                    </motion.p>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

// ── Main Page ────────────────────────────────────────────────
export default function ScanPage() {
    const [subject, setSubject] = useState("");
    const [body, setBody] = useState("");
    const [domain, setDomain] = useState("");
    const [links, setLinks] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ScanResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const res = await fetch("/api/v1/scans/analyze-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    email_subject: subject,
                    email_body: body,
                    sender_domain: domain,
                    links: links.split("\n").map(l => l.trim()).filter(Boolean),
                }),
            });
            if (!res.ok) throw new Error(await res.text());
            setResult(await res.json());
        } catch (err: any) {
            setError(err.message || "Analysis failed. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    const riskCfg = result ? RISK_CONFIG[result.risk_level] : null;

    return (
        <div className="min-h-screen p-6 md:p-10">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
                <div className="flex items-center gap-3 mb-2">
                    <ShieldCheck className="w-7 h-7 text-teal-400" />
                    <h1 className="section-title text-3xl">Phishing Email Analyzer</h1>
                </div>
                <p className="text-slate-400 text-sm">
                    Paste email details below. Raw content is <strong className="text-teal-400">never stored</strong> — only extracted features.
                </p>
            </motion.div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {/* Input Form */}
                <motion.form
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    onSubmit={handleSubmit}
                    className="glass-card p-8 space-y-5 h-fit"
                >
                    <div>
                        <label className="text-xs text-slate-400 uppercase tracking-wider mb-2 block">Email Subject</label>
                        <input className="cs-input" placeholder="Your account has been suspended..." value={subject} onChange={e => setSubject(e.target.value)} required />
                    </div>
                    <div>
                        <label className="text-xs text-slate-400 uppercase tracking-wider mb-2 block">Sender Domain</label>
                        <input className="cs-input" placeholder="paypal-secure.xyz" value={domain} onChange={e => setDomain(e.target.value)} required />
                    </div>
                    <div>
                        <label className="text-xs text-slate-400 uppercase tracking-wider mb-2 block">Email Body</label>
                        <textarea
                            className="cs-input min-h-[140px] resize-y"
                            placeholder="Paste the email body text here..."
                            value={body}
                            onChange={e => setBody(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <label className="text-xs text-slate-400 uppercase tracking-wider mb-2 block flex items-center gap-2">
                            <Link2 className="w-3 h-3" /> Links (one per line)
                        </label>
                        <textarea
                            className="cs-input min-h-[80px] resize-y font-mono text-xs"
                            placeholder="https://bit.ly/3xY2abc&#10;http://192.168.1.1/verify"
                            value={links}
                            onChange={e => setLinks(e.target.value)}
                        />
                    </div>
                    <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                        {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</> : <><Send className="w-4 h-4" /> Analyze Email</>}
                    </button>
                </motion.form>

                {/* Results Panel */}
                <div className="space-y-6">
                    {!result && !error && !loading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="glass-card p-10 flex flex-col items-center justify-center gap-4 text-center min-h-[300px]"
                        >
                            <ShieldCheck className="w-16 h-16 text-teal-500/40" />
                            <p className="text-slate-500 text-sm">Your analysis results will appear here.</p>
                        </motion.div>
                    )}

                    {error && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-6 border-red-500/30">
                            <div className="flex items-center gap-3 text-red-400">
                                <AlertTriangle className="w-5 h-5" />
                                <p className="text-sm font-medium">{error}</p>
                            </div>
                        </motion.div>
                    )}

                    {result && riskCfg && (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
                            {/* Risk Score Card */}
                            <div className="glass-card p-6 space-y-5">
                                <div className="flex items-center justify-between">
                                    <h2 className="font-bold text-lg">Risk Assessment</h2>
                                    <span className={`risk-badge ${riskCfg.cls}`}>
                                        {result.risk_level} Risk
                                    </span>
                                </div>
                                <RiskBar score={result.risk_score} level={result.risk_level} />
                                <div className="flex gap-4 text-xs text-slate-400">
                                    <span>Confidence: <strong className="text-white">{(result.confidence * 100).toFixed(0)}%</strong></span>
                                    <span>Processed in <strong className="text-white">{result.processing_ms}ms</strong></span>
                                </div>
                            </div>

                            {/* Plain Explanation */}
                            <div className="glass-card p-6">
                                <div className="flex items-center gap-2 mb-3">
                                    <Info className="w-4 h-4 text-teal-400" />
                                    <h3 className="font-semibold text-sm">Why was this flagged?</h3>
                                </div>
                                <p className="text-sm text-slate-300 leading-relaxed">{result.plain_explanation}</p>
                            </div>

                            {/* Recommended Action */}
                            <div className="glass-card p-6" style={{ borderColor: riskCfg.glow.replace("0.3", "0.5") }}>
                                <h3 className="font-semibold text-sm mb-2" style={{ color: riskCfg.bar }}>
                                    Recommended Action
                                </h3>
                                <p className="text-sm text-slate-300 leading-relaxed">{result.recommended_action}</p>
                            </div>

                            {/* Signals */}
                            {result.signals_triggered.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-semibold text-slate-300 mb-3">
                                        {result.signals_triggered.length} Signal{result.signals_triggered.length > 1 ? "s" : ""} Triggered
                                    </h3>
                                    <div className="space-y-3">
                                        {result.signals_triggered.map(sig => (
                                            <SignalCard key={sig.name} signal={sig} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}
                </div>
            </div>
        </div>
    );
}
