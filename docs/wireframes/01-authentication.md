# WF-01 — Authentication (Register / Login)

Routes: `/register`, `/login` · Roles: guest · Spec: FR-001..FR-004, §28.1

## Login

```
┌──────────────────────────────────────────┐
│                 ✦ logo                   │
│            Welcome back                  │
│  ┌────────────────────────────────────┐  │
│  │ Email                              │  │
│  │ [__________________________]       │  │
│  │ Password            (👁 toggle)     │  │
│  │ [__________________________]       │  │
│  │ [ ] Remember me     Forgot?        │  │
│  │        [    Sign In    ]           │  │
│  │  ──────────  or  ──────────        │  │
│  │  [ G  Continue with Google ]       │  │ ← OAuth2 default: Google (§49.3)
│  │  New here? Create account          │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## Register

```
┌──────────────────────────────────────────┐
│              Create your account         │
│  Name*      [____________________]       │
│  Email*     [____________________]       │
│  Password*  [____________________]  ⚠ strength meter
│  Age Group  [ select ▼ ]                 │ ← FR-005 field
│  [ ] I accept Terms & Privacy Policy   * │
│           [  Create Account  ]           │
│  ──────────  or  ──────────              │
│  [ G  Sign up with Google ]              │
│  Already registered? Sign in             │
└──────────────────────────────────────────┘
```

## States & behavior

- LOADING: submit button shows spinner, form disabled.
- ERROR: inline field errors (400/422), auth-failure banner (401), rate-limit notice (429).
- SUCCESS: store JWT access token (memory) + rotating refresh token; redirect to
  onboarding/profile if first login, else `/dashboard`.
- OAuth failure: provider-error banner with retry (§23.2).
- Password rules surfaced live; Argon2id hashing server-side (never client hints of policy internals beyond UX meter).
