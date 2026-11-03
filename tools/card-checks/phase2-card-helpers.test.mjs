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

console.log("phase2 card helpers: " + checks + " checks passed");
