# Changing the UI — Template Guide

This frontend is deliberately split so you can restyle or restructure the interface **without touching backend code or the API logic**. Here's exactly what to edit for each kind of change.

---

## 1. Just want a different look? → Edit ONE file

```
frontend/css/style.css
```

Every color, font, spacing value, and border style is a CSS variable defined at the top of this file:

```css
:root {
  --bg: #0b0b0e;
  --accent: #e8923a;
  --font: 'JetBrains Mono', monospace;
  --radius: 0px;
  /* ...all other values */
}
```

**To re-theme:** change the values in `:root`. Nothing else needs to change — no JS file references a color or font directly, they all use classes styled by this file.

**To swap the whole file:** replace `style.css` entirely with your own stylesheet, as long as it defines the same class names used in the HTML templates (see file list below). The safest way to write a replacement is to keep every existing class name (`.repo-row`, `.badge--ready`, `.stat-card`, etc.) and just change what they look like.

---

## 2. Want to change what's IN the sidebar/topbar? → Edit the template files

```
frontend/js/templates/sidebar.js   — left nav menu + logo
frontend/js/templates/topbar.js    — breadcrumb bar generator
frontend/js/templates/components.js — badges, empty states, banners, formatters
```

These are pure functions: they take data in, return an HTML string out. They don't call the API and don't contain business logic — safe to rewrite freely.

**Example — adding a nav item to the sidebar:**
```js
// frontend/js/templates/sidebar.js
const NAV_ITEMS = [
  { section: 'Workspace', items: [
    { route: '#/',        label: 'Dashboard',   icon: '#' },
    { route: '#/import',  label: 'Import Repo', icon: '+' },
    { route: '#/settings', label: 'Settings',   icon: '*' },  // ← add here
  ]},
];
```

---

## 3. Want to change a whole page's layout? → Edit the page file

```
frontend/js/pages/dashboard.js    — Route: #/
frontend/js/pages/import.js       — Route: #/import
frontend/js/pages/repoDetail.js   — Route: #/repo/:id
```

Each page file exports an object with two functions:

```js
export const dashboardPage = {
  topbar(params) { return renderTopbar({...}); },      // what shows in the top bar
  async render(container, params) { ... },              // what renders in the main content area
};
```

`render()` receives the actual DOM element to fill (`container.innerHTML = "..."`) and route params (e.g. `{ id: '3' }` for `#/repo/3`). You're free to rewrite the HTML structure inside `render()` completely — just keep calling `api.*` methods (see below) to get real data instead of hardcoding it.

---

## 4. Want to add a whole new page? → 3 steps

1. Create `frontend/js/pages/yourPage.js` following the same `{ topbar, render }` shape as the existing pages.
2. Import it in `frontend/js/app.js` and add one line to the `ROUTES` array:
   ```js
   { pattern: /^#\/your-route$/, page: yourPage, params: () => ({}) },
   ```
3. Add a nav link in `frontend/js/templates/sidebar.js`.

Nothing in the backend needs to change for a purely presentational new page.

---

## 5. Never touch this file directly in a page or template

```
frontend/js/api/client.js
```

This is the **only** file that calls `fetch()`. Every page imports `api` from here and calls methods like `api.getRepositories()` — never construct a URL or call `fetch` yourself inside a page or template file. This is what keeps the UI swappable: as long as you keep calling these same methods, you can rewrite every visual file without breaking data loading.

Current methods available:
```js
api.getRepositories()        // -> array of repos
api.importRepository(url)    // -> repo object
api.processRepository(id)    // -> repo object
api.getFiles(id)             // -> array of files
```

---

## File responsibility summary

| Layer | Folder | Safe to freely rewrite? |
|---|---|---|
| Styling | `css/style.css` | ✅ Yes — swap or edit freely |
| Reusable UI pieces | `js/templates/` | ✅ Yes — pure functions, no API calls |
| Page composition | `js/pages/` | ✅ Yes — just keep using `api.*` for data |
| Routing | `js/app.js` | ⚠️ Edit only to add/remove routes |
| API communication | `js/api/client.js` | ❌ Don't rewrite — this is the contract with the backend |
| Shell | `index.html` | ⚠️ Rarely needs changes — just mounts `#sidebar`/`#topbar`/`#content` |

---

## Not using vanilla JS? Want React/Vue instead?

The backend doesn't care. `app/main.py` serves whatever is in `frontend/` as static files via:
```python
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
```
Point a React/Vue build's output folder at `frontend/` (or change `FRONTEND_DIR` in `main.py`) and it'll work the same way — the API is a completely separate concern living under `/api/*`.
