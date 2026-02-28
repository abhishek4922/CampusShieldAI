"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    BookOpen, Trophy, Star, ChevronRight, Zap,
    Lock, Shield, Brain, CheckCircle2, MessageSquare,
    Send, Bot
} from "lucide-react";

const LESSONS = [
    { id: "phishing-basics", title: "Recognising Phishing Emails", difficulty: "beginner", xp: 10, icon: Shield, completed: true },
    { id: "url-safety", title: "Spotting Dangerous Links", difficulty: "beginner", xp: 10, icon: Lock, completed: false },
    { id: "social-engineering", title: "Social Engineering Tactics", difficulty: "intermediate", xp: 20, icon: Brain, completed: false },
    { id: "mfa-guide", title: "Multi-Factor Authentication", difficulty: "intermediate", xp: 20, icon: Zap, completed: false },
    { id: "advanced-threats", title: "Advanced Persistent Threats", difficulty: "advanced", xp: 50, icon: Trophy, completed: false, locked: true },
];

const CHAT_MESSAGES = [
    { role: "ai", text: "👋 Hi! I'm Shield, your digital hygiene companion. What would you like to learn today?" },
    { role: "user", text: "How do I spot a phishing email?" },
    { role: "ai", text: "Great question! Here are the top 3 red flags:\n\n🔴 **Urgency**: 'Act now or your account will be closed'\n🔴 **Mismatch**: Links go to different domains than the sender\n🔴 **Requests**: Asking for passwords or payment info\n\nNever click links — always go directly to the website!" },
];

const DIFFICULTY_COLORS: Record<string, string> = {
    beginner: "#22c55e",
    intermediate: "#f59e0b",
    advanced: "#8b5cf6",
};

function LessonCard({ lesson }: { lesson: typeof LESSONS[0] }) {
    const Icon = lesson.icon;
    return (
        <motion.div
            className={`glass-card p-5 flex items-center gap-4 ${lesson.locked ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            whileHover={lesson.locked ? {} : { x: 4, borderColor: "rgba(6,182,212,0.5)" }}
        >
            <div className="p-3 rounded-xl flex-shrink-0" style={{ background: `${DIFFICULTY_COLORS[lesson.difficulty]}20` }}>
                <Icon className="w-5 h-5" style={{ color: DIFFICULTY_COLORS[lesson.difficulty] }} />
            </div>
            <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-white truncate">{lesson.title}</p>
                <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded-full capitalize" style={{ background: `${DIFFICULTY_COLORS[lesson.difficulty]}20`, color: DIFFICULTY_COLORS[lesson.difficulty] }}>
                        {lesson.difficulty}
                    </span>
                    <span className="text-xs text-slate-500">+{lesson.xp} XP</span>
                </div>
            </div>
            <div className="flex-shrink-0">
                {lesson.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                ) : lesson.locked ? (
                    <Lock className="w-4 h-4 text-slate-600" />
                ) : (
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
            </div>
        </motion.div>
    );
}

export default function HygienePage() {
    const [messages, setMessages] = useState(CHAT_MESSAGES);
    const [input, setInput] = useState("");

    function sendMessage(e: React.FormEvent) {
        e.preventDefault();
        if (!input.trim()) return;
        setMessages(m => [
            ...m,
            { role: "user", text: input },
            { role: "ai", text: "That's a great question! Keep exploring the lessons above to deepen your cybersecurity knowledge. 🛡️" },
        ]);
        setInput("");
    }

    return (
        <div className="min-h-screen p-6 md:p-10 space-y-8 animate-fade-in">
            {/* Header */}
            <div>
                <div className="flex items-center gap-3 mb-1">
                    <BookOpen className="w-7 h-7 text-teal-400" />
                    <h1 className="section-title text-3xl">Digital Hygiene Companion</h1>
                </div>
                <p className="text-slate-400 text-sm">Learn, earn XP, and level up your cyber awareness. Progress is stored anonymously.</p>
            </div>

            {/* Progress Banner */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-6 flex flex-col md:flex-row items-center gap-6"
            >
                <div className="flex items-center gap-4">
                    <Trophy className="w-10 h-10 text-amber-400" />
                    <div>
                        <p className="text-xs text-slate-400 uppercase tracking-widest">Your Rank</p>
                        <p className="text-xl font-bold text-amber-400">Defender 🛡️</p>
                    </div>
                </div>
                <div className="flex-1 w-full">
                    <div className="flex justify-between text-xs text-slate-400 mb-2">
                        <span>XP Progress</span>
                        <span className="font-semibold text-white">65 / 150 XP</span>
                    </div>
                    <div className="h-2.5 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: "43%" }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className="h-full rounded-full bg-gradient-to-r from-amber-500 to-amber-300"
                        />
                    </div>
                </div>
                <div className="flex gap-3 text-center">
                    <div>
                        <p className="text-2xl font-bold text-white">1</p>
                        <p className="text-xs text-slate-400">Completed</p>
                    </div>
                    <div className="w-px bg-white/10" />
                    <div>
                        <p className="text-2xl font-bold text-teal-400">4</p>
                        <p className="text-xs text-slate-400">Remaining</p>
                    </div>
                </div>
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Lessons */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <Star className="w-4 h-4 text-teal-400" />
                        <h2 className="font-semibold text-white">Lessons</h2>
                    </div>
                    <div className="space-y-3">
                        {LESSONS.map(lesson => <LessonCard key={lesson.id} lesson={lesson} />)}
                    </div>
                </div>

                {/* AI Chat Companion */}
                <div className="glass-card flex flex-col" style={{ minHeight: 480 }}>
                    <div className="p-5 border-b border-white/5 flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-500 to-brand-600 flex items-center justify-center">
                            <Bot className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <p className="font-semibold text-sm text-white">Shield AI</p>
                            <p className="text-xs text-teal-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-teal-400 inline-block" />Online</p>
                        </div>
                    </div>
                    <div className="flex-1 p-5 space-y-4 overflow-y-auto">
                        {messages.map((msg, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                            >
                                {msg.role === "ai" && (
                                    <div className="w-7 h-7 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center flex-shrink-0">
                                        <Bot className="w-4 h-4 text-teal-400" />
                                    </div>
                                )}
                                <div
                                    className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${msg.role === "user"
                                            ? "bg-brand-600 text-white rounded-tr-sm"
                                            : "bg-white/5 text-slate-200 rounded-tl-sm border border-white/10"
                                        }`}
                                >
                                    {msg.text}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                    <form onSubmit={sendMessage} className="p-4 border-t border-white/5 flex gap-2">
                        <input
                            className="cs-input flex-1 py-2 text-sm"
                            placeholder="Ask Shield a question..."
                            value={input}
                            onChange={e => setInput(e.target.value)}
                        />
                        <button type="submit" className="btn-primary px-4 py-2">
                            <Send className="w-4 h-4" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
