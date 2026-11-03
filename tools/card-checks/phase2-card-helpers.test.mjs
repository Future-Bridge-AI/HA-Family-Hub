// Node check for the Phase 2 calendar-card helpers (build stamp, loud delete).
// No dependencies: reads the served card as text, slices the DOM-free helper
// block between the two marker comments and evaluates only that slice.
//
//   node tools/card-checks/phase2-card-helpers.test.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const CARD = path.resolve(here, "../../custom_components/family_hub/card/family-week-calendar-card.js");
const BEGIN = "// __FH_TESTABLE_HELPERS_BEGIN";
const END = "// __FH_TESTABLE_HELPERS_END";

let checks = 0;
function check(name, fn) {
  try {
    fn();
  } catch (err) {
    console.error("FAILED: " + name);
    throw err;
  }
  checks += 1;
}

function sliceHelpers(source) {
  const start = source.indexOf(BEGIN);
  const stop = source.indexOf(END);
  assert.ok(start >= 0 && stop > start, "helper markers present and ordered");
  return source.slice(start + BEGIN.length, stop);
}

function loadHelpers(source) {
  const body = sliceHelpers(source);
  // Return whatever the block defines; a name that is not defined yet is
  // reported as undefined so each check fails on its own assertion.
  return new Function(
    body +
      "\nreturn {" +
      " __FH_BUILD," +
      " __fhBuildStampText," +
      " __fhRealCalendarDeleteWarning: typeof __fhRealCalendarDeleteWarning === 'function' ? __fhRealCalendarDeleteWarning : undefined" +
      " };"
  )();
}

const source = fs.readFileSync(CARD, "utf8");
const h = loadHelpers(source);
const MIDDOT = "·";

// ---- build stamp ---------------------------------------------------------
check("literal tokens + DEV location name -> 'Dev · live'", () => {
  assert.equal(h.__fhBuildStampText(h.__FH_BUILD, "Family Hub DEV"), "Dev " + MIDDOT + " live");
});

for (const name of ["Home", "Family Hub PREVIEW", "Family Hub dev", "Family Hub DEVELOPMENT", "", undefined, null]) {
  check("literal tokens + " + JSON.stringify(name) + " -> nothing", () => {
    assert.equal(h.__fhBuildStampText(h.__FH_BUILD, name), "");
  });
}

check("substituted build gives the full Preview stamp", () => {
  const out = h.__fhBuildStampText({ env: "Preview", version: "2.0.0+a1b2c3d", deployed: "2 Nov 16:05" }, "Family Hub PREVIEW");
  assert.equal(out, "Preview " + MIDDOT + " 2.0.0+a1b2c3d " + MIDDOT + " 2 Nov 16:05");
  assert.equal(out.split(MIDDOT).length - 1, 2, "U+00B7 exactly twice");
  assert.ok(!out.includes("__FH_BUILD"), "no raw token text in the stamp");
});

check("substituted build shows regardless of the location name", () => {
  const out = h.__fhBuildStampText({ env: "Preview", version: "2.0.0+a1b2c3d", deployed: "2 Nov 16:05" }, "Home");
  assert.ok(out.startsWith("Preview "));
});

const partly = { env: "Preview", version: h.__FH_BUILD.version, deployed: "2 Nov 16:05" };
check("partly substituted build + Home -> nothing", () => {
  assert.equal(h.__fhBuildStampText(partly, "Home"), "");
});
check("partly substituted build + DEV -> 'Dev · live'", () => {
  assert.equal(h.__fhBuildStampText(partly, "Family Hub DEV"), "Dev " + MIDDOT + " live");
});
check("missing build object never throws and shows nothing on Home", () => {
  assert.equal(h.__fhBuildStampText(undefined, "Home"), "");
  assert.equal(h.__fhBuildStampText({}, "Home"), "");
});

for (const token of ["__FH_BUILD_ENV__", "__FH_BUILD_VERSION__", "__FH_BUILD_TIME__"]) {
  check("token " + token + " occurs exactly once in the card", () => {
    assert.equal(source.split(token).length - 1, 1);
  });
}

check("simulated deploy substitution survives detection", () => {
  const deployed = source
    .replace("__FH_BUILD_ENV__", "Preview")
    .replace("__FH_BUILD_VERSION__", "2.0.0+a1b2c3d")
    .replace("__FH_BUILD_TIME__", "2 Nov 16:05");
  assert.ok(deployed.includes("__FH_TESTABLE_HELPERS_BEGIN"), "markers survive substitution");
  const d = loadHelpers(deployed);
  assert.equal(
    d.__fhBuildStampText(d.__FH_BUILD, "Family Hub PREVIEW"),
    "Preview " + MIDDOT + " 2.0.0+a1b2c3d " + MIDDOT + " 2 Nov 16:05"
  );
});

// ---- loud delete confirmation (D-09) ------------------------------------
const warn = h.__fhRealCalendarDeleteWarning;

