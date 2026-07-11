import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "C:/Users/Julia/OneDrive/Desktop/coding/ASIoP/ML ZDC all 1/outputs/ZDC_Blocked_Rebuild_Presentation.pptx";
const PREVIEW_DIR = "C:/Users/Julia/AppData/Local/Temp/codex-presentations/manual-zdc-blocked-study/tmp/preview";
const LAYOUT_DIR = "C:/Users/Julia/AppData/Local/Temp/codex-presentations/manual-zdc-blocked-study/tmp/layout";
const QA_DIR = "C:/Users/Julia/AppData/Local/Temp/codex-presentations/manual-zdc-blocked-study/tmp/qa";

const W = 1280;
const H = 720;
const ink = "#000000";
const muted = "#555555";
const panel = "#EDEDED";
const rule = "#B8BCC4";
const accent = "#FF6B35";
const body = "#222222";

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: style.fontSize ?? 22,
    bold: style.bold ?? false,
    color: style.color ?? body,
    alignment: style.alignment ?? "left",
    typeface: "Helvetica Neue",
  };
  return shape;
}

function addBox(slide, position, fill = panel, lineFill = "none") {
  return slide.shapes.add({
    geometry: "rect",
    position,
    fill,
    line: { style: "solid", fill: lineFill, width: lineFill === "none" ? 0 : 1 },
  });
}

function addRule(slide, x, y, w, color = rule) {
  addBox(slide, { left: x, top: y, width: w, height: 1 }, color, "none");
}

function addFooter(slide, n) {
  addText(slide, String(n).padStart(2, "0"), { left: 1184, top: 659, width: 54, height: 25 }, {
    fontSize: 15,
    color: muted,
    alignment: "right",
  });
}

function addBullet(slide, text, x, y, width, fontSize = 21) {
  addBox(slide, { left: x, top: y + 8, width: 10, height: 10 }, ink);
  addText(slide, text, { left: x + 22, top: y, width, height: 54 }, {
    fontSize,
    color: body,
  });
}

function addMetric(slide, stat, label, x, y, w = 245, h = 178) {
  addBox(slide, { left: x, top: y, width: w, height: h }, panel);
  addText(slide, stat, { left: x + 24, top: y + 26, width: w - 48, height: 70 }, {
    fontSize: 44,
    bold: true,
    color: ink,
  });
  addText(slide, label, { left: x + 24, top: y + 104, width: w - 48, height: 56 }, {
    fontSize: 18,
    color: muted,
  });
}

function addSlideTitle(slide, title, subtitle, n) {
  addText(slide, title, { left: 41, top: 36, width: 980, height: 72 }, {
    fontSize: 39,
    bold: true,
    color: ink,
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 41, top: 112, width: 1050, height: 58 }, {
      fontSize: 21,
      color: muted,
    });
  }
  addFooter(slide, n);
}

