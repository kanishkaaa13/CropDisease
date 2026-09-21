"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useI18n, type Locale } from "@/lib/i18n";
import { matchVoiceIntent, type VoiceIntent } from "@/lib/voiceIntents";

interface RecognitionResultEvent {
  resultIndex: number;
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal?: boolean }>;
}

interface RecognitionErrorEvent { error: string; }
interface RecognitionInstance {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: RecognitionResultEvent) => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

type RecognitionConstructor = new () => RecognitionInstance;
type SpeechWindow = Window & {
  SpeechRecognition?: RecognitionConstructor;
  webkitSpeechRecognition?: RecognitionConstructor;
};

interface VoiceAssistantProps {
  lastResultText?: string;
  diseaseLabel?: string;
  cropName?: string;
  severityPct?: number;
  onIntent?: (intent: VoiceIntent) => void | Promise<void>;
}

const localeToSpeech: Record<Locale, string> = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

export function speakText(text: string, locale: Locale, onFallback?: () => void) {
  if (typeof window === "undefined" || !window.speechSynthesis) return false;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices();
  const language = localeToSpeech[locale].toLowerCase();
  const voice = voices.find((item) => item.lang.toLowerCase() === language)
    ?? voices.find((item) => item.lang.toLowerCase().startsWith(locale));
  if (voice) utterance.voice = voice;
  else if (locale === "mr") onFallback?.();
  utterance.lang = language;
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
  return true;
}

export default function VoiceAssistant({ lastResultText, diseaseLabel, cropName, severityPct, onIntent }: VoiceAssistantProps) {
  const { locale, setLocale } = useI18n();
  const recognitionRef = useRef<RecognitionInstance | null>(null);
  const [supported, setSupported] = useState<boolean | null>(null);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState("");
  const [speakingFallback, setSpeakingFallback] = useState(false);

  useEffect(() => {
    const speechWindow = window as SpeechWindow;
    setSupported(Boolean(speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition) && Boolean(window.speechSynthesis));
  }, []);

  useEffect(() => () => {
    recognitionRef.current?.stop();
    window.speechSynthesis?.cancel();
  }, []);

  function startListening() {
    if (!supported) return;
    const speechWindow = window as SpeechWindow;
    const Constructor = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    if (!Constructor) return;
    const recognition = new Constructor();
    recognition.lang = localeToSpeech[locale];
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      let text = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) text += event.results[index][0].transcript;
      setTranscript(text);
      setStatus("Listening...");
      const lastResult = event.results[event.results.length - 1];
      if (lastResult?.[0]?.transcript && lastResult.isFinal) {
        const finalText = text.trim();
        const intent = matchVoiceIntent(finalText, locale);
        if (intent) {
          if (intent === "change_language_hi") setLocale("hi");
          if (intent === "read_last_result") {
            if (lastResultText) {
              speakText(lastResultText, locale, () => setSpeakingFallback(true));
              setStatus("Reading your last result");
            } else {
              setStatus("There is no scan result yet");
            }
          }
          void onIntent?.(intent);
          setStatus("Command understood");
        } else {
          void askQuestion(finalText);
        }
      }
    };
    recognition.onerror = (event) => {
      setListening(false);
      setStatus(event.error === "not-allowed" ? "Microphone permission was denied" : event.error === "no-speech" ? "No speech heard. Please try again." : "Voice input is unavailable");
    };
    recognition.onend = () => { setListening(false); };
    recognitionRef.current = recognition;
    setTranscript("");
    setStatus("Listening...");
    setListening(true);
    try { recognition.start(); } catch { setListening(false); setStatus("Voice input is busy. Try again."); }
  }

  async function askQuestion(question: string) {
    if (!question) { setStatus("Please say a question"); return; }
    setStatus("Finding an answer...");
    try {
      const response = await api.askAssistant(question, locale, { disease_label: diseaseLabel, crop_name: cropName, severity_pct: severityPct });
      speakText(response.answer, locale, () => setSpeakingFallback(true));
      setStatus("Answering");
    } catch {
      setStatus("I could not reach the assistant. Please try again.");
    }
  }

  if (supported === false) return <div className="fixed bottom-4 right-4 z-50 max-w-[220px] rounded-xl border border-amber-500/30 bg-slate-950/95 px-3 py-2 text-[11px] text-amber-200 shadow-xl">Voice input is not supported in this browser.</div>;
  if (supported === null) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex max-w-[calc(100vw-2rem)] flex-col items-end gap-2">
      {(status || transcript || speakingFallback) && <div className="rounded-xl border border-white/10 bg-slate-950/95 px-3 py-2 text-right text-xs text-slate-200 shadow-xl">
        {transcript && <p className="max-w-[260px] break-words text-emerald-300">{transcript}</p>}
        {status && <p>{status}</p>}
        {speakingFallback && <p className="text-amber-300">No Marathi voice found; using the browser default voice.</p>}
      </div>}
      <button onClick={listening ? () => recognitionRef.current?.stop() : startListening} className={`flex h-14 w-14 items-center justify-center rounded-full border-2 text-2xl shadow-2xl transition ${listening ? "animate-pulse border-red-300 bg-red-500 text-white" : "border-emerald-300 bg-emerald-500 text-slate-950"}`} aria-label={listening ? "Stop listening" : `Speak in ${localeToSpeech[locale]}`}>
        {listening ? "■" : "🎙"}
      </button>
    </div>
  );
}