check("warning helper is defined", () => {
  assert.equal(typeof warn, "function");
});

check("Preview + google -> exact S4 copy", () => {
  const out = warn("Family Hub PREVIEW", "google", "Dentist", "Jordan");
  assert.equal(
    out,
    "THIS IS THE REAL FAMILY CALENDAR.\n\n" +
      'You are in Preview, but "Dentist" is on Jordan\'s real Google Calendar. ' +
      "Deleting it here deletes it for the whole family, and Family Hub cannot undo it.\n\n" +
      "Delete it anyway?"
  );
});

check("DEV + google says 'You are in Dev'", () => {
  const out = warn("Family Hub DEV", "google", "Dentist", "Jordan");
  assert.ok(out.startsWith("THIS IS THE REAL FAMILY CALENDAR."));
  assert.ok(out.includes('You are in Dev, but "Dentist" is on Jordan\'s real Google Calendar.'));
});

for (const [label, args] of [
  ["Home location", ["Home", "google", "Dentist", "Jordan"]],
  ["lower-case dev location", ["Family Hub dev", "google", "Dentist", "Jordan"]],
  ["DEVELOPMENT location", ["Family Hub DEVELOPMENT", "google", "Dentist", "Jordan"]],
  ["PREVIEWS location", ["Family Hub PREVIEWS", "google", "Dentist", "Jordan"]],
  ["missing location", [undefined, "google", "Dentist", "Jordan"]],
  ["local_calendar platform", ["Family Hub PREVIEW", "local_calendar", "Dentist", "Jordan"]],
  ["null platform", ["Family Hub PREVIEW", null, "Dentist", "Jordan"]],
  ["undefined platform", ["Family Hub PREVIEW", undefined, "Dentist", "Jordan"]],
  ["[PREVIEW] seed tag", ["Family Hub PREVIEW", "google", "[PREVIEW] Dentist", "Jordan"]],
  ["[DEV] seed tag", ["Family Hub DEV", "google", "[DEV] Dentist", "Jordan"]],
]) {
  check("no warning for " + label, () => {
    assert.equal(warn(...args), null);
  });
}

for (const summary of ["[PREVIEW]Dentist", "[preview] Dentist", " [PREVIEW] Dentist", "[DEV]Dentist"]) {
  check("seed-tag lookalike " + JSON.stringify(summary) + " is not exempt", () => {
    const out = warn("Family Hub PREVIEW", "google", summary, "Jordan");
    assert.ok(out && out.startsWith("THIS IS THE REAL FAMILY CALENDAR."));
  });
}

check("120-character summary is cut to 80 characters plus an ellipsis", () => {
  const summary = Array.from({ length: 120 }, (_, i) => String.fromCharCode(97 + (i % 26))).join("");
  const out = warn("Family Hub PREVIEW", "google", summary, "Jordan");
  assert.ok(out.includes('"' + summary.slice(0, 80) + '…"'));
  assert.ok(!out.includes(summary.slice(0, 81)), "81st character absent");
});

check("80-character summary is not cut and gets no ellipsis", () => {
  const summary = "x".repeat(80);
  const out = warn("Family Hub PREVIEW", "google", summary, "Jordan");
  assert.ok(out.includes('"' + summary + '"'));
});

check("emoji around position 80 never leaves a lone surrogate", () => {
  const summary = "a".repeat(79) + "\u{1F600}\u{1F600}" + "b".repeat(20);
  const out = warn("Family Hub PREVIEW", "google", summary, "Jordan");
  assert.ok(out.includes('"' + "a".repeat(79) + "\u{1F600}…" + '"'));
  assert.ok(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/.test(out), "no lone surrogate");
});

check("_wireEventInfoDeleteButton: confirm, then loud warning, then disable", () => {
  const from = source.indexOf("async _wireEventInfoDeleteButton(");
  assert.ok(from >= 0, "method found");
  const next = source.indexOf("async _wireEventInfoEditButton(", from);
  assert.ok(next > from, "next method found");
  const method = source.slice(from, next);
  const first = method.indexOf("event_info.delete_confirm");
  const second = method.indexOf("__fhRealCalendarDeleteWarning(");
  const disable = method.indexOf("btn.disabled = true");
  assert.ok(first >= 0 && second >= 0 && disable >= 0, "all three landmarks present");
  assert.ok(first < second && second < disable, "order: first confirm < warning < btn.disabled = true");
});

check("_getCalendarDeleteSupport keeps the backend platform", () => {
  const from = source.indexOf("async _getCalendarDeleteSupport(");
  assert.ok(from >= 0, "method found");
  const method = source.slice(from, from + 3000);
  assert.ok(method.includes("platform: res.platform || null"), "platform passed through");
  assert.ok(method.includes("platform: null"), "no-hass default carries platform: null");
});

console.log("phase2 card helpers: " + checks + " checks passed");
