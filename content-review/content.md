# davidlybeck.com — content dump for pre-launch review

Source: the `dev` branch (origin/dev at 64f1045), rendered by the running app and read from the served HTML; cover stickers were read from the live DOM in headless Chromium (1280×800) and tapped to capture reveals. Nothing here was taken from the templates. Headings in page bodies are demoted (page title = `##`, page heading = `###`).

Reading order: cover → the notebook pages in book order → metadata. The book has 15 pages on a phone (one at a time) and 12 on desktop (the 3 index pages — Contents, Projects, Hobbies — are replaced by a spread/section list). Both numbers are shown.

# 1. Cover

**Cover label:** David Lybeck  
**Button:** open  
**Header (visible on every screen once the book is open):** logo + “David Lybeck” (the page also has a hidden `<h1>` “David Lybeck”).  
**Footer / page indicator:** a tab wheel showing the current section and page, e.g. “About · p.1”. Screen-reader live text: “David Lybeck, page N of 12”. There is no other footer text.  
**Tabs on the wheel (in order):** About, Projects, Work, School, Hobbies, Say hi.

## Stickers (cover, back to front, 9 in all)

| # | Sticker | Visible label | What tapping reveals | Screen-reader label |
|---|---|---|---|---|
| 1 | Name tag | HELLO / my name is / David | Wipes the name and rewrites “David” in another handwriting font (5 fonts: Caveat, Permanent Marker, Homemade Apple, Gochi Hand, Nothing You Could Do). Text never changes. | HELLO my name is David. Tap to write it in another hand. |
| 2 | “Now” pill | NOW · AI tools at Denali | Each tap cycles: “NOW AI tools at Denali” → “2025 ScribbleScan LLC” → “2024 2nd Chair intern” → “2022 tennis coach” → back to “NOW AI tools at Denali”. | now AI tools at Denali. Tap for an earlier one. |
| 3 | Trail stamp (mountain) | (none — picture only) | A hiker climbs a trail; sun sets. Tap again for morning. No text. | Stamp of a mountain trail. Tap to go for a hike. |
| 4 | ScribbleScan pad | SCRIBBLESCAN | A pad “writes” a word, scans it, and types it out beside the label. Words, in turn: “hello”, “notes”, “ideas”, “hi there” (each shown once, then it rests). Drawing on the pad ‘scans’ the doodle and types “1 doodle, saved”. Canvas label: “Write or draw here”. Screen-reader announcement: “ScribbleScan read: <word>”. | (pad) Write or draw here |
| 5 | Puzzle box | PUZZLE BOX | A 3×3 sliding puzzle on the logo; on solving, the label changes to “solved!”. | Sliding puzzle; tiles “Tile 1” … “Tile 8” |
| 6 | 3D printer | (none — picture only) | Prints the logo layer by layer; tap to print again. No text. | 3D printer. Tap to print again. |
| 7 | Raccoon at a keyboard | (none — picture only) | Types a speech bubble, one per tap, in turn: “hi!” → “hello” → “hey there”. | A raccoon at a keyboard. Tap to say hi. |
| 8 | “Your sticker here” | your / sticker / here | Opens a dialog (see below) to draw or add a picture; stays in the visitor's browser only. | your sticker here. Tap to draw one or add a picture. |
| 9 | Tennis ball | (none — picture only) | Bounces / can be thrown. No text. | Tennis ball. Tap to bounce it, or throw it. |

### “Your sticker here” dialog (appears on tap)

```
Make your sticker

Draw on the sticker, or add a picture and draw on top. It stays in this browser only.

Add a picture
Clear
Cancel
Stick it on
```

Also labelled for screen readers: Drawing area; Pen color; Ink pen; Blue pen; Red pen; Green pen; Yellow pen; Shape; Circle; Rounded square; Star; Heart; Background color; White background; Lemon background; Pink background; Tangerine background; Mint background; Sky background. A “Take it off” button appears once a sticker is saved. Heading id: “Make your sticker”.

**Hint behaviour:** until a visitor touches a sticker, one sticker at a time plays a small quiet animation as a nudge. No text.

# 2. Notebook pages (book order)

## About · phone p.1 · desktop p.1 — David Lybeck

*Tab: About (colour: lemon). Page id `me`. Address: `/#about`. Contents-list line: “David Lybeck”.*

[image] `/static/dlybeck/dl-note.svg` — alt: “”
Hi, I'm David
### David Lybeck
I build AI tools at Denali, and on my own time I make things like ScribbleScan, puzzle boxes and this website.
- Now
  Innovation AI Developer at Denali
- Studied
  Computer science, University of Puget Sound, 2025
- Made
  ScribbleScan, from capstone to company
- Plays
  Tennis, since middle school

**Images on this page:**
- `/static/dlybeck/dl-note.svg` — alt: “”

## About · phone p.2 · desktop: not a page (replaced by a list/spread) — Contents

*Tab: About (colour: lemon). Page id `toc`. Address: `/#contents`. Contents-list line: “Contents”.*