function addDeck() {
  const deck = Presentation.create({ slideSize: { width: W, height: H } });

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addText(s, "ZDC Four-Vector Study", { left: 41, top: 41, width: 520, height: 60 }, {
      fontSize: 32,
      color: muted,
    });
    addText(s, "Blocked at the data contract", { left: 41, top: 182, width: 980, height: 176 }, {
      fontSize: 72,
      bold: true,
      color: ink,
    });
    addText(
      s,
      "The ROOT file is readable and truth semantics are resolved. ECAL/HCAL hit-signal units are not authoritatively defined, so training and test results would violate the protocol.",
      { left: 41, top: 502, width: 760, height: 104 },
      { fontSize: 26, color: body },
    );
    addText(s, "2026-07-11", { left: 862, top: 41, width: 376, height: 60 }, {
      fontSize: 32,
      color: muted,
      alignment: "right",
    });
    addFooter(s, 1);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The requested study has a strict fail-closed gate", "The model target is an on-shell neutron four-vector in GeV for the 50-250 GeV focus population.", 2);
    addMetric(s, "764,940", "events in latest ROOT tree", 41, 213);
    addMetric(s, "50-250", "GeV headline focus range", 351, 213);
    addMetric(s, "80/10/10", "required group-safe split", 661, 213);
    addMetric(s, "$78", "planned Vertex ceiling under $90 cap", 971, 213);
    addText(s, "Hard rule", { left: 41, top: 565, width: 180, height: 44 }, {
      fontSize: 24,
      bold: true,
      color: ink,
    });
    addText(
      s,
      "Do not infer detector signal units from whichever scale makes ML metrics look better. Use simulation metadata, simulation code, or data documentation.",
      { left: 224, top: 560, width: 940, height: 64 },
      { fontSize: 22, color: body },
    );
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "Repository intake changed the task from training to gating", "The checked-in repo was a scaffold, so I added a real fail-closed CLI path and evidence artifacts.", 3);
    addBullet(s, "Read every file in /read me first/ and every file returned by rg --files.", 73, 214, 470);
    addBullet(s, "Built a Python 3.11 environment and installed the package with dev dependencies.", 73, 296, 470);
    addBullet(s, "Added zdc-reco CLI commands and tests that refuse downstream work when BLOCKED.md exists.", 73, 378, 470);
    addBullet(s, "Reran compile, unittest, pytest, Ruff, and smoke after edits.", 73, 460, 470);
    addBox(s, { left: 657, top: 214, width: 581, height: 287 }, panel);
    addText(s, "Local verification", { left: 689, top: 244, width: 520, height: 40 }, {
      fontSize: 30,
      bold: true,
      color: ink,
    });
    addText(s, "compileall passed\nunittest: 11 tests OK\npytest: 11 passed\nRuff: all checks passed\nsmoke: perfect self-check", { left: 689, top: 306, width: 520, height: 150 }, {
      fontSize: 24,
      color: body,
    });
    addText(s, "Docker was not available locally. No new Vertex job was submitted after the blocker was found.", { left: 657, top: 535, width: 581, height: 70 }, {
      fontSize: 20,
      color: muted,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The ROOT file opens and the latest tree is identifiable", "The supplied object was inspected through GCS-backed Uproot without copying ROOT data into the repo.", 4);
    addBox(s, { left: 41, top: 205, width: 1197, height: 86 }, panel);
    addText(s, "Data URI", { left: 73, top: 228, width: 170, height: 32 }, {
      fontSize: 22,
      bold: true,
      color: ink,
    });
    addText(s, "gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root", { left: 244, top: 226, width: 930, height: 36 }, {
      fontSize: 18,
      color: body,
    });
    addMetric(s, "25.0 GB", "GCS object size", 41, 330, 270, 170);
    addMetric(s, "cycle 865", "latest myTree cycle", 351, 330, 270, 170);
    addMetric(s, "764,940", "entries in latest tree", 661, 330, 270, 170);
    addMetric(s, "6", "ROOT top-level objects", 971, 330, 270, 170);
    addText(s, "A prior tree cycle exists with 764,640 entries; the latest cycle was used for inspection.", { left: 41, top: 565, width: 980, height: 48 }, {
      fontSize: 22,
      color: muted,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The truth contract is resolved, not guessed", "A full truth-branch pass verified the particle identity and total-energy semantics.", 5);
    addMetric(s, "1", "MC particle per event", 41, 213, 270, 190);
    addMetric(s, "2112", "PDG code for all events", 351, 213, 270, 190);
    addMetric(s, "7.7e-17", "median shell residual", 661, 213, 270, 190);
    addMetric(s, "300.001", "max truth energy GeV", 971, 213, 270, 190);
    addBox(s, { left: 41, top: 482, width: 1197, height: 95 }, panel);
    addText(s, "Primary rule", { left: 73, top: 512, width: 220, height: 36 }, {
      fontSize: 26,
      bold: true,
      color: ink,
    });
    addText(s, "Use the only MC particle in the event after verifying every event has exactly one candidate and all candidates are neutrons.", { left: 305, top: 510, width: 850, height: 44 }, {
      fontSize: 22,
      color: body,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The detector hit-unit evidence is missing", "This is the single hard scientific ambiguity that stops the study.", 6);
    addBox(s, { left: 41, top: 213, width: 581, height: 139 }, panel);
    addText(s, "ROOT metadata", { left: 73, top: 239, width: 524, height: 40 }, {
      fontSize: 30,
      bold: true,
      color: ink,
    });
    addText(s, "Branch titles are only names like ecal_energy and hcal_energy. Histogram axes have numeric ranges but no unit titles.", { left: 73, top: 294, width: 520, height: 74 }, {
      fontSize: 21,
      color: body,
    });
    addBox(s, { left: 657, top: 213, width: 581, height: 139 }, panel);
    addText(s, "Bucket search", { left: 689, top: 239, width: 524, height: 40 }, {
      fontSize: 30,
      bold: true,
      color: ink,
    });
    addText(s, "No detector macro, simulation source, data dictionary, README, DD4hep, or Geant unit authority was found.", { left: 689, top: 294, width: 520, height: 74 }, {
      fontSize: 21,
      color: body,
    });
    addRule(s, 41, 430, 1197, accent);
    addText(s, "Protocol consequence", { left: 41, top: 466, width: 360, height: 40 }, {
      fontSize: 28,
      bold: true,
      color: ink,
    });
    addText(s, "No absolute energy reconstruction is valid until ecal_energy and hcal_energy are defined by authoritative simulation metadata, code, or documentation.", { left: 41, top: 520, width: 1000, height: 66 }, {
      fontSize: 24,
      color: body,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "No champion or locked test result exists", "Stopping here protects the science: training would require a unit assumption the prompt forbids.", 7);
    addMetric(s, "$0", "new Vertex spend after blocker", 41, 213, 245, 178);
    addMetric(s, "0", "new models trained", 312, 213, 245, 178);
    addMetric(s, "0", "test rows unlocked", 582, 213, 245, 178);
    addMetric(s, "1", "hard blocker recorded", 852, 213, 245, 178);
    addBox(s, { left: 41, top: 455, width: 1197, height: 130 }, panel);
    addText(s, "Not run", { left: 73, top: 488, width: 180, height: 36 }, {
      fontSize: 28,
      bold: true,
      color: ink,
    });
    addText(s, "production features, splits, baselines, XGBoost comparisons, dual-grid T4 training, calibration, test unlock, final plots, and headline metrics", { left: 260, top: 484, width: 870, height: 58 }, {
      fontSize: 23,
      color: body,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "Prior Vertex artifacts are context, not completion", "Existing GCS runs used the same ROOT object, but they do not satisfy the current protocol.", 8);
    addBullet(s, "Completed prior CPU jobs exist in Vertex from 2026-07-10.", 73, 214, 520);
    addBullet(s, "They used an older configs/default.yaml and older zdc-reco container images.", 73, 296, 520);
    addBullet(s, "They assumed hit_signal_scale_to_gev = 1.0 without current authoritative unit evidence.", 73, 378, 520);
    addBullet(s, "They did not complete the required current dual-grid T4 path or current QA ledger.", 73, 460, 520);
    addBox(s, { left: 760, top: 225, width: 360, height: 260 }, panel);
    addText(s, "Useful only as historical context", { left: 792, top: 274, width: 300, height: 110 }, {
      fontSize: 34,
      bold: true,
      color: ink,
    });
    addText(s, "Do not present prior numbers as new locked results.", { left: 792, top: 406, width: 300, height: 54 }, {
      fontSize: 21,
      color: muted,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "Once unit authority exists, the rebuild path is explicit", "The current repo now fails closed first, then resumes the intended production ladder.", 9);
    const steps = [
      ["1", "Provide unit authority", "Simulation code or documentation defining ECAL/HCAL hit energy units."],
      ["2", "Rerun preflight", "Lock schema, hit policies, grid mapping, and source hashes."],
      ["3", "Build artifacts", "Targets, split, scalar features, ECAL grids, HCAL grids, manifests."],
      ["4", "Train candidates", "B0/B1, corrected XGBoost, bounded dual-grid T4 trials if gates pass."],
      ["5", "Freeze and test", "Select champion, calibrate on validation, unlock test once, report."],
    ];
    steps.forEach((step, i) => {
      const y = 190 + i * 86;
      addBox(s, { left: 41, top: y, width: 92, height: 58 }, i === 0 ? accent : panel);
      addText(s, step[0], { left: 41, top: y + 8, width: 92, height: 38 }, {
        fontSize: 30,
        bold: true,
        color: i === 0 ? "#FFFFFF" : ink,
        alignment: "center",
      });
      addText(s, step[1], { left: 160, top: y, width: 340, height: 34 }, {
        fontSize: 24,
        bold: true,
        color: ink,
      });
      addText(s, step[2], { left: 520, top: y, width: 650, height: 44 }, {
        fontSize: 20,
        color: body,
      });
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The decision ask is small and concrete", "Resolve one missing authority before spending Vertex budget or opening the test fold.", 10);
    addBox(s, { left: 41, top: 213, width: 581, height: 245 }, panel);
    addText(s, "Needed from the data owner", { left: 73, top: 245, width: 520, height: 44 }, {
      fontSize: 32,
      bold: true,
      color: ink,
    });
    addText(s, "A source file, macro, README, detector note, or data dictionary that defines ecal_energy and hcal_energy units and conversion to GeV.", { left: 73, top: 314, width: 500, height: 100 }, {
      fontSize: 23,
      color: body,
    });
    addBox(s, { left: 657, top: 213, width: 581, height: 245 }, panel);
    addText(s, "Restart command", { left: 689, top: 245, width: 520, height: 44 }, {
      fontSize: 32,
      bold: true,
      color: ink,
    });
    addText(s, "zdc-reco run-all --config configs/study.yaml --data gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root", { left: 689, top: 312, width: 510, height: 114 }, {
      fontSize: 18,
      color: body,
    });
    addText(s, "Until then, the scientifically correct result is BLOCKED, not a guessed champion.", { left: 41, top: 548, width: 1000, height: 48 }, {
      fontSize: 26,
      bold: true,
      color: ink,
    });
  }

  return deck;
}

async function main() {
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  await fs.mkdir(QA_DIR, { recursive: true });
  const deck = addDeck();
  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(PREVIEW_DIR, `${stem}.png`), await deck.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  await writeBlob(path.join(QA_DIR, "deck-montage.webp"), await deck.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

