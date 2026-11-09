# The scan pad reads handwriting with a small model, in the visitor's browser

The scan pad on the cover used to fake its scan. It now reads what a visitor writes
on it, with a real handwriting model running in a Web Worker (`static/js/notebook/stickers/`:
`scan.js` the sticker, `ink.js` strokes to lines, `ocr.js` and `ocr.worker.js` the reader).

## The model

TrOCR small, handwritten (`Xenova/trocr-small-handwritten`, MIT, trained on IAM handwriting
lines), 8-bit weights, through transformers.js 4.3.2 (ONNX Runtime).

Measured, not assumed (Chromium, written test lines drawn as pen strokes, six word and
sentence samples per font):

- Download: about 70 MB at 8-bit over the wire (23 MB image encoder, 41 MB text decoder, 1 MB
  tokenizer, 5.6 MB compressed ONNX Runtime; the runtime is 27 MB once unpacked). 16-bit is 124 MB
  and needs a GPU feature many devices lack. Full precision is 250 MB. This model has no 4-bit build.
- Accuracy: 8-bit and full precision read the same lines about equally (22 and 23 of 40 exact
  on a hard mixed set, including long sentences and names). Paying 3.6 times the bytes bought nothing.
- Time: about 1.2 s a line and 4.5 s to start on a desktop. With the page's main thread
  slowed 4x (phone-class), about 7 s a line and 8 s to start from cache.
- WebAssembly only. 8-bit weights on WebGPU ran correctly on a software adapter but were 17 times
  slower, and have not been measured on a real GPU (none was available to test on). Some 8-bit
  operators may fall back to the CPU on WebGPU, so it is left out until it has been measured; adding
  it back is a `device` change in `ocr.worker.js` plus a speed and accuracy check on real hardware.

So: 8-bit, the smallest build that reads as well as the biggest.

It reads one line at a time, and the pad has room for a word (sometimes two), so everything
written on it is read as one line, however tall it is written and however many ruled lines it
crosses. Strokes are kept as points, cropped tightly to the ink and redrawn large in thin dark
ink on white before reading. This matters a great deal: the same strokes at on-screen size and
thickness read as nonsense. (An earlier version cut the writing into slices at the ruled lines;
a word written big across them came back as three lines of invented text.)

The answer is shown only if it is believable for the ink: it must contain a letter or digit, be
at most two words and 24 characters, and be no longer than the ink could hold. Otherwise the pad
says "Couldn't read that. Try again" rather than show the model's guess.

## Loading

The reader is fetched in the background once the page has loaded and gone idle (1.5 s after the
load event, then at the browser's first idle moment), so most visitors find it ready. This is a
download of about 70 MB with no interaction, from `cdn.jsdelivr.net` and `huggingface.co`, so
those hosts see the visitor's IP address and user agent and the site's origin as referrer. It
never shows anything until the pad is touched; then the pad joins the load from where it has got
to. The checks run when the preload is scheduled and again just before it starts. The preload is
skipped, and the model loads only when someone writes on the pad, when:

- the browser reports Save-Data, a cellular link, or an effective type of 3g or slower;
- the device looks weak: `deviceMemory` of 2 GB or less, or 4 or fewer logical cores;
- the browser does not report its link at all (Safari and Firefox do not) and the pointer is
  coarse (a phone or tablet that might be on cellular);
- the cover is not shut when the page loads (a deep link to a page; the pad is not in view);
- the notebook is in its phone layout (`nb--phone`, checked again just before the load starts). A phone may be
  on mobile data whatever the browser reports, so it never preloads; the reader loads on the first stroke or scan;
- the tab is hidden; it waits until the tab is shown.

On a device with 1 GB of memory or less (where the browser reports it) reading is simply off:
the pad is a drawing pad with the note below, and nothing is loaded even on a first stroke.

Weights come from Hugging Face at a pinned revision, the library and its runtime from jsDelivr
at exact versions (the runtime is 27 MB uncompressed, too heavy for the repository). The
browser's Cache API keeps the weights, so the second visit downloads nothing. The page has no
CSP, and both hosts send CORS headers. A dynamic `import()` cannot carry a subresource-integrity
hash, so the library is trusted at its pinned version; it runs in a worker, which has no access
to the page's DOM or storage.

## Switching itself off

The site must never lag because of the pad. While the reader loads or reads, the page is
watched, and the reader stops (the worker is terminated and the model unloaded) if, within any
4 seconds, any of these happens: five frames arrive 100 ms or more late; one frame is 800 ms
late; or long tasks (50 ms or more each) add up to 1.2 s. The pad then stays a drawing pad and
says "Reading is off on this device" (not an error, no retry). The switch-off is remembered in
`sessionStorage` for the visit, so no later page tries again. Hidden tabs are ignored.

## Why this is an exception to "no CDN"

`AGENTS.md` says scripts are served from `static/`. This is the one exception: the weights
cannot live in git, and the runtime alone is bigger than everything else in `static/vendor`
put together. The exception is limited to the pad, pinned, skipped on metered and weak devices,
and the pad says so and offers a retry if a host is unreachable. If either host proves unreliable, serve the files
from a bucket we control; only the two URLs in `ocr.worker.js` change.

## What it cannot do

It reads tidy handwriting, one to four short lines. It misreads sloppy writing, similar
letters ("hi there" can come back as "li there") and uncommon words, and a visitor sees
exactly what it returned.
