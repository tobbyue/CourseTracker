# Lighthouse Audit Report - CourseTracker
## Group CT - Sustainability & Performance Assessment (Day 12)

### Audit Date
_Fill in after running Lighthouse in Chrome DevTools_

### Pages Tested
1. Login page (`/accounts/login/`)
2. Student Dashboard (`/courses/dashboard/`)
3. Profile page (`/accounts/profile/`)

---

## Before Optimisation (Baseline)

| Metric               | Login Page | Dashboard | Profile |
|-----------------------|-----------|-----------|---------|
| Performance           |           |           |         |
| Accessibility         |           |           |         |
| Best Practices        |           |           |         |
| SEO                   |           |           |         |

### Key Issues Identified
- _List Lighthouse warnings here_

---

## After Optimisation (Day 12 Changes)

| Metric               | Login Page | Dashboard | Profile |
|-----------------------|-----------|-----------|---------|
| Performance           |           |           |         |
| Accessibility         |           |           |         |
| Best Practices        |           |           |         |
| SEO                   |           |           |         |

---

## Optimisations Applied

### Performance
| Change | File | Impact |
|--------|------|--------|
| Added `<link rel="preconnect">` for CDN | `base.html` | Reduces DNS lookup + TLS handshake time for Bootstrap CDN |
| Added `defer` attribute to all `<script>` tags | `base.html` | Eliminates render-blocking JavaScript |
| Removed redundant `DOMContentLoaded` wrapper | `main.js` | Smaller JS payload; `defer` already ensures DOM readiness |
| Non-blocking Bootstrap Icons load (`preload` + `onload`) | `base.html` | Icons CSS no longer render-blocking; improves FCP/LCP |
| `font-display: swap` for icon font | `style.css` | Prevents invisible text during icon font loading |
| Cache-Control middleware | `middleware.py` | Enables browser caching for static auth pages (5 min TTL) |
| WhiteNoise compressed static files | `settings.py` | Gzip/Brotli compression for CSS/JS in production |

### Security / Best Practices
| Change | File | Impact |
|--------|------|--------|
| Subresource Integrity (SRI) hashes on Bootstrap CDN | `base.html` | Prevents tampered CDN scripts from executing |
| `X-Content-Type-Options: nosniff` header | `middleware.py` | Prevents MIME-type sniffing attacks |
| `Referrer-Policy: strict-origin-when-cross-origin` | `middleware.py` | Limits referrer info sent to third parties |
| `Permissions-Policy` header | `middleware.py` | Disables unused browser APIs (camera, mic, etc.) |
| `X-DNS-Prefetch-Control: on` header | `middleware.py` | Enables DNS prefetching for external resources |
| HSTS + Secure Cookies (production) | `settings.py` | Enforces HTTPS in production deployment |

### Accessibility
| Change | File | Impact |
|--------|------|--------|
| `<meta name="description">` | `base.html` | Improves SEO score; describes page purpose |
| `<meta name="theme-color">` | `base.html` | Enhances mobile browser chrome appearance |
| `aria-hidden="true"` on decorative icons | `base.html`, templates | Screen readers skip decorative icons (WCAG 1.1.1) |
| Fixed heading hierarchy (h1 > h2) | `login.html` | Proper document outline for assistive technology |
| Removed redundant `role="navigation"` on `<nav>` | `base.html` | Eliminates ARIA redundancy warning |
| `aria-label` on progress bars | `student_dashboard.html` | Programmatic progress identification (WCAG 1.3.1) |
| `aria-label` on all forms | Templates | Screen readers announce form purpose (WCAG 1.3.1) |
| `aria-invalid` on error fields | Templates | Programmatic error identification (WCAG 3.3.1) |
| Skip-to-content link | `base.html` | Keyboard users can bypass navigation (WCAG 2.4.1) |
| Touch targets min 44px | `style.css` | Meets WCAG 2.5.5 target size requirement |
| `prefers-reduced-motion` | `style.css` | Respects user motion preferences (WCAG 2.3.3) |

### SEO
| Change | File | Impact |
|--------|------|--------|
| Meta description tag | `base.html` | Provides search-engine-friendly page summary |
| Semantic HTML structure | Templates | Proper heading hierarchy (h1 > h2 > h3) |

---

## Score Improvement Summary

| Metric          | Before (avg) | After (avg) | Change |
|-----------------|-------------|-------------|--------|
| Performance     |             |             |        |
| Accessibility   |             |             |        |
| Best Practices  |             |             |        |
| SEO             |             |             |        |

---

## How to Run the Audit

1. Start the development server: `python manage.py runserver`
2. Open Chrome and navigate to the page
3. Open DevTools (F12) > Lighthouse tab
4. Select categories: Performance, Accessibility, Best Practices, SEO
5. Choose "Mobile" device
6. Click "Analyze page load"
7. Record scores in the tables above
8. Save the full HTML report from Lighthouse for submission
