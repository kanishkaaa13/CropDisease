# Implementation Plan — Internationalization (i18n) with English, Hindi, and Marathi

Implement full multi-language support (English `en`, Hindi `hi`, Marathi `mr`) across the Next.js 14 frontend and FastAPI backend.

- **Default Language**: **Marathi (`mr`)** for the Farmer portal (`/farmer`), and **English (`en`)** for Field Officer (`/officer`) and Command Center (`/admin`).
- **Language Switcher**: Persistent in the top navigation bar, synced to `localStorage` and `cookie` (`app_lang`).
- **Backend API**: Machine-readable keys (`disease_key`, `severity_key`, `advisory_key`, `risk_level_key`) + localized outputs based on `lang` parameter or `Accept-Language` header.
- **Typography & Layout**: `Noto Sans Devanagari` font integration + layout validation against Devanagari text overflow.
- **Completeness Checker**: Automated validation script ensuring 100% key parity across `en.json`, `hi.json`, and `mr.json`.

---

## User Review Required

> [!IMPORTANT]
> - **Default Route Locales**: Visiting `/farmer` without prior saved language preference defaults to **Marathi (`mr`)**. Visiting `/officer`, `/admin`, or `/` defaults to **English (`en`)**. Once a user selects a language from the language switcher dropdown, that choice is remembered globally across all portals via `localStorage` and cookie `app_lang`.
> - **Translations Review**: Any translations involving complex agricultural terminology have been carefully translated into Marathi and Hindi and tagged with `TODO: Native speaker review` in translation comments/metadata where appropriate.

---

## Proposed Changes

### Frontend Internationalization

#### [NEW] [frontend/messages/en.json](file:///d:/CropDisease/frontend/messages/en.json)
#### [NEW] [frontend/messages/hi.json](file:///d:/CropDisease/frontend/messages/hi.json)
#### [NEW] [frontend/messages/mr.json](file:///d:/CropDisease/frontend/messages/mr.json)
- Full dictionary of UI translation keys grouped hierarchically:
  - `common`: buttons, statuses, loading, errors, units
  - `nav`: logo, portal links, language names
  - `home`: hero, portal cards, tech stack
  - `farmer`: farm list, scan workflow, blur warnings, quality checks, diagnosis details, Grad-CAM, IPM recommendations, follow-ups
  - `officer`: stats, validation queue, expert review actions, geospatial controls
  - `admin`: national overview, state metrics, district risk table, alerts
  - `diseases`: localized names for all 22 crop disease/pest classes
  - `severity`: low, moderate, high, critical labels and tooltips
  - `risk`: factors, explainability ("why"), forecast days

#### [NEW] [frontend/lib/i18n.tsx](file:///d:/CropDisease/frontend/lib/i18n.tsx)
- Lightweight, zero-dependency, type-safe Next.js App Router i18n Context & Hook (`useI18n()`, `useTranslations()`).
- Auto-detects route context (default `mr` for `/farmer`, `en` for `/officer` and `/admin`).
- Reads and writes `localStorage` and `document.cookie`.
- Provides template interpolation (e.g., `t("farmer.health_score", { score: 85 })`).

#### [MODIFY] [frontend/app/layout.tsx](file:///d:/CropDisease/frontend/app/layout.tsx)
- Import `Noto_Sans_Devanagari` alongside `Inter` from `next/font/google`.
- Wrap children in `<I18nProvider>`.
- Configure body font family with Devanagari fallback.

#### [MODIFY] [frontend/components/Navbar.tsx](file:///d:/CropDisease/frontend/components/Navbar.tsx)
- Add Language Switcher dropdown (English / हिंदी / मराठी) in the desktop & mobile navigation header with flags/icons.
- Use translation keys for navigation links.

