import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Save, AlertTriangle, X, Monitor } from 'lucide-react';
import '../KizunaHUD.css';

interface ConfigurationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  showScanlines: boolean;
  setShowScanlines: (show: boolean) => void;
}

export const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  isOpen,
  onClose,
  showScanlines,
  setShowScanlines
}) => {
  const [config, setConfig] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [coreDirective, setCoreDirective] = useState("");

  useEffect(() => {
    if (isOpen) {
      fetchConfig();
    }
  }, [isOpen]);

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/system/config");
      const data = await res.json();
      setConfig(data);
      setCoreDirective(data.core_directive || "");
    } catch (e) {
      console.error("Failed to load config", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setIsSaving(true);
    try {
      // Merge current config with updated directive
      const newConfig = { ...config, core_directive: coreDirective };
      const res = await fetch("/api/system/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newConfig)
      });
      if (res.ok) {
        setConfig(await res.json());
        alert("Configuration Saved.");
      } else {
        alert("Save failed.");
      }
    } catch (e) {
      console.error("Save error", e);
      alert("Error saving config.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleWipeGraph = async () => {
    if (!window.confirm("WARNING: This will permanently delete all episodic memories and dreams. Are you sure?")) {
      return;
    }

    try {
      const res = await fetch("/api/system/purge-memories", {
        method: "DELETE"
      });

      if (res.ok) {
        window.alert("Memory Cleared. The slate is clean.");
      } else {
        window.alert("Purge failed. Check server logs.");
      }
    } catch (e) {
      console.error(e);
      window.alert("Purge error.");
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm"
        >
          <div className="w-[800px] max-h-[90vh] bg-abyssal-black border border-electric-blue/50 shadow-2xl shadow-electric-blue/20 flex flex-col overflow-hidden relative shape-modal-shard">

            {/* Header */}
            <div className="h-12 bg-vintage-navy/20 border-b border-electric-blue/30 flex items-center justify-between px-6">
              <div className="flex items-center gap-2 font-technical text-electric-blue">
                <Settings size={18} />
                <span>CONFIGURATION NEXUS // SYSTEM LEVEL 0</span>
              </div>
              <button onClick={onClose} className="text-electric-blue/60 hover:text-electric-blue">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-8">

              {/* SECTION 1: SOUL MATRIX */}
              <div className="space-y-4">
                <h3 className="font-monumental text-xl text-electric-blue border-b border-electric-blue/30 pb-2">
                  THE SOUL MATRIX
                </h3>
                <div className="bg-vintage-navy/10 p-4 border border-electric-blue/20">
                  <label className="block text-xs font-technical text-electric-blue mb-2">
                    CORE DIRECTIVE (IMMUTABLE INSTRUCTION SET)
                  </label>
                  {isLoading ? (
                    <div className="text-electric-blue animate-pulse">Loading Matrix...</div>
                  ) : (
                    <textarea
                      value={coreDirective}
                      onChange={(e) => setCoreDirective(e.target.value)}
                      className="w-full h-48 bg-abyssal-black text-electric-blue font-mono text-sm p-4 border border-vintage-navy focus:border-electric-blue outline-none resize-none"
                    />
                  )}
                  <div className="flex justify-end mt-4">
                    <button
                      onClick={handleSaveConfig}
                      disabled={isSaving || isLoading}
                      className="kizuna-shard-btn-wrapper"
                    >
                      <div className="kizuna-shard-btn-inner gap-2">
                        <Save size={16} /> {isSaving ? "SAVING..." : "COMMIT CHANGES"}
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              {/* SECTION 2: INTERFACE */}
              <div className="space-y-4">
                <h3 className="font-monumental text-xl text-electric-blue border-b border-electric-blue/30 pb-2">
                  INTERFACE PROTOCOLS
                </h3>
                <div className="bg-vintage-navy/10 p-4 border border-electric-blue/20 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Monitor size={24} className="text-electric-blue" />
                    <div>
                      <div className="font-technical text-electric-blue">CRT / SCANLINE EMULATION</div>
                      <div className="text-xs text-electric-blue/60 font-mono">
                        Toggle retro-dystopian visual artifacts.
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowScanlines(!showScanlines)}
                    className={`px-4 py-2 border ${showScanlines ? 'border-electric-blue bg-electric-blue/20 text-electric-blue' : 'border-vintage-navy text-gray-500'} font-technical transition-all`}
                  >
                    {showScanlines ? "ENABLED" : "DISABLED"}
                  </button>
                </div>
              </div>

              {/* SECTION 3: DANGER ZONE */}
              <div className="space-y-4">
                 <h3 className="font-monumental text-xl text-alert-red border-b border-alert-red/30 pb-2">
                    DANGER ZONE
                 </h3>
                 <div className="bg-alert-red/5 p-4 border border-alert-red/20 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                       <AlertTriangle size={24} className="text-alert-red" />
                       <div>
                          <div className="font-technical text-alert-red">SCORCHED EARTH PROTOCOL</div>
                          <div className="text-xs text-alert-red/60 font-mono">
                             Permanently wipe all episodic memories and dreams. Irreversible.
                          </div>
                       </div>
                    </div>
                    <button
                       onClick={handleWipeGraph}
                       className="px-4 py-2 bg-alert-red/10 border border-alert-red text-alert-red font-technical hover:bg-alert-red/20 transition-all"
                    >
                       WIPE GRAPH
                    </button>
                 </div>
              </div>

            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
