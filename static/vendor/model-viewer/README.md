# model-viewer

`model-viewer.min.js` is `@google/model-viewer` **3.5.0** (`dist/model-viewer.min.js`), copied unchanged from the
npm package. It is served from this site so the 3D models need no CDN.

Licenses: model-viewer is Apache-2.0 (`LICENSE`). The bundle also carries Lit (BSD-3-Clause), three.js (MIT)
and fflate (MIT); their notices are kept in the file as `@license` comments.

The bundle can fetch Draco or Basis decoders from `gstatic.com`, but only for compressed models. The models in
`static/3Dmodels` are plain glTF with no compression (`tests/test_pages.py` checks this). If a compressed model
is ever added, serve the decoders from this folder and set `ModelViewerElement.dracoDecoderLocation` first.
