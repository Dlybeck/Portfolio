// Shared bits for the cover stickers. Each sticker is a small module with `html()` and `wire(element, context)`.

export { reducedMotion } from "../motion.js";

/** The dl note logo, used on the puzzle tiles and the printer's print. */
export const LOGO = "/static/dlybeck/dl-note.svg";

/** Run `fn` on a click, or on Enter or Space when the sticker has the keyboard. */
export function tap(element, fn) {
  element.addEventListener("click", fn);
  element.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fn(e);
    }
  });
}

/** Play a CSS animation class again from the start. */
export function restart(element, className) {
  element.classList.remove(className);
  void element.offsetWidth;
  element.classList.add(className);
}

/** A sticker's own touches must not open the cover or turn the book. */
export function keepEventsHere(element) {
  for (const type of ["pointerdown", "pointerup", "click"]) element.addEventListener(type, (e) => e.stopPropagation());
  element.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") e.stopPropagation();
  });
}
