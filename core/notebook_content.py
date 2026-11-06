"""Repeated content for the notebook pages (wording moved from the old templates).

Prose that belongs to one page lives in that page's template; lists that a
page loops over live here.
"""

from __future__ import annotations

JOBS = [{'logo': 'denali',
  'width': 240,
  'height': 149,
  'org': 'Denali Advanced Integration',
  'role': 'Innovation AI Developer',
  'when': 'August 2025 to now',
  'text': 'Building and deploying internal AI tools to make day-to-day work at Denali faster, '
          'including agents for workflow automation and helping individuals and teams across the '
          'company adopt AI in their own roles. Driving select external projects on edge and '
          'mobile AI and computer vision.'},
 {'logo': 'scribblescan',
  'width': 240,
  'height': 45,
  'org': 'ScribbleScan LLC',
  'role': 'Founder and developer',
  'when': 'February 2025 to April 2026',
  'text': 'I solo-developed a handwriting-digitization service that preserved images and other '
          'non-text elements in the resulting document. The company and original service have '
          'since closed, and a preserved demo remains.'},
 {'logo': '2ndchair',
  'width': 240,
  'height': 99,
  'org': '2nd Chair',
  'role': 'Software engineering intern',
  'when': 'June to September 2024',
  'text': 'Developed and researched software to improve AI document parsing, relevance and '
          'accuracy.'},
 {'logo': 'tech',
  'width': 240,
  'height': 102,
  'org': 'University of Puget Sound',
  'role': 'Technology Services Assistant II',
  'when': 'August 2022 to May 2025',
  'text': 'Answered phone calls and tickets from faculty, staff and incoming students about a '
          'range of technology issues, then either resolved them or routed them to the right '
          'team.'},
 {'logo': 'tcgc',
  'width': 225,
  'height': 225,
  'org': 'Tacoma Country and Golf Club',
  'role': 'Tennis instructor',
  'when': 'July to August 2023',
  'text': 'Coached group lessons for children ages 6 to 15 with a range of abilities, along with '
          'private lessons for players of all ages.'},
 {'logo': 'gtc',
  'width': 240,
  'height': 240,
  'org': 'Galbraith Tennis Center',
  'role': 'On court associate',
  'when': 'July to August 2023',
  'text': 'Coached group lessons for adults and children ages 5 to 18 with a range of abilities.'},
 {'logo': 'ptc',
  'width': 240,
  'height': 117,
  'org': 'Portland Tennis Center',
  'role': 'Assistant coach',
  'when': 'June 2022 to January 2023',
  'text': 'Helped coach group lessons for children ages 4 to 18 with a wide range of abilities.'},
 {'logo': 'tech',
  'width': 240,
  'height': 102,
  'org': 'University of Puget Sound',
  'role': 'Technology Services Assistant I',
  'when': 'January to May 2022',
  'text': 'Answered calls from faculty, staff and incoming students about technology issues, then '
          'either resolved them or routed them to the right team.'}]

COURSES = [{'group': 'Computer science',
  'classes': ['Intro to Computer Science',
              'Computer Science II',
              'Software Engineering',
              'Assembly Language and Computer Architecture',
              'Programming Language Paradigms',
              'Network Programming',
              'Algorithms and Data Structures',
              'Intro to Artificial Intelligence',
              'Operating Systems',
              'Principles of Database Systems',
              'Cryptography and Network Security',
              'Capstone in Computer Science']},
 {'group': 'Math',
  'classes': ['Calculus 1',
              'Calculus 2',
              'Intro to Statistics',
              'Discrete Math',
              'Linear Algebra']},
 {'group': 'Business', 'classes': ['Principles of Management', 'Law and Ethics in Business']},
 {'group': 'Other',
  'classes': ['Intermediate Spanish',
              'Scientific Controversies',
              'Medical Narratives',
              'Markets and Macroeconomics',
              'Astronomy',
              'Intro to Anthropology',
              "Modeling Earth's Climate",
              'Survey of Western Music',
              'Ancient Greek Philosophy']}]

