# Dev Dashboard V2 - Discovery Questionnaire

Please fill out this form so I can design the optimal v2 architecture for your needs.

---

## 🎯 Vision & Goals

### 1. Primary Use Case
**What is the #1 thing you want to do with this dashboard on mobile?**
- [x] Access Claude AI terminal for coding on-the-go
- [ ] Monitor/manage development servers remotely
- [ ] Quick edits and file browsing
- [ ] Full development workflow replacement
- [ ] Other: _______________

### 2. Device Priority
**Which devices matter most? (Rank 1-3, 1 = highest priority)**
- iPhone (Safari): _3_
- Android (Chrome): _1_
- iPad: _4_
- Desktop: _2_

### 3. Network Environment
**Where will you primarily use this?**
- [ ] On cellular data (need to minimize data usage)
- [x] On WiFi (performance over data savings)
- [ ] Mixed

---

## 📱 Mobile Experience Preferences

### 4. Navigation Style
**How should users switch between terminal and preview on mobile?**
- [x] Swipe gestures (current approach)
- [ ] Bottom tab bar (like iOS apps)
- [ ] Dropdown/hamburger menu
- [ ] Full-screen modal approach (one thing at a time)
- [ ] Other idea: _______________

### 5. Mobile Toolbar
**The keyboard shortcut toolbar - do you actually use it?**
- [x, it seems needed on mobile devices becasue of a lack of keyboard for commands?] Yes, it's essential
- [ ] Sometimes, but could be simplified
- [ ] No, I'd rather just type
- [ ] Replace with something else: _______________

**If keeping it, what's your priority?**
- [ ] More shortcuts (willing to scroll/swipe between pages)
- [ ] Fewer shortcuts (all visible at once)
- [ ] Context-aware shortcuts (change based on what's active)

### 6. Touch Interactions
**What feels most natural to you on mobile?**
- [ ] Tap to switch views, swipe to navigate within
- [ ] Swipe to switch everything
- [ ] Buttons only (no gestures)
- [x] Mix: I don't quite understand the options, but I was imagining swiping between modes/windows with buttons to control them within.

---

## ⚡ Performance & Constraints

### 7. Loading Speed
**What's acceptable for initial page load on mobile?**
- [ ] <1 second (need instant)
- [ ] 1-3 seconds (reasonable)
- [ ] 3-5 seconds (fine if feature-rich)
- [x] Don't care, load everything

### 8. Data Usage
**Is cellular data usage a concern?**
- [ ] Yes, minimize JS/CSS bundle sizes
- [ ] Somewhat - be reasonable
- [x] No, load whatever makes it work best

### 9. Browser Compatibility
**Do you need to support older browsers?**
- [ ] Latest iOS Safari only
- [ ] Latest Chrome/Safari only
- [x] Need to support 2-3 years back
- [ ] Maximum compatibility

---

## 🏗️ Technical Preferences

### 10. Complexity Tolerance
**How complex of a rebuild are you comfortable with?**
- [ ] Minimal changes - fix current architecture
- [ ] Moderate - refactor into components
- [x] Major - complete rewrite with modern framework
- [x] Whatever works best, I trust your judgment

### 11. Framework Opinion
**If we use a framework, which sounds better?**
- [ ] None - keep it vanilla JS (current)
- [ ] Alpine.js (lightweight, minimal learning curve)
- [ ] HTMX (server-driven, minimal JS)
- [ ] React/Preact (component-based, industry standard)
- [ ] Vue (progressive, easier than React)
- [ ] Svelte (compiles away, smallest bundle)
- [x] I don't know - you decide

### 12. Build Process
**Are you okay with adding a build step?**
- [ ] Yes - npm, bundling, minification, etc.
- [ ] Maybe - if it's simple (single command)
- [ ] No - must work without build tools
- [ ] Don't care
 I don't understand what you mean

---

## 🎨 UI/UX Priorities

### 13. Current Pain Points
**What frustrates you most about the current mobile experience? (Check all that apply)**
- [x] Blank/white screens
- [x] Buttons don't work
- [x] Swipe gestures unreliable
- [x] Toolbar takes too much space
- [ ] Terminal text too small
- [x] Can't select/copy text easily
- [x] Keyboard pops up and breaks layout
- [ ] Switching views is confusing
- [ ] Other: _______________

### 14. Essential Features
**What MUST work perfectly on mobile? (Rank 1-5, 1 = critical)**
- Terminal access: _1_
- File browsing: _2_
- Code preview: _3_
- Logs viewing: _5_
- Quick keyboard shortcuts: _4_

### 15. Nice-to-Haves
**What would make this amazing but isn't required?**
- [ ] Offline support
- [x] Multiple terminal tabs
- [] Split screen (terminal + preview)
- [ ] Voice commands
- [x] Haptic feedback on actions
- [ ] Dark/light theme auto-switch
- [ ] Other: _______________

---

## 🔧 Development Workflow

### 16. Testing Access
**Can you easily test on real devices?**
- [x] Yes - I have iPhone/Android for testing
- [ ] Limited - only have one device
- [ ] No - only desktop/simulator
- [ ] I can test but hate doing it

### 17. Deployment
**How do you deploy updates?**
- [x] Git push → Cloud Run auto-deploys
- [ ] Manual deployment process
- [ ] Other: _______________

**How often do you want to deploy?**
- [ ] Multiple times per day (need hot reload / fast iteration)
- [x] Daily
- [ ] Weekly
- [ ] Rarely (stability over features)

---

## 💭 Open-Ended

### 18. Inspiration
**Are there any mobile apps or websites whose UX you love?**

Example: "I love how VS Code mobile handles tabs" or "Termius app's keyboard shortcuts"

I like vs code a lot in terms of how everything works, but its too complicated with features I don't use

### 19. Deal Breakers
**What absolutely cannot change?**

Example: "Must keep the dark theme" or "Can't lose terminal persistence"

I want the davidlybeck.com looking theme to stay, even with light and dark mode. Kind of like tehre is now
### 20. Dream Feature
**If you could wave a magic wand, what's the ONE thing you wish this dashboard could do?**

Persistance across devices, being able to stop one session on my phone and seamlessly continue on my pc. Or even at the same time

---

## 📊 Your Responses Summary

Once filled out, save this file and let me know. I'll use your answers to design a v2 architecture that actually solves your problems instead of creating new ones.

**Current Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete

