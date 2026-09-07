"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiCreateSession, apiGetSession } from "@/lib/api";

const SessionContext = createContext(null);

const SESSION_STORAGE_KEY = "trinetra_active_session_id";

export function SessionProvider({ children }) {
  const [activeSession, setActiveSession] = useState(null);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionStatus, setSessionStatus] = useState(null);
  const [currentStep, setCurrentStep] = useState("idle"); // idle, created, uploading, verifying, completed, error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Restore session from sessionStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedId = sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (storedId) {
      setActiveSessionId(storedId);
      // Fetch latest session status from backend
      apiGetSession(storedId)
        .then((res) => {
          setSessionStatus(res.status || "active");
          setActiveSession((prev) => ({
            ...(prev || {}),
            session_id: res.session_id,
            status: res.status,
            created_by: res.created_by,
            created_at: res.created_at,
            has_document: res.has_document,
            has_biometric: res.has_biometric,
            has_result: res.has_result,
            subject_name: res.subject_name,
            document_type: res.document_type,
          }));
          setCurrentStep(res.has_result ? "completed" : res.has_document ? "document_uploaded" : "created");
        })
        .catch((err) => {
          // If session not found or error, clear invalid stored session
          sessionStorage.removeItem(SESSION_STORAGE_KEY);
          setActiveSessionId(null);
          setActiveSession(null);
        });
    }
  }, []);

  const createSession = useCallback(async (subjectName = "Verification Subject", documentType = "passport") => {
    if (loading) return null; // Prevent duplicate session creation clicks
    setLoading(true);
    setError(null);

    try {
      const res = await apiCreateSession(subjectName, documentType);
      const sessionObj = {
        session_id: res.session_id,
        created_by: res.created_by,
        status: res.status,
        subject_name: res.subject_name || subjectName,
        document_type: res.document_type || documentType,
        created_at: res.created_at,
      };

      setActiveSession(sessionObj);
      setActiveSessionId(res.session_id);
      setSessionStatus(res.status || "created");
      setCurrentStep("created");

      if (typeof window !== "undefined") {
        sessionStorage.setItem(SESSION_STORAGE_KEY, res.session_id);
      }

      return sessionObj;
    } catch (err) {
      const msg = err.message || "Failed to create verification session on backend.";
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const loadSession = useCallback(async (sessionId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiGetSession(sessionId);
      setActiveSessionId(res.session_id);
      setSessionStatus(res.status);
      setActiveSession({
        session_id: res.session_id,
        status: res.status,
        created_by: res.created_by,
        created_at: res.created_at,
        has_document: res.has_document,
        has_biometric: res.has_biometric,
        has_result: res.has_result,
        subject_name: res.subject_name,
        document_type: res.document_type,
      });
      if (typeof window !== "undefined") {
        sessionStorage.setItem(SESSION_STORAGE_KEY, res.session_id);
      }
      return res;
    } catch (err) {
      setError(err.message || "Failed to load session details.");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearSession = useCallback(() => {
    setActiveSession(null);
    setActiveSessionId(null);
    setSessionStatus(null);
    setCurrentStep("idle");
    setError(null);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  }, []);

  return (
    <SessionContext.Provider
      value={{
        activeSession,
        activeSessionId,
        sessionStatus,
        currentStep,
        setCurrentStep,
        loading,
        error,
        createSession,
        loadSession,
        clearSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession must be used inside a SessionProvider");
  }
  return ctx;
}