ARCHIVE = [{'label': '2024 · Python',
  'items': ['Negamax Connect 4 bot',
            'A* sliding puzzle solver',
            'Representative voting history by K-Means',
            'CNN cat vs dog detector',
            'Representative voting history by decision tree']},
 {'label': '2024 · C',
  'items': ['Parallel matrix multiplication',
            'Mini shell',
            'ls command recreation',
            'Hash map',
            'Heap sort']},
 {'label': '2023 · Java',
  'items': ['Red-black tree binary search',
            'Digraph and topological sort for strings',
            'Priority queue']},
 {'label': '2023 · Haskell', 'items': ['Evil Hangman']},
 {'label': '2023 · Prolog', 'items': ['Mass Covid test process']},
 {'label': '2022 · Java', 'items': ['Selection sort', 'Quick sort', 'Insertion sort', 'Heap sort']},
 {'label': '2021 · Java', 'items': ['Bubble sort', 'Bitwise to hash']}]

VERSIONS = [{'id': 'v1',
  'name': 'Version 1',
  'when': 'December 2022 to June 2023',
  'steps': [{'n': 1,
             'height': 444,
             'date': 'December 23rd 2022',
             'text': 'This is what I considered to be the first base model of my website. None of '
                     'the buttons worked. I was just trying to test out the rough idea and color '
                     'scheme for how it should look.'},
            {'n': 2,
             'height': 450,
             'date': 'January 5th 2023',
             'text': 'At this point I had added working buttons and transitions between pages, as '
                     'well as a new background image to see the scrolling from the transition '
                     'effect.'},
            {'n': 3,
             'height': 450,
             'date': 'January 6th 2023',
             'text': 'For this change I had simply settled on a new background image to use '
                     'throughout the website.'},
            {'n': 4,
             'height': 450,
             'date': 'January 10th 2023',
             'text': 'I wanted my website to have something unique that stood out from other '
                     'websites. So I decided to mess with the standard of menus and try this '
                     '"radial" navigation menu that changes page to page.'},
            {'n': 5,
             'height': 450,
             'date': 'January 12th 2023',
             'text': 'Here I had finalized the placement of the menu and menu button (currently a '
                     'checkbox).'},
            {'n': 6,
             'height': 449,
             'date': 'January 13th 2023',
             'text': 'I added the animated menu button along with the old home button, and moved '
                     'the page links into the new menu and made it functional.'},
            {'n': 7,
             'height': 451,
             'date': 'June 13th 2023',
             'text': 'My first functional version of the map idea. Testing with friends and '
                     'family, the new menu proved a bit confusing. With the rough map, people '
                     'understood that the menu was "taking them somewhere", and the map subtly '
                     'encouraged them to explore the entire website.'},
            {'n': 8,
             'height': 450,
             'date': 'June 18th 2023',
             'text': 'Close to the final version of the map and menu. I moved the map to the '
                     "center of the menu to save space, moved the home button to the top so it's "
                     'always visible, and added a "current location" marker and names for every '
                     'discovered location.'}]},
 {'id': 'v2',
  'name': 'Version 2',
  'when': 'January 2025',
  'steps': [{'n': 1,
             'height': 428,
             'date': 'January 4th 2025',
             'text': 'Two big changes in mind. 1: Removing the previous map. It was big, slow, and '
                     'broke the mobile experience. 2: Keep the feeling of exploring the website '
                     'like it is a place. So instead of a large map taking up half the page, I '
                     'made the map the website!'},
            {'n': 2,
             'height': 427,
             'date': 'January 5th 2025',
             'text': 'The navbar size is drastically reduced, to make the blue less overwhelming '
                     'and give tiles more space on mobile. The home button became a house shape.'},
            {'n': 3,
             'height': 428,
             'date': 'January 6th 2025',
             'text': 'I changed the background from white paper to sand, for a bit more depth '
                     'without overwhelming the tiles. The home button moved into the navbar and '
                     'hides when you are already home.'},
            {'n': 4,
             'height': 427,
             'date': 'January 8th 2025',
             'text': 'This is when links were added. The url now changes depending on the tiles '
                     'viewed, so people can jump straight to what they want to see.'},
            {'n': 5,
             'height': 428,
             'date': 'January 10th 2025',
             'text': 'The mini windows got their full functionality, opening and closing '
                     'seamlessly. They load a separate page and just change based on the tile '
                     'clicked.'},
            {'n': 6,
             'height': 428,
             'date': 'January 11th 2025',
             'text': 'Very close to the finished v2: a back button to navigate the mini windows, '
                     'and cleaned up versions of all the pages.'}]},
 {'id': 'v3',
  'name': 'Version 3',
  'when': 'April to September 2026',
  'steps': [{'n': 1,
             'height': 500,
             'date': 'April 22nd 2026',
             'text': 'v3 threw out the tile grid and replaced it with a wall of handwritten notes '
                     'pinned to a wood tabletop. Every tile is its own paper scrap, so the wall '
                     'reads as a real, hand-built collection instead of a generated UI.'},
            {'n': 2,
             'height': 500,
             'date': 'April 23rd 2026',
             'text': 'Opening a tile slides a cream paper in from the side. The close button turns '
                     "into a back button when you've gone deeper, and tapping outside the paper "
                     'closes it: one contextual button, no menu hamburger.'},
            {'n': 3,
             'height': 500,
             'date': 'April 25th 2026',
             'text': 'The cream paper now slides up to close, like lifting it off the table, runs '
                     'larger on desktop, and gets pushed down on mobile so the navbar and close '
                     "button don't overlap it."},
            {'n': 0,
             'height': 0,
             'date': 'September 8th 2026',
             'text': 'I kept the same map and rebuilt its visual layer into seven switchable '
                     'worlds. The difficult part was not adding skins; it was preserving the same '
                     'navigation, direct links, keyboard behavior and document flow across every '
                     'theme.'}]}]

