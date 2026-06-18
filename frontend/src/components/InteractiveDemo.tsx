import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, Activity, Play, CheckCircle2, Stethoscope, FileText } from 'lucide-react';

const SIMULATION_TEXT = "Patient presents with a severe headache and high fever starting 2 days ago. They report feeling nauseous this morning. Denies any chest pain or shortness of breath.";

export function InteractiveDemo() {
  const [phase, setPhase] = useState<'idle' | 'recording' | 'transcribing' | 'extracting' | 'complete'>('idle');
  const [transcript, setTranscript] = useState("");
  const [showEntities, setShowEntities] = useState(false);
  const [showSoap, setShowSoap] = useState(false);

  // Simulation Sequence
  const runSimulation = () => {
    if (phase !== 'idle') return;
    
    setPhase('recording');
    setTranscript("");
    setShowEntities(false);
    setShowSoap(false);

    // After 2s of recording, start transcribing
    setTimeout(() => {
      setPhase('transcribing');
      let currentText = "";
      const textArray = SIMULATION_TEXT.split("");
      let i = 0;
      
      const typeWriter = setInterval(() => {
        if (i < textArray.length) {
          currentText += textArray[i];
          setTranscript(currentText);
          i++;
        } else {
          clearInterval(typeWriter);
          // Transcription done, start extraction
          setTimeout(() => {
            setPhase('extracting');
            setTimeout(() => {
              setShowEntities(true);
              // Extraction done, show SOAP
              setTimeout(() => {
                setPhase('complete');
                setShowSoap(true);
              }, 1500);
            }, 800);
          }, 500);
        }
      }, 30); // Speed of typing
    }, 2000);
  };

  const resetSimulation = () => {
    setPhase('idle');
    setTranscript("");
    setShowEntities(false);
    setShowSoap(false);
  };

  // Waveform dots
  const Waveform = () => (
    <div className="flex items-center gap-1 h-6">
      {[...Array(5)].map((_, i) => (
        <motion.div
          key={i}
          animate={{ height: ['20%', '100%', '20%'] }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.1,
            ease: "easeInOut"
          }}
          className="w-1.5 bg-red-400 rounded-full"
        />
      ))}
    </div>
  );

  return (
    <div className="w-full max-w-4xl mx-auto rounded-xl border border-white/10 bg-[#0a0f18] shadow-2xl overflow-hidden font-sans">
      {/* Top Bar */}
      <div className="h-10 bg-[#111827] border-b border-white/5 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></div>
        </div>
        <div className="text-[10px] text-slate-500 font-mono tracking-wider">VOICE2SOAP CONSOLE</div>
        <div className="w-16"></div> {/* Spacer for centering */}
      </div>

      <div className="flex flex-col md:flex-row h-[400px]">
        {/* Left Panel: Audio & Transcript */}
        <div className="flex-1 border-r border-white/5 p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Mic className="w-4 h-4 text-emerald-400" /> Consultation Audio
            </h3>
            
            {phase === 'idle' ? (
              <button 
                onClick={runSimulation}
                className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 rounded border border-emerald-500/20 text-xs font-bold transition-colors"
              >
                <Play className="w-3 h-3" /> Run Simulation
              </button>
            ) : phase === 'complete' ? (
              <button 
                onClick={resetSimulation}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded border border-white/10 text-xs font-bold transition-colors"
              >
                Reset
              </button>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 text-red-400 rounded border border-red-500/20 text-xs font-bold">
                <Square className="w-3 h-3 fill-current" /> {phase === 'recording' ? 'Listening...' : 'Processing...'}
              </div>
            )}
          </div>

          <div className="bg-[#111827] rounded-lg border border-white/5 p-4 min-h-[100px] mb-4 flex items-center justify-center">
             {phase === 'idle' ? (
               <span className="text-slate-500 text-sm">Awaiting input...</span>
             ) : phase === 'recording' ? (
               <Waveform />
             ) : (
               <div className="flex items-center gap-2 text-slate-400 text-sm">
                 <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Audio Captured (12s)
               </div>
             )}
          </div>

          <div className="flex-1 bg-[#111827] rounded-lg border border-white/5 p-4 overflow-y-auto">
            <p className="text-sm text-slate-300 leading-relaxed font-medium">
              {transcript}
              {(phase === 'transcribing' || phase === 'recording') && (
                <span className="inline-block w-1.5 h-4 ml-1 bg-emerald-400 animate-pulse align-middle"></span>
              )}
            </p>
          </div>
        </div>

        {/* Right Panel: Extraction & SOAP */}
        <div className="w-full md:w-72 bg-[#0d131f] p-6 flex flex-col relative overflow-hidden">
          <AnimatePresence mode="wait">
            {!showSoap ? (
              <motion.div 
                key="extraction"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex-1 flex flex-col"
              >
                <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-6">
                  <Activity className="w-4 h-4 text-blue-400" /> Live Extraction
                </h3>
                
                <div className="space-y-4">
                  {/* Symptoms */}
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 block">Symptoms</span>
                    <div className="flex flex-wrap gap-2">
                      <AnimatePresence>
                        {showEntities && (
                          <>
                            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs rounded">Headache</motion.div>
                            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.1 }} className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs rounded">Fever</motion.div>
                            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.2 }} className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs rounded">Nausea</motion.div>
                          </>
                        )}
                        {!showEntities && <span className="text-slate-600 text-xs">Waiting...</span>}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Vitals */}
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 block">Context / Vitals</span>
                    <div className="flex flex-wrap gap-2">
                      <AnimatePresence>
                        {showEntities && (
                          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.3 }} className="px-2 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs rounded">Duration: 2 Days</motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Negated */}
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2 block">Negated</span>
                    <div className="flex flex-wrap gap-2">
                      <AnimatePresence>
                        {showEntities && (
                          <>
                            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.4 }} className="px-2 py-1 bg-red-500/5 border border-red-500/10 text-slate-400 line-through text-xs rounded">Chest Pain</motion.div>
                            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.5 }} className="px-2 py-1 bg-red-500/5 border border-red-500/10 text-slate-400 line-through text-xs rounded">Shortness of Breath</motion.div>
                          </>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </div>

                {phase === 'extracting' && !showEntities && (
                  <div className="absolute inset-0 bg-[#0d131f]/50 backdrop-blur-sm flex items-center justify-center">
                    <div className="flex items-center gap-2 text-blue-400 text-xs font-medium">
                      <Stethoscope className="w-4 h-4 animate-pulse" /> NLP Engine Running...
                    </div>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div 
                key="soap"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex-1 flex flex-col h-full"
              >
                <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
                  <FileText className="w-4 h-4 text-cyan-400" /> Generated SOAP
                </h3>
                
                <div className="flex-1 bg-white border border-slate-200 rounded p-3 overflow-y-auto text-slate-800 text-xs">
                  <div className="space-y-3">
                    <div>
                      <strong className="text-slate-900 block mb-1">Subjective</strong>
                      <p>Patient reports severe headache and high fever starting 2 days ago. Accompanied by morning nausea. Denies chest pain or shortness of breath.</p>
                    </div>
                    <div>
                      <strong className="text-slate-900 block mb-1">Objective</strong>
                      <p>Pending physical examination.</p>
                    </div>
                    <div>
                      <strong className="text-slate-900 block mb-1">Assessment</strong>
                      <p>Acute febrile illness with headache and nausea. Differential diagnosis includes viral syndrome.</p>
                    </div>
                    <div>
                      <strong className="text-slate-900 block mb-1">Plan</strong>
                      <p>Advised symptomatic relief. Review if symptoms worsen or persist.</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
