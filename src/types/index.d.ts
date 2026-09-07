/**
 * Trinetra Identity Verification System - Type Definitions
 */

export interface User {
  user_id: string;
  username: string;
  role: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user?: User | null;
}

export interface VerificationSessionCreate {
  subject_name?: string | null;
  document_type?: string | null;
}

export interface VerificationSession {
  session_id: string;
  created_by: string;
  status: string;
  subject_name?: string | null;
  document_type?: string | null;
  created_at: string;
}

export interface VerificationSessionStatusResponse {
  session_id: string;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  has_document: boolean;
  has_biometric: boolean;
  has_result: boolean;
  subject_name?: string | null;
  document_type?: string | null;
}

export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
}

export class ApiError extends Error {
  status: number | null;
  detail: string;
  isNetworkError: boolean;
  isTimeout: boolean;
  isUnauthorized: boolean;
  isForbidden: boolean;
  isNotFound: boolean;
  isValidationError: boolean;
  isServerError: boolean;

  constructor(
    message: string,
    options?: {
      status?: number | null;
      detail?: string;
      isNetworkError?: boolean;
      isTimeout?: boolean;
    }
  );
}

export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (tokenVal: string, userVal: User) => void;
  logout: () => void;
}

export interface VerificationSessionState {
  activeSession: VerificationSession | null;
  activeSessionId: string | null;
  sessionStatus: string | null;
  currentStep: 'idle' | 'created' | 'document_uploaded' | 'biometric_uploaded' | 'verifying' | 'completed' | 'error';
  loading: boolean;
  error: string | null;
  createSession: (subjectName?: string, documentType?: string) => Promise<VerificationSession>;
  loadSession: (sessionId: string) => Promise<VerificationSessionStatusResponse>;
  clearSession: () => void;
}
