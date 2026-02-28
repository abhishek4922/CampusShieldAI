"use client";

import { motion } from "framer-motion";
import { Shield, ArrowRight, Zap, Eye, Lock, BookOpen } from "lucide-react";
import Link from "next/link";

const FEATURES = [
    { icon: Eye, title: "Explainable AI", desc: "Every alert shows exactly why it was flagged — no black boxes." },
    { icon: Lock, title: "Privacy-First", desc: "Differential privacy on all analytics. Raw email content never stored." },
    { icon: Zap, title: "Instant Analysis", desc: "Sub-second phishing detection powered by AMD-optimized inference." },
    { icon: BookOpen, title: "Hygiene Companion", desc: "Gamified micro-lessons that build lasting cybersecurity habits." },
];

export default function LandingPage() {
    return (
        <div className="min-h-screen flex flex-col">
            {/* Nav */}
            <nav className="flex items-center justify-between px-8 py-5 border-b border-white/5">
                <div className="flex items-center gap-2.5">
                    <Shield className="w-6 h-6 text-teal-400" />
                    <span className="font-bold text-lg tracking-tight">CampusShield <span className="text-teal-400">AI</span></span>
                </div>
                <div className="flex items-center gap-4">
                    <Link href="/login" className="text-sm text-slate-400 hover:text-white transition-colors">Sign In</Link>
                    <Link href="/login" className="btn-primary text-sm py-2">Get Started</Link>
                </div>
            </nav>

            {/* Hero */}
            <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-24 relative">
                {/* Background glow */}
                <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 50% 40%, rgba(6,182,212,0.08) 0%, transparent 60%)" }} />

                <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="relative max-w-3xl">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-6" style={{ background: "rgba(6,182,212,0.1)", border: "1px solid rgba(6,182,212,0.3)", color: "#06b6d4" }}>
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                        Now serving 15,000+ students across 8 campuses
                    </div>

                    <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-tight mb-6">
                        Safer digital experiences<br />
                        <span className="bg-gradient-to-r from-teal-400 to-brand-400 bg-clip-text text-transparent">for every campus.</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-xl mx-auto mb-10 leading-relaxed">
                        CampusShield AI detects phishing threats, explains every decision in plain language,
                        and protects student privacy — built for the scale of modern higher education.
                    </p>

                    <div className="flex items-center justify-center gap-4">
                        <Link href="/student/scan" className="btn-primary flex items-center gap-2">
                            Analyze an Email <ArrowRight className="w-4 h-4" />
                        </Link>
                        <Link href="/admin/dashboard" className="btn-outline">
                            Admin Dashboard
                        </Link>
                    </div>
                </motion.div>

                {/* Feature Cards */}
                <div className="mt-24 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 max-w-5xl w-full">
                    {FEATURES.map((f, i) => (
                        <motion.div
                            key={f.title}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 + i * 0.1 }}
                            className="glass-card p-6 text-left space-y-3"
                        >
                            <div className="p-2.5 w-fit rounded-xl bg-teal-500/10 border border-teal-500/20">
                                <f.icon className="w-5 h-5 text-teal-400" />
                            </div>
                            <h3 className="font-semibold text-white text-sm">{f.title}</h3>
                            <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </main>

            <footer className="text-center py-6 text-xs text-slate-600 border-t border-white/5">
                CampusShield AI © 2025 — Privacy-first campus security
            </footer>
        </div>
    );
}