#### [MODIFY] [frontend/app/page.tsx](file:///d:/CropDisease/frontend/app/page.tsx)
#### [MODIFY] [frontend/app/farmer/page.tsx](file:///d:/CropDisease/frontend/app/farmer/page.tsx)
#### [MODIFY] [frontend/app/officer/page.tsx](file:///d:/CropDisease/frontend/app/officer/page.tsx)
#### [MODIFY] [frontend/app/admin/page.tsx](file:///d:/CropDisease/frontend/app/admin/page.tsx)
#### [MODIFY] [frontend/components/farmer/FarmCard.tsx](file:///d:/CropDisease/frontend/components/farmer/FarmCard.tsx)
#### [MODIFY] [frontend/components/HealthBadge.tsx](file:///d:/CropDisease/frontend/components/HealthBadge.tsx)
- Replace all hardcoded strings with `t("...")` translation keys.
- Ensure container flex-wraps and padding accommodate longer Devanagari words without clipping.

#### [NEW] [frontend/scripts/check-i18n-keys.js](file:///d:/CropDisease/frontend/scripts/check-i18n-keys.js)
- Script that recursively traverses `en.json`, matches against `hi.json` and `mr.json`, and outputs any missing keys or empty values.
- Integrated into `frontend/package.json` as `"i18n:check": "node scripts/check-i18n-keys.js"`.

---

### Backend Internationalization

#### [NEW] [backend/app/i18n/__init__.py](file:///d:/CropDisease/backend/app/i18n/__init__.py)
#### [NEW] [backend/app/i18n/catalog.py](file:///d:/CropDisease/backend/app/i18n/catalog.py)
- Catalog containing:
  - 22 crop disease machine-readable keys (`tomato_leaf_blight`, `maize_fall_armyworm`, `cashew_anthracnose`, etc.) mapped to multilingual names (`en`, `hi`, `mr`).
  - Severity keys (`low`, `moderate`, `high`, `critical`) mapped to localized strings.
  - Risk factor explainability messages in `en`, `hi`, `mr`.
  - Helper functions `get_locale_from_request(lang, accept_language)` and `translate_disease(disease_name, lang)`.

#### [MODIFY] [backend/app/models/schemas.py](file:///d:/CropDisease/backend/app/models/schemas.py)
- Update `ScanResponse`, `TopPrediction`, `RiskScoreResponse` to include machine-readable keys (`disease_key`, `crop_key`, `severity_key`, `status_key`) alongside localized text fields.

#### [MODIFY] [backend/app/api/scan.py](file:///d:/CropDisease/backend/app/api/scan.py)
- Accept `lang: Optional[str] = Query(None)` and `Accept-Language: Optional[str] = Header(None)`.
- Populate machine-readable keys and localized disease name/status in the response.

#### [MODIFY] [backend/app/api/advisory.py](file:///d:/CropDisease/backend/app/api/advisory.py)
- Accept `lang` parameter / header, return machine-readable `advisory_key`, `disease_key`, and `crop_key`.

#### [MODIFY] [backend/app/api/risk.py](file:///d:/CropDisease/backend/app/api/risk.py)
- Accept `lang` parameter / header, return machine-readable `risk_level_key` and localized why factors.

---

## Verification Plan

### Automated Tests
1. **Translation Completeness Check**:
   ```bash
   cd frontend && node scripts/check-i18n-keys.js
   ```
   Must exit with code 0 and 0 missing keys.
2. **Frontend Typecheck & Build**:
   ```bash
   cd frontend && npm run build
   ```
3. **Backend Tests**:
   ```bash
   cd backend && .\venv\Scripts\pytest.exe tests/test_scan_api.py -v
   ```
4. **Backend i18n Unit Tests**:
   ```bash
   cd backend && .\venv\Scripts\python.exe -c "from app.i18n.catalog import translate_disease; print(translate_disease('Tomato leaf blight', 'mr'))"
   ```

### Manual Verification
- Open `http://localhost:3000/farmer` -> verify Marathi by default.
- Open `http://localhost:3000/officer` -> verify English by default.
- Use the Language Switcher in Navbar -> switch to Hindi, verify instant update and cookie/localStorage persistence across page navigation.
- Scan image -> verify localized response with machine-readable keys in network tab.