THEMES = [{'id': 'original', 'name': 'Original'},
 {'id': 'clouds', 'name': 'Clouds'},
 {'id': 'islands', 'name': 'Islands'},
 {'id': 'lily-pads', 'name': 'Lily pads'},
 {'id': 'planets', 'name': 'Planets'},
 {'id': 'postcards', 'name': 'Postcards'},
 {'id': 'vinyl', 'name': 'Vinyl'}]

GAMES = [{'id': 'Cyberpunk', 'name': 'Cyberpunk 2077'},
 {'id': 'HighOnLife', 'name': 'High on Life'},
 {'id': 'MKWii', 'name': 'Mario Kart Wii'},
 {'id': 'Subnautica', 'name': 'Subnautica'},
 {'id': 'SubnauticaBZ', 'name': 'Subnautica: Below Zero'},
 {'id': 'EdithFinch', 'name': 'What Remains of Edith Finch'},
 {'id': 'SoT', 'name': 'Sea of Thieves'},
 {'id': 'Minecraft', 'name': 'Minecraft'},
 {'id': 'NMS', 'name': "No Man's Sky"},
 {'id': 'Portal', 'name': 'Portal'},
 {'id': 'Portal2', 'name': 'Portal 2'},
 {'id': 'Trackmania', 'name': 'Trackmania'},
 {'id': 'Valorant', 'name': 'Valorant'},
 {'id': 'Apex', 'name': 'Apex Legends'},
 {'id': 'Firewatch', 'name': 'Firewatch'},
 {'id': 'OuterWilds', 'name': 'Outer Wilds'},
 {'id': 'Titanfall', 'name': 'Titanfall'},
 {'id': 'Titanfall2', 'name': 'Titanfall 2'},
 {'id': 'road96', 'name': 'Road 96'},
 {'id': 'ForeverSkies', 'name': 'Forever Skies'}]
