# The scan pad reads handwriting with a small model, in the visitor's browser

The ScribbleScan pad on the cover used to fake its scan. It now reads what a visitor writes
on it, with a real handwriting model running in a Web Worker (`static/js/notebook/stickers/`:
`scan.js` the sticker, `ink.js` strokes to lines, `ocr.js` and `ocr.worker.js` the reader).

## The model

TrOCR small, handwritten (`Xenova/trocr-small-handwritten`, MIT, trained on IAM handwriting
lines), 8-bit weights, through transformers.js 4.3.2 (ONNX Runtime).

Measured, not assumed (Chromium, written test lines drawn as pen strokes, six word and
sentence samples per font):

- Download: 69.6 MB at 8-bit (23 MB image encoder, 41 MB text decoder, 1 MB tokenizer, 5.6 MB
  runtime). 16-bit is 124 MB and needs a GPU feature many devices lack. Full precision is 250 MB.
  This model has no 4-bit build.
- Accuracy: 8-bit and full precision read the same lines about equally (22 and 23 of 40 exact
  on a hard mixed set, including long sentences and names). Paying 3.6 times the bytes bought nothing.
- Time: about 1.2 s a line and 4.5 s to start on a desktop. With the page's main thread
  slowed 4x (phone-class), about 7 s a line and 8 s to start from cache.

So: 8-bit, the smallest build that reads as well as the biggest.

It reads one line at a time, so the pad's four ruled rows are the lines. Strokes are kept as
points, grouped by row, and redrawn large in thin dark ink before reading. This matters a
great deal: the same strokes at on-screen size and thickness read as nonsense.

## Loading

Nothing is downloaded until a visitor writes on the pad or presses "scan". Weights come from
Hugging Face at a pinned revision, the library and its runtime from jsDelivr at exact versions
(the runtime is 27 MB uncompressed, too heavy for the repository). The browser's Cache API
keeps the weights, so the second visit downloads nothing. The page has no CSP, and both hosts
send CORS headers. WebGPU is used only on a real graphics adapter, with WebAssembly as the
fallback if it is missing or fails.

## Why this is an exception to "no CDN"

`AGENTS.md` says scripts are served from `static/`. This is the one exception: the weights
cannot live in git, and the runtime alone is bigger than everything else in `static/vendor`
put together. The exception is lazy (only when the pad is used), pinned, and the pad says so
and offers a retry if a host is unreachable. If either host proves unreliable, serve the files
from a bucket we control; only the two URLs in `ocr.worker.js` change.

## What it cannot do

It reads tidy handwriting, one to four short lines. It misreads sloppy writing, similar
letters ("hi there" can come back as "li there") and uncommon words, and a visitor sees
exactly what it returned.
