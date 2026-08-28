"use client";

import { createContext, ReactNode, useContext } from "react";
import { AuthProvider, useAuth } from "react-oidc-context";

interface EnterpriseAuthState {
  configured: boolean;
  authenticated: boolean;
  loading: boolean;
  accessToken?: string;
  subject?: string;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const authority = process.env.NEXT_PUBLIC_OIDC_AUTHORITY;
const clientId = process.env.NEXT_PUBLIC_OIDC_CLIENT_ID;
const redirectUri = process.env.NEXT_PUBLIC_OIDC_REDIRECT_URI;
const oidcConfigured = Boolean(authority && clientId && redirectUri);

const EnterpriseAuthContext = createContext<EnterpriseAuthState | null>(null);

const developmentAuth: EnterpriseAuthState = {
  configured: false,
  authenticated: true,
  loading: false,
  signIn: async () => undefined,
  signOut: async () => undefined
};

function OidcBridge({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const state: EnterpriseAuthState = {
    configured: true,
    authenticated: auth.isAuthenticated,
    loading: auth.isLoading,
    accessToken: auth.user?.access_token,
    subject: auth.user?.profile.sub,
    signIn: async () => {
      await auth.signinRedirect();
    },
    signOut: async () => {
      await auth.signoutRedirect();
    }
  };
  return <EnterpriseAuthContext.Provider value={state}>{children}</EnterpriseAuthContext.Provider>;
}

export function Providers({ children }: { children: ReactNode }) {
  if (!oidcConfigured) {
    return (
      <EnterpriseAuthContext.Provider value={developmentAuth}>
        {children}
      </EnterpriseAuthContext.Provider>
    );
  }

  return (
    <AuthProvider
      authority={authority!}
      client_id={clientId!}
      redirect_uri={redirectUri!}
      scope={process.env.NEXT_PUBLIC_OIDC_SCOPE ?? "openid profile"}
      response_type="code"
      automaticSilentRenew
      onSigninCallback={() => window.history.replaceState({}, document.title, window.location.pathname)}
    >
      <OidcBridge>{children}</OidcBridge>
    </AuthProvider>
  );
}

export function useEnterpriseAuth(): EnterpriseAuthState {
  const context = useContext(EnterpriseAuthContext);
  if (!context) {
    throw new Error("useEnterpriseAuth must be used within Providers");
  }
  return context;
}
