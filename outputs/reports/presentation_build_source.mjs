import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "C:/Users/Julia/OneDrive/Desktop/coding/ASIoP/ML ZDC all 1/outputs/ZDC_Accepted_XGB_Result_Presentation.pptx";
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
    addText(s, "Accepted XGBoost result", { left: 41, top: 182, width: 980, height: 176 }, {
      fontSize: 72,
      bold: true,
      color: ink,
    });
    addText(
      s,
      "The local ROOT file matches the US-CENTRAL1 Vertex input. ECAL/HCAL hit signals are accepted as GeV deposits using the prior pipeline evidence and the data-owner continuation.",
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
    addSlideTitle(s, "The study now has an accepted scalar result", "The model target is an on-shell neutron four-vector in GeV for the 50-250 GeV focus population.", 2);
    addMetric(s, "764,940", "events in latest ROOT tree", 41, 213);
    addMetric(s, "50-250", "GeV headline focus range", 351, 213);
    addMetric(s, "80/10/10", "required group-safe split", 661, 213);
    addMetric(s, "$78", "planned Vertex ceiling under $90 cap", 971, 213);
    addText(s, "Resolved gate", { left: 41, top: 565, width: 180, height: 44 }, {
      fontSize: 24,
      bold: true,
      color: ink,
    });
    addText(
      s,
      "The prior implementation showed energy sums and ratios are internally consistent with GeV hit deposits; the user directed that interpretation for this normal ZDC dataset.",
      { left: 224, top: 560, width: 940, height: 64 },
      { fontSize: 22, color: body },
    );
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "Repository intake added an audit trail", "The checked-in repo started as a stricter scaffold, so I preserved the fail-closed audit and imported the executable prior pipeline.", 3);
    addBullet(s, "Read every file in /read me first/ and every file returned by rg --files.", 73, 214, 470);
    addBullet(s, "Built a Python 3.11 environment and installed the package with dev dependencies.", 73, 296, 470);
    addBullet(s, "Imported the prior zdc_reco pipeline that produced the accepted Vertex result.", 73, 378, 470);
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
    addText(s, "Docker was not available locally. No new Vertex job was needed after the accepted prior Vertex artifacts were identified.", { left: 657, top: 535, width: 581, height: 70 }, {
      fontSize: 20,
      color: muted,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The local ROOT file is already staged for Vertex", "The local file hash matches the US-CENTRAL1 Cloud Storage object used by Vertex custom jobs.", 4);
    addBox(s, { left: 41, top: 190, width: 1197, height: 76 }, panel);
    addText(s, "Local file", { left: 73, top: 211, width: 170, height: 32 }, {
      fontSize: 22,
      bold: true,
      color: ink,
    });
    addText(s, "C:/Users/Julia/.../ML ZDC all 1/myTree_20251117_765k_0to300GeV_neutron_All.root", { left: 244, top: 209, width: 930, height: 36 }, {
      fontSize: 17,
      color: body,
    });
    addBox(s, { left: 41, top: 284, width: 1197, height: 76 }, panel);
    addText(s, "Vertex URI", { left: 73, top: 305, width: 170, height: 32 }, {
      fontSize: 22,
      bold: true,
      color: ink,
    });
    addText(s, "gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root", { left: 244, top: 303, width: 930, height: 36 }, {
      fontSize: 17,
      color: body,
    });
    addMetric(s, "25.0 GB", "local and staged object size", 41, 410, 270, 150);
    addMetric(s, "lCVUvQ==", "matching CRC32C", 351, 410, 270, 150);
    addMetric(s, "b7c666", "SHA-256 prefix verified", 661, 410, 270, 150);
    addMetric(s, "region OK", "US-CENTRAL1 bucket matches Vertex", 971, 410, 270, 150);
    addText(s, "No duplicate 23.3 GiB upload was performed because the staged object already matches the local file. Use the GCS URI for Vertex jobs; the deletion command is recorded in the package.", { left: 41, top: 590, width: 1120, height: 58 }, {
      fontSize: 20,
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
    addSlideTitle(s, "The detector hit-unit gate is resolved for this run", "The scale is accepted as 1.0 GeV for both ECAL and HCAL hit signals.", 6);
    addBox(s, { left: 41, top: 213, width: 581, height: 139 }, panel);
    addText(s, "Prior evidence", { left: 73, top: 239, width: 524, height: 40 }, {
      fontSize: 30,
      bold: true,
      color: ink,
    });
    addText(s, "energySum branches equal summed per-hit energies; energyRatio branches equal sum divided by mcPar_mom.", { left: 73, top: 294, width: 520, height: 74 }, {
      fontSize: 21,
      color: body,
    });
    addBox(s, { left: 657, top: 213, width: 581, height: 139 }, panel);
    addText(s, "Owner direction", { left: 689, top: 239, width: 524, height: 40 }, {
      fontSize: 30,
      bold: true,
      color: ink,
    });
    addText(s, "The user directed use of the normal ZDC interpretation and the prior ML ZDC all implementation.", { left: 689, top: 294, width: 520, height: 74 }, {
      fontSize: 21,
      color: body,
    });
    addRule(s, 41, 430, 1197, accent);
    addText(s, "Locked contract", { left: 41, top: 466, width: 360, height: 40 }, {
      fontSize: 28,
      bold: true,
      color: ink,
    });
    addText(s, "ecal_energy and hcal_energy are treated as ideal simulated hit-energy deposits in GeV with scale 1.0. This does not imply real-detector electronics calibration.", { left: 41, top: 520, width: 1000, height: 66 }, {
      fontSize: 24,
      color: body,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "M1_xgb_focus_only is the accepted champion", "The locked focus-test result comes from the prior Vertex scalar-feature/XGBoost run.", 7);
    addMetric(s, "0.2044", "macro RMS relative four-vector error", 41, 213, 245, 178);
    addMetric(s, "11.48", "energy MAE in GeV", 312, 213, 245, 178);
    addMetric(s, "5.87", "median angular error mrad", 582, 213, 245, 178);
    addMetric(s, "50,685", "focus test events", 852, 213, 245, 178);
    addBox(s, { left: 41, top: 455, width: 1197, height: 130 }, panel);
    addText(s, "Caveat", { left: 73, top: 488, width: 180, height: 36 }, {
      fontSize: 28,
      bold: true,
      color: ink,
    });
    addText(s, "This accepted run is scalar-feature/XGBoost. The newer dual-grid T4 neural path and ECAL/HCAL tensor artifacts are not present in the accepted output.", { left: 260, top: 484, width: 870, height: 58 }, {
      fontSize: 23,
      color: body,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The accepted run completed on Vertex", "The result was produced by the prior implementation against the same ROOT object.", 8);
    addBullet(s, "Finalization job completed on 2026-07-10 from 15:00:07 to 15:12:49 UTC.", 73, 214, 520);
    addBullet(s, "Stages completed: baselines, XGBoost, selection, calibration, test unlock, evaluation, plots, verify.", 73, 296, 520);
    addBullet(s, "Output prefix: gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs.", 73, 378, 520);
    addBullet(s, "The local ROOT hash matches the Vertex input hash exactly.", 73, 460, 520);
    addBox(s, { left: 760, top: 225, width: 360, height: 260 }, panel);
    addText(s, "Accepted as scalar result", { left: 792, top: 274, width: 300, height: 110 }, {
      fontSize: 34,
      bold: true,
      color: ink,
    });
    addText(s, "Do not present it as the newer dual-grid neural result.", { left: 792, top: 406, width: 300, height: 54 }, {
      fontSize: 21,
      color: muted,
    });
  }

  {
    const s = deck.slides.add();
    s.background.fill = "#FFFFFF";
    addSlideTitle(s, "The rebuild path is explicit", "The imported legacy pipeline can reproduce the accepted scalar/XGBoost run from the staged Vertex input.", 9);
    const steps = [
      ["1", "Use staged data", "The local ROOT matches the US-CENTRAL1 GCS object."],
      ["2", "Run preflight", "Lock schema, hit policies, frame, and source hashes."],
      ["3", "Build artifacts", "Targets, split, scalar features, ECAL grids, HCAL grids, manifests."],
      ["4", "Train candidates", "B0/B1 and XGBoost support variants in the scalar pipeline."],
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
    addSlideTitle(s, "The next decision is whether to fund the neural extension", "The scalar result is accepted; the dual-grid T4 model remains future work.", 10);
    addBox(s, { left: 41, top: 213, width: 581, height: 245 }, panel);
    addText(s, "Accepted result", { left: 73, top: 245, width: 520, height: 44 }, {
      fontSize: 32,
      bold: true,
      color: ink,
    });
    addText(s, "Use M1_xgb_focus_only as the scalar-feature benchmark: macro RMS 0.2044, energy MAE 11.48 GeV, angular median 5.87 mrad.", { left: 73, top: 314, width: 500, height: 100 }, {
      fontSize: 23,
      color: body,
    });
    addBox(s, { left: 657, top: 213, width: 581, height: 245 }, panel);
    addText(s, "Rebuild command", { left: 689, top: 245, width: 520, height: 44 }, {
      fontSize: 32,
      bold: true,
      color: ink,
    });
    addText(s, "python -m zdc_reco.cli run-all-gcs --data-gcs gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root --config configs/legacy_vertex_default.yaml", { left: 689, top: 312, width: 510, height: 114 }, {
      fontSize: 18,
      color: body,
    });
    addText(s, "Delete staged data later: gcloud storage rm gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root", { left: 657, top: 466, width: 560, height: 54 }, {
      fontSize: 16,
      color: muted,
    });
    addText(s, "The final package keeps both the accepted result and the remaining neural-caveat visible.", { left: 41, top: 548, width: 1000, height: 48 }, {
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