### Contents
- [Projects](https://davidlybeck.com/#projects)
- [Work From coaching tennis to building AI tools.](https://davidlybeck.com/jobs)
- [School Schools I've gone to and classes I've taken.](https://davidlybeck.com/education/college)
- [Hobbies](https://davidlybeck.com/#hobbies)
- [Say hi](https://davidlybeck.com/#say-hi)
spin the wheel, or turn the page

Contents list (generated): Projects (p.3 phone); Work (p.9 phone); School (p.10 phone); Hobbies (p.11 phone); Say hi (p.15 phone).

**Links on this page:**
- Projects → https://davidlybeck.com/#projects
- Work From coaching tennis to building AI tools. → https://davidlybeck.com/jobs
- School Schools I've gone to and classes I've taken. → https://davidlybeck.com/education/college
- Hobbies → https://davidlybeck.com/#hobbies
- Say hi → https://davidlybeck.com/#say-hi

## Projects · phone p.3 · desktop: not a page (replaced by a list/spread) — Projects

*Tab: Projects (colour: sky). Page id `projects`. Address: `/#projects`. Contents-list line: “Projects”.*

5 entries
### Projects
Personal projects I've developed, and how they were made.
- [ScribbleScan Handwriting digitization, from a hosted product to a privacy-first experiment.](https://davidlybeck.com/projects/websites/scribblescan)
- [This website You're looking at it! Four versions so far, and how each was made.](https://davidlybeck.com/projects/websites/this_website)
- [NBA Prediction AI A neural network that called the 2024 playoffs with only 2 mistakes.](https://davidlybeck.com/projects/nba_predictions)
- [Digital Planner A calendar and to-do list built with a four-person class team.](https://davidlybeck.com/projects/websites/digital_planner)
- [Programs Software experiments and selected coursework, from sorts to a Connect 4 bot.](https://davidlybeck.com/projects/programs)

Section list lead: “Personal projects I've developed, and how they were made.”. Entries: ScribbleScan — Handwriting digitization, from a hosted product to a privacy-first experiment.; This website — You're looking at it! Four versions so far, and how each was made.; NBA Prediction AI — A neural network that called the 2024 playoffs with only 2 mistakes.; Digital Planner — A calendar and to-do list built with a four-person class team.; Programs — Software experiments and selected coursework, from sorts to a Connect 4 bot..

**Links on this page:**
- ScribbleScan Handwriting digitization, from a hosted product to a privacy-first experiment. → https://davidlybeck.com/projects/websites/scribblescan
- This website You're looking at it! Four versions so far, and how each was made. → https://davidlybeck.com/projects/websites/this_website
- NBA Prediction AI A neural network that called the 2024 playoffs with only 2 mistakes. → https://davidlybeck.com/projects/nba_predictions
- Digital Planner A calendar and to-do list built with a four-person class team. → https://davidlybeck.com/projects/websites/digital_planner
- Programs Software experiments and selected coursework, from sorts to a Connect 4 bot. → https://davidlybeck.com/projects/programs

## Projects · phone p.4 · desktop p.2 — ScribbleScan

*Tab: Projects (colour: sky). Page id `scribblescan`. Address: `/projects/websites/scribblescan`. Contents-list line: “ScribbleScan” — “Handwriting digitization, from a hosted product to a privacy-first experiment.”.*

2025 to now
### ScribbleScan
Handwriting digitization, from a hosted product to a privacy-first experiment.
[image] `/static/img/scribblescan/jul1.webp` — alt: “ScribbleScan web app showing a digitized handwritten page”
The finished hosted version, July 2025
ScribbleScan began as my 2025 capstone, grew into a hosted handwriting-digitization service and LLC, and is now preserved as a demo. It digitized handwritten pages while keeping images and other non-text elements in the resulting document.
[View the preserved demo](https://scribblescan.app)
#### How well it read
##### Character accuracy, five sample pages
ScribbleScan
95.10%
Pen to Print AI
83.46%
Baseline OCR
74.39%
A small project comparison, not a general benchmark.
#### What I'm exploring now
I'm now exploring what comes next for it, with privacy as the main goal. It's early work, not a finished product.
#### How it grew
- January 2025 · proposal
  The initial proposal I submitted for my capstone. It's interesting to see what I stuck with (like the export options) and what I changed (target audience, some features).
  [Read the proposal](https://davidlybeck.com/static/PDF/ScribbleScan_Proposal.pdf)
- February 7th 2025
  [image] `/static/img/scribblescan/feb7.webp` — alt: “First working version of ScribbleScan”
  The first working version. The results split each line into a section and showed them line by line. Rough, but it matched the design I had in mind, and I was very happy with it at the time.
- February 8th 2025
  [image] `/static/img/scribblescan/feb8.webp` — alt: “ScribbleScan a day later with larger tiles”
  Only a day later, but big UI improvements: much larger tiles, and the digitize button hides once clicked. That stayed in every later version.
- March 12th 2025
  [image] `/static/img/scribblescan/mar12.webp` — alt: “ScribbleScan with export and corrections”
  A month after the proof of concept: PDF export, copy to clipboard, corrections and accuracy scores. The focus shifted from a demo to a usable tool.
- April 28th 2025
  [image] `/static/img/scribblescan/apr28.webp` — alt: “ScribbleScan as presented for the capstone”
  The version I presented for my capstone: a batch page limit, Google sign-in and a toned down UI. Not a full product, but a finished tool.
- June 25th 2025
  [image] `/static/img/scribblescan/jun25.webp` — alt: “ScribbleScan as a hosted product”
  After graduating, ScribbleScan LLC full time: profiles and support, a cloud-hosted database, paid tiers and many smaller features. A complete product.
- July 1st 2025
  [image] `/static/img/scribblescan/jul1.webp` — alt: “ScribbleScan with demo mode”
  A week later I called it finished. The big addition was a demo mode, so anyone could try pre-calculated pages of tough handwriting without costing the service.

**Links on this page:**
- View the preserved demo → https://scribblescan.app
- Read the proposal → https://davidlybeck.com/static/PDF/ScribbleScan_Proposal.pdf

**Images on this page:**
- `/static/img/scribblescan/jul1.webp` — alt: “ScribbleScan web app showing a digitized handwritten page”
- `/static/img/scribblescan/feb7.webp` — alt: “First working version of ScribbleScan”
- `/static/img/scribblescan/feb8.webp` — alt: “ScribbleScan a day later with larger tiles”
- `/static/img/scribblescan/mar12.webp` — alt: “ScribbleScan with export and corrections”
- `/static/img/scribblescan/apr28.webp` — alt: “ScribbleScan as presented for the capstone”
- `/static/img/scribblescan/jun25.webp` — alt: “ScribbleScan as a hosted product”
- `/static/img/scribblescan/jul1.webp` — alt: “ScribbleScan with demo mode”

## Projects · phone p.5 · desktop p.3 — This website

*Tab: Projects (colour: sky). Page id `site`. Address: `/projects/websites/this_website`. Contents-list line: “This website” — “You're looking at it! Four versions so far, and how each was made.”.*

2022 to now
### This website
You're looking at it! Four versions so far, and how each was made.
[image] `/static/img/site/v3-1.webp` — alt: “Version 3: handwritten notes pinned to a tabletop”
Version 3, April 2026
- Dec 2022 · v1
  A hand-coded static layout that grew into an exploratory map.
- Jan 2025 · v2
  The map became the website, so you explore pages without opening them.
- Apr 2026 · v3
  Handwritten notes pinned to a tabletop, then seven visual themes.
- Nov 2026 · v4
  This one, rebuilt on my own design system.
#### Version 1
December 2022 to June 2023 · 8 snapshots
- [image] `/static/img/site/v1-1.webp` — alt: “First static layout for DavidLybeck.com version 1”
  December 23rd 2022
  This is what I considered to be the first base model of my website. None of the buttons worked. I was just trying to test out the rough idea and color scheme for how it should look.
- [image] `/static/img/site/v1-2.webp` — alt: “Version 1 with working buttons and page transitions”
  January 5th 2023
  At this point I had added working buttons and transitions between pages, as well as a new background image to see the scrolling from the transition effect.
- [image] `/static/img/site/v1-3.webp` — alt: “Version 1 with its updated background image”
  January 6th 2023
  For this change I had simply settled on a new background image to use throughout the website.
- [image] `/static/img/site/v1-4.webp` — alt: “Early radial navigation menu experiment”
  January 10th 2023
  I wanted my website to have something unique that stood out from other websites. So I decided to mess with the standard of menus and try this "radial" navigation menu that changes page to page.
- [image] `/static/img/site/v1-5.webp` — alt: “Version 1 radial menu placement experiment”
  January 12th 2023
  Here I had finalized the placement of the menu and menu button (currently a checkbox).
- [image] `/static/img/site/v1-6.webp` — alt: “Version 1 animated menu and home controls”
  January 13th 2023
  I added the animated menu button along with the old home button, and moved the page links into the new menu and made it functional.
- [image] `/static/img/site/v1-7.webp` — alt: “First functional map interface for version 1”
  June 13th 2023
  My first functional version of the map idea. Testing with friends and family, the new menu proved a bit confusing. With the rough map, people understood that the menu was "taking them somewhere", and the map subtly encouraged them to explore the entire website.
- [image] `/static/img/site/v1-8.webp` — alt: “Near-final version 1 map and navigation menu”
  June 18th 2023
  Close to the final version of the map and menu. I moved the map to the center of the menu to save space, moved the home button to the top so it's always visible, and added a "current location" marker and names for every discovered location.
#### Version 2
January 2025 · 6 snapshots
- [image] `/static/img/site/v2-1.webp` — alt: “First explorable tile map for DavidLybeck.com version 2”
  January 4th 2025
  Two big changes in mind. 1: Removing the previous map. It was big, slow, and broke the mobile experience. 2: Keep the feeling of exploring the website like it is a place. So instead of a large map taking up half the page, I made the map the website!
- [image] `/static/img/site/v2-2.webp` — alt: “Version 2 with a smaller navbar and house-shaped Home button”
  January 5th 2025
  The navbar size is drastically reduced, to make the blue less overwhelming and give tiles more space on mobile. The home button became a house shape.
- [image] `/static/img/site/v2-3.webp` — alt: “Version 2 sand background and navbar Home button”
  January 6th 2025
  I changed the background from white paper to sand, for a bit more depth without overwhelming the tiles. The home button moved into the navbar and hides when you are already home.
- [image] `/static/img/site/v2-4.webp` — alt: “Version 2 destination URLs and mini-window work”
  January 8th 2025
  This is when links were added. The url now changes depending on the tiles viewed, so people can jump straight to what they want to see.
- [image] `/static/img/site/v2-5.webp` — alt: “Version 2 functional mini-window viewer”
  January 10th 2025
  The mini windows got their full functionality, opening and closing seamlessly. They load a separate page and just change based on the tile clicked.
- [image] `/static/img/site/v2-6.webp` — alt: “Near-final version 2 with mini-window Back control”
  January 11th 2025
  Very close to the finished v2: a back button to navigate the mini windows, and cleaned up versions of all the pages.
#### Version 3
April to September 2026 · 3 snapshots
- [image] `/static/img/site/v3-1.webp` — alt: “Version 3 paper notes arranged on a wood tabletop”
  April 22nd 2026
  v3 threw out the tile grid and replaced it with a wall of handwritten notes pinned to a wood tabletop. Every tile is its own paper scrap, so the wall reads as a real, hand-built collection instead of a generated UI.
- [image] `/static/img/site/v3-2.webp` — alt: “Version 3 paper document viewer open over the Board”
  April 23rd 2026
  Opening a tile slides a cream paper in from the side. The close button turns into a back button when you've gone deeper, and tapping outside the paper closes it: one contextual button, no menu hamburger.
- [image] `/static/img/site/v3-3.webp` — alt: “Version 3 paper viewer showing the ScribbleScan project page”
  April 25th 2026
  The cream paper now slides up to close, like lifting it off the table, runs larger on desktop, and gets pushed down on mobile so the navbar and close button don't overlap it.
#### Seven themes
September 8th 2026
I kept the same map and rebuilt its visual layer into seven switchable worlds. The difficult part was not adding skins; it was preserving the same navigation, direct links, keyboard behavior and document flow across every theme.
- [image] `/static/img/site/theme-original.webp` — alt: “The Original theme”
  Original
- [image] `/static/img/site/theme-clouds.webp` — alt: “The Clouds theme”
  Clouds
- [image] `/static/img/site/theme-islands.webp` — alt: “The Islands theme”
  Islands
- [image] `/static/img/site/theme-lily-pads.webp` — alt: “The Lily pads theme”
  Lily pads
- [image] `/static/img/site/theme-planets.webp` — alt: “The Planets theme”
  Planets
- [image] `/static/img/site/theme-postcards.webp` — alt: “The Postcards theme”
  Postcards
- [image] `/static/img/site/theme-vinyl.webp` — alt: “The Vinyl theme”
  Vinyl

**Images on this page:**
- `/static/img/site/v3-1.webp` — alt: “Version 3: handwritten notes pinned to a tabletop”
- `/static/img/site/v1-1.webp` — alt: “First static layout for DavidLybeck.com version 1”
- `/static/img/site/v1-2.webp` — alt: “Version 1 with working buttons and page transitions”
- `/static/img/site/v1-3.webp` — alt: “Version 1 with its updated background image”
- `/static/img/site/v1-4.webp` — alt: “Early radial navigation menu experiment”
- `/static/img/site/v1-5.webp` — alt: “Version 1 radial menu placement experiment”
- `/static/img/site/v1-6.webp` — alt: “Version 1 animated menu and home controls”
- `/static/img/site/v1-7.webp` — alt: “First functional map interface for version 1”
- `/static/img/site/v1-8.webp` — alt: “Near-final version 1 map and navigation menu”
- `/static/img/site/v2-1.webp` — alt: “First explorable tile map for DavidLybeck.com version 2”
- `/static/img/site/v2-2.webp` — alt: “Version 2 with a smaller navbar and house-shaped Home button”
- `/static/img/site/v2-3.webp` — alt: “Version 2 sand background and navbar Home button”
- `/static/img/site/v2-4.webp` — alt: “Version 2 destination URLs and mini-window work”
- `/static/img/site/v2-5.webp` — alt: “Version 2 functional mini-window viewer”
- `/static/img/site/v2-6.webp` — alt: “Near-final version 2 with mini-window Back control”
- `/static/img/site/v3-1.webp` — alt: “Version 3 paper notes arranged on a wood tabletop”
- `/static/img/site/v3-2.webp` — alt: “Version 3 paper document viewer open over the Board”
- `/static/img/site/v3-3.webp` — alt: “Version 3 paper viewer showing the ScribbleScan project page”
- `/static/img/site/theme-original.webp` — alt: “The Original theme”
- `/static/img/site/theme-clouds.webp` — alt: “The Clouds theme”
- `/static/img/site/theme-islands.webp` — alt: “The Islands theme”
- `/static/img/site/theme-lily-pads.webp` — alt: “The Lily pads theme”
- `/static/img/site/theme-planets.webp` — alt: “The Planets theme”
- `/static/img/site/theme-postcards.webp` — alt: “The Postcards theme”
- `/static/img/site/theme-vinyl.webp` — alt: “The Vinyl theme”

## Projects · phone p.6 · desktop p.4 — NBA Prediction AI

*Tab: Projects (colour: sky). Page id `nba`. Address: `/projects/nba_predictions`. Contents-list line: “NBA Prediction AI” — “A neural network that called the 2024 playoffs with only 2 mistakes.”.*

2024 · partner project
### NBA Prediction AI
A neural network that called the 2024 playoffs with only 2 mistakes.
Live predictor
Home team
(dropdown) Loading teams
Away team
(dropdown) Loading teams
(button: Predict)
Select two teams to make a prediction. Data through May 2024.
- PyTorch
- TensorFlow
- Data through May 2024
[View the repository](https://github.com/mattzou1/NBA-predictor)
#### How it works
A partner project I worked on starting April 28th: a convolutional neural network trained on a custom-made data set of NBA stats. This model was built with PyTorch, and we also made a very similar version with TensorFlow.
From our testing it's pretty good at predicting the win or loss, and as expected it has a bit of trouble with the exact point differential. It predicted the 2024 NBA Playoffs with high accuracy, making only 2 mistakes while predicting multiple upsets.

**Predictor (filled in by script from results.json; 30 team codes in each dropdown):** ATL, BKN, BOS, CHA, CHI, CLE, DAL, DEN, DET, GSW, HOU, IND, LAC, LAL, MEM, MIA, MIL, MIN, NOP, NYK, OKC, ORL, PHI, PHX, POR, SAC, SAS, TOR, UTA, WAS. Prompt: “Select two teams to make a prediction. Data through May 2024.”. Result lines come from `results.json`; fallback “I can't predict this matchup.”; error “The predictor could not load its data. Try again later.”

**Links on this page:**
- View the repository → https://github.com/mattzou1/NBA-predictor

## Projects · phone p.7 · desktop p.5 — Digital Planner

*Tab: Projects (colour: sky). Page id `planner`. Address: `/projects/websites/digital_planner`. Contents-list line: “Digital Planner” — “A calendar and to-do list built with a four-person class team.”.*

2022 · class team
### Digital Planner
A calendar and to-do list built with a four-person class team.
A web app four other people and I built for our Software Engineering course over just over two months, split into two sprints. It taught us to code as a team with GitHub, Trello and daily meetings. The "final" product wasn't close to done, but we were happy with it, and I think of it as a proof of concept.
#### End of sprint 1
November 1st 2022
[video] `/static/img/planner/old.mp4` poster `/static/img/planner/old-poster.webp` — label: “Digital Planner at the end of sprint 1: assignments dragged onto a calendar”
I made assignments show up correctly when created, while a teammate built the add assignment menu. I also figured out and built drag and drop for assignments onto the calendar.
#### End of sprint 2
December 15th 2022
[video] `/static/img/planner/new.mp4` poster `/static/img/planner/new-poster.webp` — label: “Digital Planner at the end of sprint 2: events and assignments on a scrolling calendar”
Much more drag and drop: events alongside assignments, the calendar adjusting for different-length items without overlaps, calendar scrolling, and many smaller fixes.

**Images on this page:**
- `/static/img/planner/old.mp4` — alt: “Digital Planner at the end of sprint 1: assignments dragged onto a calendar”
- `/static/img/planner/new.mp4` — alt: “Digital Planner at the end of sprint 2: events and assignments on a scrolling calendar”

## Projects · phone p.8 · desktop p.6 — Programs

*Tab: Projects (colour: sky). Page id `programs`. Address: `/projects/programs`. Contents-list line: “Programs” — “Software experiments and selected coursework, from sorts to a Connect 4 bot.”.*

2021 to 2024
### Programs
Software projects, experiments, and selected coursework.
##### Coursework archive · 2024
2024 · Python
- [Negamax Connect 4 bot](https://github.com/Dlybeck/AI/tree/main/HW_2)
- [A* sliding puzzle solver](https://github.com/Dlybeck/AI/tree/main/HW_1)
- [Representative voting history by K-Means](https://github.com/Dlybeck/AI/tree/main/HW_5)
- [CNN cat vs dog detector](https://github.com/Dlybeck/AI/tree/main/HW_4)
- [Representative voting history by decision tree](https://github.com/Dlybeck/AI/blob/main/HW_3)
2024 · C
- [Parallel matrix multiplication](https://github.com/Dlybeck/cs475-hwk5-mmm)
- [Mini shell](https://github.com/Dlybeck/cs475-hwk4-os-dsh)
- [ls command recreation](https://github.com/Dlybeck/cs475-hwk3-ls2)
- Hash map
- Heap sort
#### Earlier coursework
2023 · Java
- [Red-black tree binary search](https://github.com/Dlybeck/Algorithms/tree/main/Assignment4/src)
- [Digraph and topological sort for strings](https://github.com/Dlybeck/Algorithms/tree/main/Assignment%206/src)
- Priority queue
2023 · Haskell
- [Evil Hangman demo](https://davidlybeck.com/static/programs/Assignments/Evilhangman.html)
- [Evil Hangman file](https://davidlybeck.com/static/programs/Haskell/EvilHangman.hs)
2023 · Prolog
- [Mass Covid test process](https://swish.swi-prolog.org/p/Covid-Test.pl)
2022 · Java
- [Selection sort](https://davidlybeck.com/static/programs/Java/SelectionSort.zip)
- [Quick sort](https://davidlybeck.com/static/programs/Java/QuickSort.zip)
- [Insertion sort](https://davidlybeck.com/static/programs/Java/InsertionSort.zip)
- [Heap sort](https://davidlybeck.com/static/programs/Java/HeapSort.zip)
2021 · Java
- [Bubble sort](https://davidlybeck.com/static/programs/Java/BubbleSort.zip)
- [Bitwise to hash](https://davidlybeck.com/static/programs/Java/BitwiseHash.zip)
Most have their code or a demo on the live site.

**Links on this page:**
- Negamax Connect 4 bot → https://github.com/Dlybeck/AI/tree/main/HW_2
- A* sliding puzzle solver → https://github.com/Dlybeck/AI/tree/main/HW_1
- Representative voting history by K-Means → https://github.com/Dlybeck/AI/tree/main/HW_5
- CNN cat vs dog detector → https://github.com/Dlybeck/AI/tree/main/HW_4
- Representative voting history by decision tree → https://github.com/Dlybeck/AI/blob/main/HW_3
- Parallel matrix multiplication → https://github.com/Dlybeck/cs475-hwk5-mmm
- Mini shell → https://github.com/Dlybeck/cs475-hwk4-os-dsh
- ls command recreation → https://github.com/Dlybeck/cs475-hwk3-ls2
- Red-black tree binary search → https://github.com/Dlybeck/Algorithms/tree/main/Assignment4/src
- Digraph and topological sort for strings → https://github.com/Dlybeck/Algorithms/tree/main/Assignment%206/src
- Evil Hangman demo → https://davidlybeck.com/static/programs/Assignments/Evilhangman.html
- Evil Hangman file → https://davidlybeck.com/static/programs/Haskell/EvilHangman.hs
- Mass Covid test process → https://swish.swi-prolog.org/p/Covid-Test.pl
- Selection sort → https://davidlybeck.com/static/programs/Java/SelectionSort.zip
- Quick sort → https://davidlybeck.com/static/programs/Java/QuickSort.zip
- Insertion sort → https://davidlybeck.com/static/programs/Java/InsertionSort.zip
- Heap sort → https://davidlybeck.com/static/programs/Java/HeapSort.zip
- Bubble sort → https://davidlybeck.com/static/programs/Java/BubbleSort.zip
- Bitwise to hash → https://davidlybeck.com/static/programs/Java/BitwiseHash.zip

## Work · phone p.9 · desktop p.7 — Work

*Tab: Work (colour: mint). Page id `work`. Address: `/jobs`. Contents-list line: “Work” — “From coaching tennis to building AI tools.”.*

Work · 8 roles
### Work
From coaching tennis to building AI tools.
- [image] `/static/img/work/denali.webp` — alt: “Denali Advanced Integration logo”
  August 2025 to now
  Innovation AI Developer
  Denali Advanced Integration
  Building and deploying internal AI tools to make day-to-day work at Denali faster, including agents for workflow automation and helping individuals and teams across the company adopt AI in their own roles. Driving select external projects on edge and mobile AI and computer vision.
- [image] `/static/img/work/scribblescan.webp` — alt: “ScribbleScan LLC logo”
  February 2025 to now
  Founder and developer
  ScribbleScan LLC
  I solo-developed a handwriting-digitization service that preserved images and other non-text elements in the resulting document. The website is still up as a demo, the live service is switched off, and I'm still working on what comes next.
#### Before Denali
- [image] `/static/img/work/2ndchair.webp` — alt: “2nd Chair logo”
  June to September 2024
  Software engineering intern
  2nd Chair
  Developed and researched software to improve AI document parsing, relevance and accuracy.
- [image] `/static/img/work/tech.webp` — alt: “University of Puget Sound logo”
  August 2022 to May 2025
  Technology Services Assistant II
  University of Puget Sound
  Answered phone calls and tickets from faculty, staff and incoming students about a range of technology issues, then either resolved them or routed them to the right team.
- [image] `/static/img/work/tcgc.webp` — alt: “Tacoma Country and Golf Club logo”
  July to August 2023
  Tennis instructor
  Tacoma Country and Golf Club
  Coached group lessons for children ages 6 to 15 with a range of abilities, along with private lessons for players of all ages.
#### Earlier
- [image] `/static/img/work/gtc.webp` — alt: “Galbraith Tennis Center logo”
  July to August 2023
  On court associate
  Galbraith Tennis Center
  Coached group lessons for adults and children ages 5 to 18 with a range of abilities.
- [image] `/static/img/work/ptc.webp` — alt: “Portland Tennis Center logo”
  June 2022 to January 2023
  Assistant coach
  Portland Tennis Center
  Helped coach group lessons for children ages 4 to 18 with a wide range of abilities.
- [image] `/static/img/work/tech.webp` — alt: “University of Puget Sound logo”
  January to May 2022
  Technology Services Assistant I
  University of Puget Sound
  Answered calls from faculty, staff and incoming students about technology issues, then either resolved them or routed them to the right team.

**Images on this page:**
- `/static/img/work/denali.webp` — alt: “Denali Advanced Integration logo”
- `/static/img/work/scribblescan.webp` — alt: “ScribbleScan LLC logo”
- `/static/img/work/2ndchair.webp` — alt: “2nd Chair logo”
- `/static/img/work/tech.webp` — alt: “University of Puget Sound logo”
- `/static/img/work/tcgc.webp` — alt: “Tacoma Country and Golf Club logo”
- `/static/img/work/gtc.webp` — alt: “Galbraith Tennis Center logo”
- `/static/img/work/ptc.webp` — alt: “Portland Tennis Center logo”
- `/static/img/work/tech.webp` — alt: “University of Puget Sound logo”

## School · phone p.10 · desktop p.8 — School

*Tab: School (colour: pink). Page id `school`. Address: `/education/college`. Contents-list line: “School” — “Schools I've gone to and classes I've taken.”.*

Class of 2025
### College
CS degree, math minor, tennis team.
[image] `/static/img/school/upscampus.webp` — alt: “University of Puget Sound campus”
As of May 2025 I hold a Bachelor of Science in Computer Science with a minor in Mathematics from the University of Puget Sound.
#### Classes taken
Computer science · 12
- [Intro to Computer Science](https://www.pugetsound.edu/courses/csci-161-introduction-computer-science)
- [Computer Science II](https://www.pugetsound.edu/courses/csci-261-computer-science-ii)
- [Software Engineering](https://www.pugetsound.edu/academics/computer-science/courses)
- [Assembly Language and Computer Architecture](https://www.pugetsound.edu/courses/csci-281-assembly-language-and-computer-architecture)
- [Programming Language Paradigms](https://www.pugetsound.edu/courses/csci-291-programming-language-paradigms)
- [Network Programming](https://www.pugetsound.edu/courses/csci-325-network-programming)
- [Algorithms and Data Structures](https://www.pugetsound.edu/courses/csci-361-algorithms-and-data-structures)
- [Intro to Artificial Intelligence](https://bulletin.pugetsound.edu/courses/0013121)
- [Operating Systems](https://www.pugetsound.edu/courses/csci-475-operating-systems)
- [Principles of Database Systems](https://www.pugetsound.edu/courses/csci-360-principles-database-systems)
- [Cryptography and Network Security](https://www.pugetsound.edu/courses/csci-425-advanced-topics-computer-science)
- [Capstone in Computer Science](https://www.pugetsound.edu/courses/csci-440-capstone-computer-science)
Math · 5
- [Calculus 1](https://www.pugetsound.edu/courses/math-180-calculus-and-analytic-geometry-i)
- [Calculus 2](https://www.pugetsound.edu/courses/math-181-calculus-and-analytic-geometry-ii)
- [Intro to Statistics](https://www.pugetsound.edu/courses/math-160-introduction-applied-statistics)
- [Discrete Math](https://www.pugetsound.edu/courses/math-210-introduction-mathematics-computer-science)
- [Linear Algebra](https://www.pugetsound.edu/courses/math-290-linear-algebra)
Business · 2
- [Principles of Management](https://library.pugetsound.edu/BUS305)
- [Law and Ethics in Business](https://www.pugetsound.edu/courses/bus-340-law-and-ethics-business-environment)
Other · 9
- [Intermediate Spanish](https://www.pugetsound.edu/courses/span-201-spanish-3)
- Scientific Controversies
- [Medical Narratives](https://www.pugetsound.edu/courses/conn-148-medical-narratives)
- [Markets and Macroeconomics](https://www.pugetsound.edu/courses/econ-101-introduction-markets-and-macroeconomics)
- [Astronomy](https://www.pugetsound.edu/academics/physics/courses)
- [Intro to Anthropology](https://www.pugetsound.edu/courses/soan-102-introduction-anthropology)
- [Modeling Earth's Climate](https://www.pugetsound.edu/courses/conn-350-modeling-earths-climate)
- [Survey of Western Music](https://www.pugetsound.edu/courses/mus-100-survey-western-music)
- [Ancient Greek Philosophy](https://www.pugetsound.edu/courses/phil-210-ancient-greek-philosophy)
#### Clubs and activities
[image] `/static/img/school/upstennis.webp` — alt: “University of Puget Sound tennis”
Tennis
I played all 4 years on the [UPS tennis team](https://loggerathletics.com/sports/mens-tennis/roster/2023), 2021 to 2025.
[image] `/static/img/school/maroonsociety.webp` — alt: “Maroon Society logo”
Maroon Society
A university organization that connects students and alumni, mostly through events around campus. I was a part of it for about 2 years, 2021 to 2024. [Maroon Society page](https://www.facebook.com/PugetSoundMaroonSociety/)
##### Agile management report
A report from my 2024 management class on agile management strategies, why they work and why they might not.
[View the report](https://davidlybeck.com/static/PDF/AgileManagement_Report_David.pdf)
Portland
#### Early education
Where it all started.
[image] `/static/img/school/ghs.webp` — alt: “Grant High School”
High school
Grant High School
[image] `/static/img/school/bms.webp` — alt: “Beaumont Middle School”
Middle school
Beaumont Middle School
[image] `/static/img/school/aes.webp` — alt: “Alameda Elementary School”
Elementary
Alameda Elementary School

**Links on this page:**
- Intro to Computer Science → https://www.pugetsound.edu/courses/csci-161-introduction-computer-science
- Computer Science II → https://www.pugetsound.edu/courses/csci-261-computer-science-ii
- Software Engineering → https://www.pugetsound.edu/academics/computer-science/courses
- Assembly Language and Computer Architecture → https://www.pugetsound.edu/courses/csci-281-assembly-language-and-computer-architecture
- Programming Language Paradigms → https://www.pugetsound.edu/courses/csci-291-programming-language-paradigms
- Network Programming → https://www.pugetsound.edu/courses/csci-325-network-programming
- Algorithms and Data Structures → https://www.pugetsound.edu/courses/csci-361-algorithms-and-data-structures
- Intro to Artificial Intelligence → https://bulletin.pugetsound.edu/courses/0013121
- Operating Systems → https://www.pugetsound.edu/courses/csci-475-operating-systems
- Principles of Database Systems → https://www.pugetsound.edu/courses/csci-360-principles-database-systems
- Cryptography and Network Security → https://www.pugetsound.edu/courses/csci-425-advanced-topics-computer-science
- Capstone in Computer Science → https://www.pugetsound.edu/courses/csci-440-capstone-computer-science
- Calculus 1 → https://www.pugetsound.edu/courses/math-180-calculus-and-analytic-geometry-i
- Calculus 2 → https://www.pugetsound.edu/courses/math-181-calculus-and-analytic-geometry-ii
- Intro to Statistics → https://www.pugetsound.edu/courses/math-160-introduction-applied-statistics
- Discrete Math → https://www.pugetsound.edu/courses/math-210-introduction-mathematics-computer-science
- Linear Algebra → https://www.pugetsound.edu/courses/math-290-linear-algebra
- Principles of Management → https://library.pugetsound.edu/BUS305
- Law and Ethics in Business → https://www.pugetsound.edu/courses/bus-340-law-and-ethics-business-environment
- Intermediate Spanish → https://www.pugetsound.edu/courses/span-201-spanish-3
- Medical Narratives → https://www.pugetsound.edu/courses/conn-148-medical-narratives
- Markets and Macroeconomics → https://www.pugetsound.edu/courses/econ-101-introduction-markets-and-macroeconomics
- Astronomy → https://www.pugetsound.edu/academics/physics/courses
- Intro to Anthropology → https://www.pugetsound.edu/courses/soan-102-introduction-anthropology
- Modeling Earth's Climate → https://www.pugetsound.edu/courses/conn-350-modeling-earths-climate
- Survey of Western Music → https://www.pugetsound.edu/courses/mus-100-survey-western-music
- Ancient Greek Philosophy → https://www.pugetsound.edu/courses/phil-210-ancient-greek-philosophy
- UPS tennis team → https://loggerathletics.com/sports/mens-tennis/roster/2023
- Maroon Society page → https://www.facebook.com/PugetSoundMaroonSociety/
- View the report → https://davidlybeck.com/static/PDF/AgileManagement_Report_David.pdf

**Images on this page:**
- `/static/img/school/upscampus.webp` — alt: “University of Puget Sound campus”
- `/static/img/school/upstennis.webp` — alt: “University of Puget Sound tennis”
- `/static/img/school/maroonsociety.webp` — alt: “Maroon Society logo”
- `/static/img/school/ghs.webp` — alt: “Grant High School”
- `/static/img/school/bms.webp` — alt: “Beaumont Middle School”
- `/static/img/school/aes.webp` — alt: “Alameda Elementary School”

## Hobbies · phone p.11 · desktop: not a page (replaced by a list/spread) — Hobbies

*Tab: Hobbies (colour: tangerine). Page id `hobbies`. Address: `/#hobbies`. Contents-list line: “Hobbies”.*

3 entries
### Hobbies
All my favorites! (Coding gets its own section.)
- [3D printing Puzzle boxes I designed, one with 45,000+ downloads. I bet you can't solve them.](https://davidlybeck.com/hobbies/3d_printing/puzzles)
- [Gaming Some of my favorites. I'll race you in Mario Kart Wii.](https://davidlybeck.com/hobbies/gaming)
- [Tennis I've played for as long as I remember. Let me know if you want to hit.](https://davidlybeck.com/hobbies/tennis)

Section list lead: “All my favorites! (Coding gets its own section.)”. Entries: 3D printing — Puzzle boxes I designed, one with 45,000+ downloads. I bet you can't solve them.; Gaming — Some of my favorites. I'll race you in Mario Kart Wii.; Tennis — I've played for as long as I remember. Let me know if you want to hit..

**Links on this page:**
- 3D printing Puzzle boxes I designed, one with 45,000+ downloads. I bet you can't solve them. → https://davidlybeck.com/hobbies/3d_printing/puzzles
- Gaming Some of my favorites. I'll race you in Mario Kart Wii. → https://davidlybeck.com/hobbies/gaming
- Tennis I've played for as long as I remember. Let me know if you want to hit. → https://davidlybeck.com/hobbies/tennis

## Hobbies · phone p.12 · desktop p.9 — 3D printing

*Tab: Hobbies (colour: tangerine). Page id `printing`. Address: `/hobbies/3d_printing/puzzles`. Contents-list line: “3D printing” — “Puzzle boxes I designed, one with 45,000+ downloads. I bet you can't solve them.”.*

Puzzles and models
### 3D printing
Here's some 3D models I've designed and printed for fun.
I always wanted more puzzle boxes to have around. So I started making them. I bet you can't solve them. Drag any model to turn it.
#### Puzzles · 5
- [3D model] `/static/3Dmodels/FirstPuzzle/FirstPuzzle.glb` (toggled: `/static/3Dmodels/FirstPuzzle/FirstPuzzle_Open.glb`) — alt: “My first puzzle box, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  (button: Open it)
  My first puzzle box
  45,000+ downloads
  [Printables](https://www.printables.com/model/40017-puzzle-box-easy-to-print-hard-to-solve) [Thingiverse](https://www.thingiverse.com/thing:4583356) [MyMiniFactory](https://www.myminifactory.com/object/3d-print-puzzle-box-easy-to-print-hard-to-solve-v1-132913) [Cults](https://cults3d.com/en/3d-model/game/puzzle-box-easy-print-hard-solution-version-1)
- [3D model] `/static/3Dmodels/CouchPuzzle/CouchPuzzle.glb` (toggled: `/static/3Dmodels/CouchPuzzle/CouchPuzzle_Open.glb`) — alt: “The couch puzzle box, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  (button: Open it)
  The couch puzzle box
  3,000+ downloads
  [Printables](https://www.printables.com/model/42742-couch-puzzle-box-moved-to-my-mini-factory-only-no-) [Thingiverse](https://www.thingiverse.com/thing:4628711) [Cults](https://cults3d.com/en/3d-model/game/couch-puzzle-box-sequential-puzzle-box)
- [3D model] `/static/3Dmodels/GiftPuzzzle/GiftPuzzle.glb` (toggled: `/static/3Dmodels/GiftPuzzzle/GiftPuzzle_Open.glb`) — alt: “The gift puzzle box, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  (button: Open it)
  The gift puzzle box
  800+ downloads
  [Printables](https://www.printables.com/model/325862-gift-puzzle-a-multi-step-puzzle-box) [Cults](https://cults3d.com/en/3d-model/game/gift-puzzle-a-multi-step-puzzle-box)
- [3D model] `/static/3Dmodels/BlockPuzzle/BlockPuzzle.glb` (toggled: `/static/3Dmodels/BlockPuzzle/BlockPuzzle_Solved.glb`) — alt: “Simple block puzzle, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  (button: Solve it)
  Simple block puzzle
  600+ downloads
  [Printables](https://www.printables.com/model/105727-simple-block-puzzle) [Thingiverse](https://www.thingiverse.com/thing:5174606) [MyMiniFactory](https://www.myminifactory.com/object/3d-print-simple-block-puzzle-201450) [Cults](https://cults3d.com/en/3d-model/game/simple-block-puzzle)
- [3D model] `/static/3Dmodels/SlidingPuzzle/SlidingPuzzle.glb` (toggled: `/static/3Dmodels/SlidingPuzzle/SlidingPuzzle_Open.glb`) — alt: “The sliding puzzle box, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  (button: Open it)
  The sliding puzzle box
  Private for now
#### Other models
Cases and organizers I needed, and a jewelry box. Drag any model to turn it.
- [3D model] `/static/3Dmodels/SamsungCase/S20FECase.glb` — alt: “Galaxy S20 FE case, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  Galaxy S20 FE case
  2,500+ downloads
  [Printables](https://www.printables.com/model/102978-samsung-galaxy-s20-fe-bumper-phone-case) [Thingiverse](https://www.thingiverse.com/thing:5171286) [MyMiniFactory](https://www.myminifactory.com/object/3d-print-samsung-galaxy-s20-fe-bumper-phone-case-201148) [Cults](https://cults3d.com/en/3d-model/gadget/dlybeck383)
- [3D model] `/static/3Dmodels/PixelCase/PixelCase.glb` — alt: “Pixel 3 case, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  Pixel 3 case
  300+ downloads
  [Thingiverse](https://www.thingiverse.com/thing:4197920) [Cults](https://cults3d.com/en/3d-model/gadget/x-case-minimal-google-pixel-3-case)
- [3D model] `/static/3Dmodels/ChargerOrganizer/ChargerOrganizer.glb` — alt: “Tech accessory organizer, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  Tech accessory organizer
  50+ downloads
  [Cults](https://cults3d.com/en/3d-model/tool/tech-organizer-dlybeck383)
- [3D model] `/static/3Dmodels/JewelryBox/JewelryBox.glb` (toggled: `/static/3Dmodels/JewelryBox/JewelryBox_Open.glb`) — alt: “Jewelry box, 3D model”, poster `/static/img/hobbies/model-icon.webp`
  (button: Open it)
  Jewelry box
  Private for now

**Links on this page:**
- Printables → https://www.printables.com/model/40017-puzzle-box-easy-to-print-hard-to-solve
- Thingiverse → https://www.thingiverse.com/thing:4583356
- MyMiniFactory → https://www.myminifactory.com/object/3d-print-puzzle-box-easy-to-print-hard-to-solve-v1-132913
- Cults → https://cults3d.com/en/3d-model/game/puzzle-box-easy-print-hard-solution-version-1
- Printables → https://www.printables.com/model/42742-couch-puzzle-box-moved-to-my-mini-factory-only-no-
- Thingiverse → https://www.thingiverse.com/thing:4628711
- Cults → https://cults3d.com/en/3d-model/game/couch-puzzle-box-sequential-puzzle-box
- Printables → https://www.printables.com/model/325862-gift-puzzle-a-multi-step-puzzle-box
- Cults → https://cults3d.com/en/3d-model/game/gift-puzzle-a-multi-step-puzzle-box
- Printables → https://www.printables.com/model/105727-simple-block-puzzle
- Thingiverse → https://www.thingiverse.com/thing:5174606
- MyMiniFactory → https://www.myminifactory.com/object/3d-print-simple-block-puzzle-201450
- Cults → https://cults3d.com/en/3d-model/game/simple-block-puzzle
- Printables → https://www.printables.com/model/102978-samsung-galaxy-s20-fe-bumper-phone-case
- Thingiverse → https://www.thingiverse.com/thing:5171286
- MyMiniFactory → https://www.myminifactory.com/object/3d-print-samsung-galaxy-s20-fe-bumper-phone-case-201148
- Cults → https://cults3d.com/en/3d-model/gadget/dlybeck383
- Thingiverse → https://www.thingiverse.com/thing:4197920
- Cults → https://cults3d.com/en/3d-model/gadget/x-case-minimal-google-pixel-3-case
- Cults → https://cults3d.com/en/3d-model/tool/tech-organizer-dlybeck383

**Images on this page:**
- `/static/img/hobbies/model-icon.webp` — alt: “My first puzzle box, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “The couch puzzle box, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “The gift puzzle box, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “Simple block puzzle, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “The sliding puzzle box, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “Galaxy S20 FE case, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “Pixel 3 case, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “Tech accessory organizer, 3D model”
- `/static/img/hobbies/model-icon.webp` — alt: “Jewelry box, 3D model”

## Hobbies · phone p.13 · desktop p.10 — Gaming

*Tab: Hobbies (colour: tangerine). Page id `gaming`. Address: `/hobbies/gaming`. Contents-list line: “Gaming” — “Some of my favorites. I'll race you in Mario Kart Wii.”.*

Shorter games
### Gaming
Check out some of my favorite video games! I'll race you in Mario Kart Wii.
When I have free time, video games are another thing I enjoy. I tend to like shorter games, so over the past few years I've cycled through a lot of them. Here's a list of games I've really enjoyed:
- [image] `/static/img/games/cyberpunk.webp` — alt: “Cyberpunk 2077 cover art”
- [image] `/static/img/games/highonlife.webp` — alt: “High on Life cover art”
- [image] `/static/img/games/mkwii.webp` — alt: “Mario Kart Wii cover art”
- [image] `/static/img/games/subnautica.webp` — alt: “Subnautica cover art”
- [image] `/static/img/games/subnauticabz.webp` — alt: “Subnautica: Below Zero cover art”
- [image] `/static/img/games/edithfinch.webp` — alt: “What Remains of Edith Finch cover art”
- [image] `/static/img/games/sot.webp` — alt: “Sea of Thieves cover art”
- [image] `/static/img/games/minecraft.webp` — alt: “Minecraft cover art”
- [image] `/static/img/games/nms.webp` — alt: “No Man's Sky cover art”
- [image] `/static/img/games/portal.webp` — alt: “Portal cover art”
- [image] `/static/img/games/portal2.webp` — alt: “Portal 2 cover art”
- [image] `/static/img/games/trackmania.webp` — alt: “Trackmania cover art”
- [image] `/static/img/games/valorant.webp` — alt: “Valorant cover art”
- [image] `/static/img/games/apex.webp` — alt: “Apex Legends cover art”
- [image] `/static/img/games/firewatch.webp` — alt: “Firewatch cover art”
- [image] `/static/img/games/outerwilds.webp` — alt: “Outer Wilds cover art”
- [image] `/static/img/games/titanfall.webp` — alt: “Titanfall cover art”
- [image] `/static/img/games/titanfall2.webp` — alt: “Titanfall 2 cover art”
- [image] `/static/img/games/road96.webp` — alt: “Road 96 cover art”
- [image] `/static/img/games/foreverskies.webp` — alt: “Forever Skies cover art”

**Images on this page:**
- `/static/img/games/cyberpunk.webp` — alt: “Cyberpunk 2077 cover art”
- `/static/img/games/highonlife.webp` — alt: “High on Life cover art”
- `/static/img/games/mkwii.webp` — alt: “Mario Kart Wii cover art”
- `/static/img/games/subnautica.webp` — alt: “Subnautica cover art”
- `/static/img/games/subnauticabz.webp` — alt: “Subnautica: Below Zero cover art”
- `/static/img/games/edithfinch.webp` — alt: “What Remains of Edith Finch cover art”
- `/static/img/games/sot.webp` — alt: “Sea of Thieves cover art”
- `/static/img/games/minecraft.webp` — alt: “Minecraft cover art”
- `/static/img/games/nms.webp` — alt: “No Man's Sky cover art”
- `/static/img/games/portal.webp` — alt: “Portal cover art”
- `/static/img/games/portal2.webp` — alt: “Portal 2 cover art”
- `/static/img/games/trackmania.webp` — alt: “Trackmania cover art”
- `/static/img/games/valorant.webp` — alt: “Valorant cover art”
- `/static/img/games/apex.webp` — alt: “Apex Legends cover art”
- `/static/img/games/firewatch.webp` — alt: “Firewatch cover art”
- `/static/img/games/outerwilds.webp` — alt: “Outer Wilds cover art”
- `/static/img/games/titanfall.webp` — alt: “Titanfall cover art”
- `/static/img/games/titanfall2.webp` — alt: “Titanfall 2 cover art”
- `/static/img/games/road96.webp` — alt: “Road 96 cover art”
- `/static/img/games/foreverskies.webp` — alt: “Forever Skies cover art”

## Hobbies · phone p.14 · desktop p.11 — Tennis

*Tab: Hobbies (colour: tangerine). Page id `tennis`. Address: `/hobbies/tennis`. Contents-list line: “Tennis” — “I've played for as long as I remember. Let me know if you want to hit.”.*

Since middle school
### Tennis
I've played for as long as I remember. Let me know if you want to hit.
[image] `/static/img/tennis/spin.webp` — alt: “David putting spin on a tennis ball”
[image] `/static/img/tennis/forehand.webp` — alt: “David hitting a forehand”
I've played competitively since middle school: four years on my high school's varsity team, four more on the University of Puget Sound team. Still hitting whenever I can.
##### Current rankings and profiles
[Puget Sound tennis profile](https://loggerathletics.com/sports/mens-tennis/roster/david-lybeck/8842) [World Tennis Number](https://worldtennisnumber.com/eng/player-profile?id=60a4ed89bf0fe5a69879dcdf) [Universal Tennis Rating](https://app.universaltennis.com/profiles/202815)

**Links on this page:**
- Puget Sound tennis profile → https://loggerathletics.com/sports/mens-tennis/roster/david-lybeck/8842
- World Tennis Number → https://worldtennisnumber.com/eng/player-profile?id=60a4ed89bf0fe5a69879dcdf
- Universal Tennis Rating → https://app.universaltennis.com/profiles/202815

**Images on this page:**
- `/static/img/tennis/spin.webp` — alt: “David putting spin on a tennis ball”
- `/static/img/tennis/forehand.webp` — alt: “David hitting a forehand”

## Say hi · phone p.15 · desktop p.12 — Say hi

*Tab: Say hi (colour: note). Page id `say`. Address: `/#say-hi`. Contents-list line: “Say hi”.*

### Say hi
GitHub
[github.com/Dlybeck](https://github.com/Dlybeck)
LinkedIn
[linkedin.com/in/davidlybeck](https://www.linkedin.com/in/davidlybeck)
Email
[Dlybeck383@gmail.com](mailto:Dlybeck383@gmail.com)
About this notebook
### How it's made
Drawn with dlybeck design, my own design system. The pages that turn are the whole interface.

**Links on this page:**
- github.com/Dlybeck → https://github.com/Dlybeck
- linkedin.com/in/davidlybeck → https://www.linkedin.com/in/davidlybeck
- Dlybeck383@gmail.com → mailto:Dlybeck383@gmail.com

**Desktop contents page numbers** (as shown in the generated contents list): projects p.2, work p.7, school p.8, hobbies p.9, say p.12.

# 3. Page titles, descriptions and social previews

All routes serve the same notebook and differ only in the metadata below. Every route also sets `og:type` website, `og:site_name` “David Lybeck”, `twitter:card` summary_large_image, and `og:image:alt` “David Lybeck, Innovation AI Developer, and a notebook cover covered in stickers”. The `<head>` also carries JSON-LD for a Person (name, jobTitle “Innovation AI Developer”, worksFor Denali Advanced Integration, sameAs GitHub + LinkedIn).

### `/`  (HTTP 200)
- title: David Lybeck | Innovation AI Developer
- meta description: David Lybeck is an Innovation AI Developer and software builder exploring AI, handwriting recognition, 3D design, tennis, and personal projects through an interactive portfolio.
- og:title: David Lybeck | Innovation AI Developer
- og:description: David Lybeck is an Innovation AI Developer and software builder exploring AI, handwriting recognition, 3D design, tennis, and personal projects through an interactive portfolio.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/

### `/jobs`  (HTTP 200)
- title: Work Experience | David Lybeck
- meta description: Explore David Lybeck's professional history, including his Innovation AI Developer role at Denali Advanced Integration since August 2025.
- og:title: Work Experience | David Lybeck
- og:description: Explore David Lybeck's professional history, including his Innovation AI Developer role at Denali Advanced Integration since August 2025.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/jobs

### `/education/college`  (HTTP 200)
- title: College | David Lybeck
- meta description: Explore David Lybeck's computer science degree, mathematics minor, coursework, tennis, and campus activities at the University of Puget Sound.
- og:title: College | David Lybeck
- og:description: Explore David Lybeck's computer science degree, mathematics minor, coursework, tennis, and campus activities at the University of Puget Sound.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/education/college

### `/education/early_education`  (HTTP 200)
- title: Early Education | David Lybeck
- meta description: Visit the schools and early education history that preceded David Lybeck's computer science work and personal projects.
- og:title: Early Education | David Lybeck
- og:description: Visit the schools and early education history that preceded David Lybeck's computer science work and personal projects.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/education/early_education

### `/education/agile_report`  (HTTP 200)
- title: Agile Management Report | David Lybeck
- meta description: Read David Lybeck's 2024 report exploring agile management strategies, benefits, and limitations.
- og:title: Agile Management Report | David Lybeck
- og:description: Read David Lybeck's 2024 report exploring agile management strategies, benefits, and limitations.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/education/agile_report

### `/hobbies/tennis`  (HTTP 200)
- title: Tennis | David Lybeck
- meta description: Explore David Lybeck's lifelong interest in competitive tennis, from school teams to current player profiles.
- og:title: Tennis | David Lybeck
- og:description: Explore David Lybeck's lifelong interest in competitive tennis, from school teams to current player profiles.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/hobbies/tennis

### `/hobbies/gaming`  (HTTP 200)
- title: Gaming | David Lybeck
- meta description: Browse a personal collection of video games David Lybeck has especially enjoyed playing.
- og:title: Gaming | David Lybeck
- og:description: Browse a personal collection of video games David Lybeck has especially enjoyed playing.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/hobbies/gaming

### `/hobbies/3d_printing/puzzles`  (HTTP 200)
- title: Puzzles | David Lybeck
- meta description: Explore interactive models of puzzle boxes designed and 3D printed by David Lybeck.
- og:title: Puzzles | David Lybeck
- og:description: Explore interactive models of puzzle boxes designed and 3D printed by David Lybeck.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/hobbies/3d_printing/puzzles

### `/hobbies/3d_printing/other_models`  (HTTP 200)
- title: Other Models | David Lybeck
- meta description: Explore interactive models of phone cases, organizers, and other objects designed by David Lybeck for 3D printing.
- og:title: Other Models | David Lybeck
- og:description: Explore interactive models of phone cases, organizers, and other objects designed by David Lybeck for 3D printing.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/hobbies/3d_printing/other_models

### `/projects/programs`  (HTTP 200)
- title: Programs | David Lybeck
- meta description: Explore current software projects, earlier experiments, and selected coursework built by David Lybeck.
- og:title: Programs | David Lybeck
- og:description: Explore current software projects, earlier experiments, and selected coursework built by David Lybeck.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/programs

### `/projects/nba_predictions`  (HTTP 200)
- title: NBA Predictions | David Lybeck
- meta description: Try an NBA game prediction demo built from a custom basketball statistics dataset and a neural network model.
- og:title: NBA Predictions | David Lybeck
- og:description: Try an NBA game prediction demo built from a custom basketball statistics dataset and a neural network model.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/nba_predictions

### `/projects/websites/digital_planner`  (HTTP 200)
- title: Digital Planner | David Lybeck
- meta description: Explore a collaborative digital planner project combining calendars and task management in one interface.
- og:title: Digital Planner | David Lybeck
- og:description: Explore a collaborative digital planner project combining calendars and task management in one interface.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/websites/digital_planner

### `/projects/websites/scribblescan`  (HTTP 200)
- title: ScribbleScan | David Lybeck
- meta description: Explore the preserved ScribbleScan demo and development history of David Lybeck's handwriting digitization project.
- og:title: ScribbleScan | David Lybeck
- og:description: Explore the preserved ScribbleScan demo and development history of David Lybeck's handwriting digitization project.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/websites/scribblescan

### `/projects/websites/this_website`  (HTTP 200)
- title: This Website | David Lybeck
- meta description: Explore how David Lybeck hand-built this interactive portfolio and how its unusual navigation evolved.
- og:title: This Website | David Lybeck
- og:description: Explore how David Lybeck hand-built this interactive portfolio and how its unusual navigation evolved.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/websites/this_website

### `/projects/websites/this_website/v1`  (HTTP 200)
- title: This Website v1 | David Lybeck
- meta description: See the first hand-coded generation of DavidLybeck.com evolve from a static layout into an exploratory map.
- og:title: This Website v1 | David Lybeck
- og:description: See the first hand-coded generation of DavidLybeck.com evolve from a static layout into an exploratory map.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/websites/this_website/v1

### `/projects/websites/this_website/v2`  (HTTP 200)
- title: This Website v2 | David Lybeck
- meta description: See the second hand-coded generation of DavidLybeck.com turn its map into the portfolio's primary interface.
- og:title: This Website v2 | David Lybeck
- og:description: See the second hand-coded generation of DavidLybeck.com turn its map into the portfolio's primary interface.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/websites/this_website/v2

### `/projects/websites/this_website/v3`  (HTTP 200)
- title: This Website v3 | David Lybeck
- meta description: See the third generation of DavidLybeck.com evolve from handwritten notes on a tabletop into seven visual themes.
- og:title: This Website v3 | David Lybeck
- og:description: See the third generation of DavidLybeck.com evolve from handwritten notes on a tabletop into seven visual themes.
- og:image: https://davidlybeck.com/static/img/social/home-notebook.webp
- canonical: https://davidlybeck.com/projects/websites/this_website/v3

# 4. Checks

## External links: 67 unique checked (HEAD, GET fallback, 10 s timeout, redirects followed, browser-like User-Agent)

_Context: all of these are bot-blocking responses to an automated client (Cults/Printables 403, LinkedIn 999, Facebook 400), not dead pages; open them in a browser to confirm. Every other external link, including Thingiverse, MyMiniFactory, GitHub, UPS and the tennis profiles, returned 200._

- **403** https://cults3d.com/en/3d-model/gadget/dlybeck383 — via GET (HEAD gave 403); on page(s): printing
- **403** https://cults3d.com/en/3d-model/gadget/x-case-minimal-google-pixel-3-case — via GET (HEAD gave 403); on page(s): printing
- **403** https://cults3d.com/en/3d-model/game/couch-puzzle-box-sequential-puzzle-box — via GET (HEAD gave 403); on page(s): printing
- **403** https://cults3d.com/en/3d-model/game/gift-puzzle-a-multi-step-puzzle-box — via GET (HEAD gave 403); on page(s): printing
- **403** https://cults3d.com/en/3d-model/game/puzzle-box-easy-print-hard-solution-version-1 — via GET (HEAD gave 403); on page(s): printing
- **403** https://cults3d.com/en/3d-model/game/simple-block-puzzle — via GET (HEAD gave 403); on page(s): printing
- **403** https://cults3d.com/en/3d-model/tool/tech-organizer-dlybeck383 — via GET (HEAD gave 403); on page(s): printing
- **400** https://www.facebook.com/PugetSoundMaroonSociety/ — via GET (HEAD gave 400); on page(s): school
- **999** https://www.linkedin.com/in/davidlybeck — via GET (HEAD gave 405); on page(s): say
- **403** https://www.printables.com/model/102978-samsung-galaxy-s20-fe-bumper-phone-case — via GET (HEAD gave 403); on page(s): printing
- **403** https://www.printables.com/model/105727-simple-block-puzzle — via GET (HEAD gave 403); on page(s): printing
- **403** https://www.printables.com/model/325862-gift-puzzle-a-multi-step-puzzle-box — via GET (HEAD gave 403); on page(s): printing
- **403** https://www.printables.com/model/40017-puzzle-box-easy-to-print-hard-to-solve — via GET (HEAD gave 403); on page(s): printing
- **403** https://www.printables.com/model/42742-couch-puzzle-box-moved-to-my-mini-factory-only-no- — via GET (HEAD gave 403); on page(s): printing

## Internal links and images: 121 unique checked against the local app

- none: every internal link, image, video, 3D model, PDF and route returned 200

## Typos, double spaces, odd spacing

- Automatic scan (double spaces, repeated words, space before punctuation): none found.
- No double spaces, repeated words or stray punctuation found in the served text; by reading the text I noticed only the items below (none are certain errors):
- **work → Denali / Tacoma / Galbraith dates:** “Tennis instructor, Tacoma Country and Golf Club — July to August 2023” and “On court associate, Galbraith Tennis Center — July to August 2023” overlap exactly; confirm both are right.
- **planner:** “A web app four other people and I built…” (five people) vs the summary “a four-person class team” (Projects list and the page's lead line). One of the two is off.
- **programs:** the lead line under the heading is “Software projects, experiments, and selected coursework.”, while the Contents/Projects list says “Software experiments and selected coursework, from sorts to a Connect 4 bot.” (different wording, not wrong). Closing line “Most have their code or a demo on the live site.” but “Hash map”, “Heap sort” (C, 2024) and “Priority queue” have no link.
- **scribblescan:** “a toned down UI” (usually “toned-down”). Straight quotes are used throughout (e.g. the "final" product, "radial", "taking them somewhere") rather than curly quotes.
- **gaming:** the lead (“Check out some of my favorite video games! I'll race you in Mario Kart Wii.”) repeats the list summary (“Some of my favorites. I'll race you in Mario Kart Wii.”).
- **contents:** the Projects and Hobbies entries in the Contents list have no one-line summary while the others do; harmless.
- **not visible to visitors:** the 3D model folder is spelled `GiftPuzzzle` (three z's) in `/static/3Dmodels/` — it works, but is a typo in the path.

## Mentions to review (customers/clients, “item capture”, ScribbleScan technical details)

- [accuracy] **ScribbleScan**: “##### Character accuracy, five sample pages”
- [accuracy] **ScribbleScan**: “95.10%”
- [accuracy] **ScribbleScan**: “83.46%”
- [ScribbleScan technical: model] **ScribbleScan**: “Baseline OCR”
- [accuracy] **ScribbleScan**: “74.39%”
- [accuracy] **ScribbleScan**: “A month after the proof of concept: PDF export, copy to clipboard, corrections and accuracy scores. The focus shifted from a demo to a usable tool.”
- [ScribbleScan technical: model] **Work**: “Building and deploying internal AI tools to make day-to-day work at Denali faster, including agents for workflow automation and helping individuals and teams across the company adopt AI in their own roles. Driving select external projects on edge and mobile AI and computer vision.”
- [company/external] **Work**: “Building and deploying internal AI tools to make day-to-day work at Denali faster, including agents for workflow automation and helping individuals and teams across the company adopt AI in their own roles. Driving select external projects on edge and mobile AI and computer vision.”
- [accuracy] **Work**: “Developed and researched software to improve AI document parsing, relevance and accuracy.”

_Scope of this scan: cover, About, Contents, Projects, ScribbleScan, Digital Planner, Programs, Work, School, Say hi and the metadata. The 3D printing, Gaming, Tennis, This-website and NBA pages were also read: their “model/trained/neural” hits are 3D models, the website's design history and the NBA project, not ScribbleScan, so they are left out._
- Also scanned: **no** occurrence of “customer”, “client”, “item capture”, “preprocessing”, or ScribbleScan model/training details anywhere (including meta descriptions and the cover). Nothing names a company's customer or client.
