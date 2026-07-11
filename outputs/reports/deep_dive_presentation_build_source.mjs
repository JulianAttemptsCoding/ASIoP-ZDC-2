import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/Julia/OneDrive/Desktop/coding/ASIoP/ML ZDC all 1";
const OUT = `${ROOT}/outputs/ZDC_All_Neutron_Model_Deep_Dive.pptx`;
const TMP = "C:/Users/Julia/AppData/Local/Temp/codex-presentations/manual-zdc-all-deep-dive/tmp";
const PREVIEW_DIR = `${TMP}/preview`;
const LAYOUT_DIR = `${TMP}/layout`;
const QA_DIR = `${TMP}/qa`;

const W = 1280;
const H = 720;
const blue = "#2E75B6";
const dark = "#111111";
const body = "#222222";
const muted = "#666666";
const light = "#F4F6F8";
const line = "#C7C7C7";
const orange = "#F4B183";
const paleOrange = "#FFF2CC";
const white = "#FFFFFF";
const green = "#70AD47";
const font = "Arial";

const plots = {
  data: `${ROOT}/outputs/plots/expanded_diagnostics/01_data_overview.png`,
  predTrue: `${ROOT}/outputs/plots/expanded_diagnostics/02_component_pred_vs_true.png`,
  residuals: `${ROOT}/outputs/plots/expanded_diagnostics/03_component_residuals.png`,
  componentBars: `${ROOT}/outputs/plots/expanded_diagnostics/04_component_metric_bars.png`,
  energySlices: `${ROOT}/outputs/plots/expanded_diagnostics/05_energy_bias_resolution_slices.png`,
  componentSlices: `${ROOT}/outputs/plots/expanded_diagnostics/06_component_bias_resolution_slices.png`,
  angular: `${ROOT}/outputs/plots/expanded_diagnostics/07_angular_error.png`,
  leaderboard: `${ROOT}/outputs/plots/expanded_diagnostics/08_validation_leaderboard.png`,
  importance: `${ROOT}/outputs/plots/expanded_diagnostics/09_feature_importance.png`,
  shell: `${ROOT}/outputs/plots/expanded_diagnostics/11_mass_shell_residual.png`,
  energyDensity: `${ROOT}/outputs/plots/expanded_diagnostics/12_energy_response_density.png`,
  errorDrivers: `${ROOT}/outputs/plots/expanded_diagnostics/16_error_driver_correlations.png`,
  tailContrast: `${ROOT}/outputs/plots/expanded_diagnostics/17_tail_feature_contrast.png`,
  sliceDiag: `${ROOT}/outputs/plots/expanded_diagnostics/18_test_focus_energy_slice_diagnostics.png`,
  lossOverall: `${ROOT}/outputs/plots/expanded_diagnostics/19_loss_overall_train_validation_vs_boosting.png`,
  lossE: `${ROOT}/outputs/plots/expanded_diagnostics/20_loss_E_train_validation_vs_boosting.png`,
  lossPx: `${ROOT}/outputs/plots/expanded_diagnostics/21_loss_px_train_validation_vs_boosting.png`,
  lossPy: `${ROOT}/outputs/plots/expanded_diagnostics/22_loss_py_train_validation_vs_boosting.png`,
  lossPz: `${ROOT}/outputs/plots/expanded_diagnostics/23_loss_pz_train_validation_vs_boosting.png`,
  nativeGrid: `${ROOT}/outputs/plots/expanded_diagnostics/24_native_target_loss_grid_vs_boosting.png`,
  lossGap: `${ROOT}/outputs/plots/expanded_diagnostics/25_loss_overall_train_validation_gap.png`,
  componentGaps: `${ROOT}/outputs/plots/expanded_diagnostics/26_loss_component_train_validation_gaps.png`,
  bestRound: `${ROOT}/outputs/plots/expanded_diagnostics/27_loss_best_round_train_vs_validation_bars.png`,
  focusAll: `${ROOT}/outputs/plots/expanded_diagnostics/28_component_metric_comparison_focus_vs_all.png`,
  heatmap: `${ROOT}/outputs/plots/expanded_diagnostics/29_component_resolution_energy_slice_heatmap.png`,
  featureError: `${ROOT}/outputs/plots/expanded_diagnostics/30_top_feature_error_correlations.png`,
  basicResidual: `${ROOT}/outputs/plots/focus_test_energy_residual.png`,
};

async function ensureDirs() {
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  await fs.mkdir(QA_DIR, { recursive: true });
  await fs.mkdir(path.dirname(OUT), { recursive: true });
}

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function imageBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, text, pos, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: pos,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: style.fontSize ?? 16,
    bold: style.bold ?? false,
    color: style.color ?? body,
    alignment: style.alignment ?? "left",
    typeface: style.typeface ?? font,
  };
  return shape;
}

function addBox(slide, pos, fill = light, stroke = "none", width = 1) {
  return slide.shapes.add({
    geometry: "rect",
    position: pos,
    fill,
    line: { style: "solid", fill: stroke, width: stroke === "none" ? 0 : width },
  });
}

function addRule(slide, y = 116) {
  addBox(slide, { left: 40, top: y, width: 1198, height: 1.3 }, line, "none");
}

function addFooter(slide, n, section = "") {
  addText(slide, `ASIoP ZDC - FOUR-VECTOR RECO${section ? ` - ${section}` : ""}`, { left: 41, top: 668, width: 700, height: 22 }, { fontSize: 9, color: muted });
  addText(slide, String(n), { left: 1190, top: 668, width: 48, height: 22 }, { fontSize: 9, color: muted, alignment: "right" });
}

function addHeader(slide, section, title, n, subtitle = "") {
  addText(slide, section.toUpperCase(), { left: 41, top: 30, width: 420, height: 24 }, { fontSize: 11, bold: true, color: blue });
  addText(slide, title, { left: 41, top: 55, width: 1060, height: 50 }, { fontSize: 26, bold: true, color: dark });
  if (subtitle) addText(slide, subtitle, { left: 41, top: 96, width: 1030, height: 28 }, { fontSize: 12, color: muted });
  addRule(slide, subtitle ? 132 : 118);
  addFooter(slide, n, section);
}

function addBullet(slide, text, x, y, w, size = 15, color = body) {
  addBox(slide, { left: x, top: y + 7, width: 6, height: 6 }, blue, "none");
  addText(slide, text, { left: x + 16, top: y, width: w, height: 48 }, { fontSize: size, color });
}

function addMetric(slide, value, label, x, y, w = 190, h = 105, accent = blue) {
  addBox(slide, { left: x, top: y, width: w, height: h }, white, "#D9D9D9");
  addBox(slide, { left: x, top: y, width: w, height: 5 }, accent, "none");
  addText(slide, value, { left: x + 12, top: y + 20, width: w - 24, height: 38 }, { fontSize: 25, bold: true, color: accent, alignment: "center" });
  addText(slide, label, { left: x + 12, top: y + 60, width: w - 24, height: 36 }, { fontSize: 11.5, color: muted, alignment: "center" });
}

function addCallout(slide, title, text, x, y, w, h, fill = paleOrange) {
  addBox(slide, { left: x, top: y, width: w, height: h }, fill, "#E6C37A");
  addText(slide, title, { left: x + 14, top: y + 12, width: w - 28, height: 24 }, { fontSize: 16, bold: true, color: dark });
  addText(slide, text, { left: x + 14, top: y + 40, width: w - 28, height: h - 48 }, { fontSize: 12.5, color: body });
}

function addImage(slide, filePath, pos, alt, fit = "contain") {
  return imageBytes(filePath).then((blob) => {
    slide.images.add({ blob, contentType: "image/png", alt, fit, position: pos });
  });
}

function addTable(slide, rows, x, y, widths, rowH, opts = {}) {
  const totalW = widths.reduce((a, b) => a + b, 0);
  rows.forEach((row, r) => {
    const fill = r === 0 ? blue : r % 2 === 0 ? "#F8F8F8" : white;
    let cx = x;
    row.forEach((cell, c) => {
      addBox(slide, { left: cx, top: y + r * rowH, width: widths[c], height: rowH }, fill, line, 0.7);
      addText(slide, String(cell), { left: cx + 5, top: y + r * rowH + 4, width: widths[c] - 10, height: rowH - 6 }, {
        fontSize: opts.fontSize ?? 10.5,
        bold: r === 0,
        color: r === 0 ? white : body,
        alignment: opts.align?.[c] ?? "left",
      });
      cx += widths[c];
    });
  });
  addBox(slide, { left: x, top: y, width: totalW, height: rows.length * rowH }, "none", line, 0.8);
}

function addFlow(slide, steps, x, y, w, h) {
  const gap = 14;
  const boxW = (w - gap * (steps.length - 1)) / steps.length;
  steps.forEach((step, i) => {
    const left = x + i * (boxW + gap);
    addBox(slide, { left, top: y, width: boxW, height: h }, i % 2 === 0 ? "#EAF2F8" : "#F4F6F8", "#BFBFBF");
    addText(slide, step[0], { left: left + 10, top: y + 13, width: boxW - 20, height: 24 }, { fontSize: 13, bold: true, color: blue, alignment: "center" });
    addText(slide, step[1], { left: left + 10, top: y + 43, width: boxW - 20, height: h - 50 }, { fontSize: 10.8, color: body, alignment: "center" });
    if (i < steps.length - 1) addText(slide, ">", { left: left + boxW + 1, top: y + h / 2 - 13, width: gap + 10, height: 24 }, { fontSize: 18, bold: true, color: orange, alignment: "center" });
  });
}

function addFormulaBox(slide, title, formulaLines, x, y, w, h, fill = "#F8F8F8") {
  addBox(slide, { left: x, top: y, width: w, height: h }, fill, "#D0D0D0");
  addText(slide, title, { left: x + 16, top: y + 12, width: w - 32, height: 26 }, { fontSize: 16, bold: true, color: blue });
  addText(slide, formulaLines.join("\n"), { left: x + 16, top: y + 48, width: w - 32, height: h - 58 }, { fontSize: 14, color: dark, typeface: "Consolas" });
}

async function buildDeck() {
  const deck = Presentation.create({ slideSize: { width: W, height: H } });
  const imagePromises = [];

  {
    const s = deck.slides.add();
    s.background.fill = white;
    addBox(s, { left: 0, top: 0, width: W, height: 7 }, blue, "none");
    addText(s, "ASIoP ZDC - FOUR-VECTOR RECONSTRUCTION", { left: 41, top: 95, width: 620, height: 24 }, { fontSize: 11, bold: true, color: blue });
    addText(s, "All-neutron ZDC model deep dive", { left: 41, top: 165, width: 920, height: 82 }, { fontSize: 38, bold: true, color: dark });
    addText(s, "Scalar-feature XGBoost model that reconstructs an on-shell neutron (E, px, py, pz) from ECAL/HCAL simulated hit deposits", { left: 41, top: 270, width: 880, height: 78 }, { fontSize: 18, color: body });
    addText(s, "Accepted Vertex result: M1_xgb_focus_only - focus range 50-250 GeV - 2026-07-11", { left: 41, top: 608, width: 900, height: 24 }, { fontSize: 11, color: muted });
    addText(s, "github.com/JulianAttemptsCoding/ASIoP-ZDC-2", { left: 800, top: 608, width: 438, height: 24 }, { fontSize: 11, color: muted, alignment: "right" });
    addFooter(s, 1);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "The task", "Reconstruct a neutron four-vector from calorimeter hits", 2);
    addText(s, "What goes in", { left: 65, top: 165, width: 240, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addBullet(s, "Jagged ECAL and HCAL hit lists: x, y, z position plus hit energy deposit.", 65, 200, 470, 14.5);
    addBullet(s, "Branch contract: ecal_posX/Y/Z, ecal_energy, hcal_posX/Y/Z, hcal_energy.", 65, 258, 470, 14.5);
    addBullet(s, "Positions are converted to cm with scale 0.1; hit signals use scale 1.0 GeV.", 65, 316, 470, 14.5);
    addText(s, "What comes out", { left: 690, top: 165, width: 240, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addBullet(s, "A total energy E_hat in GeV and three momentum components px_hat, py_hat, pz_hat.", 690, 200, 470, 14.5);
    addBullet(s, "The output is forced back onto the neutron mass shell, so E_hat^2 - |p_hat|^2 = m_n^2.", 690, 258, 470, 14.5);
    addBullet(s, "Headline scoring uses the locked test subset from 50 to 250 GeV.", 690, 316, 470, 14.5);
    addMetric(s, "4", "model heads: log kinetic + ux + uy + uz", 95, 470, 220, 105);
    addMetric(s, "195", "input scalar features from hits", 375, 470, 220, 105);
    addMetric(s, "50,685", "locked focus-test events", 655, 470, 220, 105);
    addMetric(s, "0.2044", "macro RMS rel. 4-vector error", 935, 470, 220, 105);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Before we start", "Key terms, in plain English", 3);
    addTable(s, [
      ["Term", "Meaning for this deck"],
      ["ZDC", "Zero Degree Calorimeter: a forward detector that measures neutral particles close to the beam line."],
      ["ECAL / HCAL", "Electromagnetic and hadronic sections. Neutrons mostly shower in HCAL, but ECAL still contributes geometry and early deposits."],
      ["Hit", "One simulated detector cell/sampling spot with a position and energy deposit. Each event has a variable number of hits."],
      ["Feature", "One fixed-length number derived from the hit cloud: total HCAL signal, shower centroid, depth profile, leakage proxy, and more."],
      ["Four-vector", "The physics output (E, px, py, pz). It contains both energy and direction/momentum."],
      ["On shell", "The output obeys the neutron mass relation. This keeps the prediction physically valid."],
      ["Boosting round", "One more tree added to an XGBoost head. Curves vs boosting show learning and overfitting behavior."],
    ], 78, 154, [160, 870], 50, { fontSize: 12.5 });
    addCallout(s, "Practical reading rule", "When a plot says 'focus', it means generator energy in the 50-250 GeV headline range. 'All test' means the full 0-300 GeV test support.", 820, 575, 350, 75);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Data", "Dataset and split contract", 4, "The model uses the same ROOT object staged for Vertex and verified locally by size, CRC32C, and SHA-256.");
    imagePromises.push(addImage(s, plots.data, { left: 685, top: 160, width: 520, height: 355 }, "Data overview plot"));
    addMetric(s, "764,940", "entries in latest tree myTree;865", 62, 170, 180, 96);
    addMetric(s, "25.02 GB", "ROOT object size", 265, 170, 180, 96);
    addMetric(s, "PDG 2112", "one neutron per event", 468, 170, 180, 96);
    addText(s, "Split counts", { left: 62, top: 310, width: 260, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addTable(s, [
      ["Split", "All 0-300 GeV", "Focus 50-250 GeV"],
      ["Train", "612,825", "408,276"],
      ["Validation", "76,010", "50,626"],
      ["Test", "76,105", "50,685"],
    ], 62, 345, [140, 150, 180], 44, { fontSize: 12.2, align: ["left", "right", "right"] });
    addText(s, "Data URI used by Vertex", { left: 62, top: 548, width: 260, height: 22 }, { fontSize: 14, bold: true, color: blue });
    addText(s, "gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root", { left: 62, top: 575, width: 660, height: 38 }, { fontSize: 11.5, color: body });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Detector inputs", "ECAL and HCAL are resolved by branch names and geometry", 5);
    addTable(s, [
      ["Logical input", "ROOT branch", "Unit / role"],
      ["ECAL hit position", "ecal_posX, ecal_posY, ecal_posZ", "global position; multiplied by 0.1 to cm"],
      ["ECAL hit signal", "ecal_energy", "ideal simulated deposit, GeV scale 1.0"],
      ["HCAL hit position", "hcal_posX, hcal_posY, hcal_posZ", "global position; multiplied by 0.1 to cm"],
      ["HCAL hit signal", "hcal_energy", "ideal simulated deposit, GeV scale 1.0"],
      ["Truth particle", "mcPar_PDG, mcPar_energy, mcPar_momX/Y/Z", "used only for targets and metrics"],
      ["Cell IDs", "ecal_cellID, hcal_cellID, hcal_LayerID", "used for fingerprint and detector provenance"],
    ], 50, 152, [190, 380, 510], 48, { fontSize: 11.3 });
    addCallout(s, "ECAL vs HCAL common sense", "The ecal_* branches are the electromagnetic calorimeter hit cloud; the hcal_* branches are the downstream hadronic calorimeter hit cloud. The locked detector frame points from ECAL center to HCAL center.", 87, 515, 500, 92);
    addCallout(s, "No truth leakage", "Features come from hit positions and calibrated hit signals. Truth branches are excluded from inference features and appear only in target building and scoring.", 650, 515, 500, 92);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Preflight QA", "The run locks units, truth convention, and detector frame before training", 6);
    addMetric(s, "2.48e-12", "median truth mass-shell residual", 70, 168, 210, 96, green);
    addMetric(s, "1.0", "ECAL and HCAL signal scale to GeV", 320, 168, 210, 96, blue);
    addMetric(s, "0.1 cm", "position scale applied to hit coordinates", 570, 168, 210, 96, blue);
    addMetric(s, "0", "negative hit signals allowed", 820, 168, 210, 96, green);
    addText(s, "Checks that matter", { left: 70, top: 315, width: 240, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addBullet(s, "Every event has exactly one selected neutron; all selected particles are PDG 2112.", 70, 352, 520, 14.5);
    addBullet(s, "mcPar_energy is total energy in GeV, confirmed by E^2 - |p|^2 = m_n^2.", 70, 410, 520, 14.5);
    addBullet(s, "energySum_* evidence and prior accepted pipeline lock ecal_energy and hcal_energy as GeV hit deposits.", 70, 468, 520, 14.5);
    addBullet(s, "The local ROOT object and staged GCS object match by size/CRC32C/SHA-256; no duplicate upload was needed.", 70, 526, 520, 14.5);
    addFormulaBox(s, "Locked local detector frame", [
      "origin = median ECAL center",
      "z_axis = unit(HCAL center - ECAL center)",
      "x/y axes = right-handed orthonormal basis",
      "local_points = (global_points - origin) @ rotation.T",
    ], 725, 330, 420, 190);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Pipeline", "End-to-end path from ROOT file to final metrics", 7);
    addFlow(s, [
      ["Inspect ROOT", "branch map, truth convention, detector frame, data hash"],
      ["Build targets", "single-neutron truth, kinetic energy, unit direction, event fingerprints"],
      ["Make split", "group-safe 80/10/10 split stratified by energy and angle"],
      ["Build features", "jagged ECAL/HCAL hits become 195 scalar features"],
      ["Train", "baselines plus XGBoost focus/full-support candidates"],
      ["Select/calibrate", "validation-focus macro score, energy affine calibration"],
      ["Unlock test", "one final focus-test read, plots, verification"],
    ], 45, 176, 1190, 118);
    addText(s, "What is heavy compute?", { left: 70, top: 360, width: 320, height: 28 }, { fontSize: 18, bold: true, color: blue });
    addBullet(s, "ROOT scan, feature materialization, XGBoost training, and loss-curve jobs were run from Vertex/GCS outputs, not repeated locally.", 70, 398, 560, 15);
    addBullet(s, "Local work here is presentation/report generation and QA using saved metrics, predictions, and diagnostic figures.", 70, 462, 560, 15);
    addCallout(s, "Accepted Vertex prefix", "gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs", 690, 380, 420, 95);
    addCallout(s, "Loss-curve prefix", "gs://asiop-zdc-1-zdc-reco-us-central1/runs/loss-curves-20260711/outputs", 690, 500, 420, 95, "#EAF2F8");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "From hits to features", "The model sees fixed-length scalar summaries, not raw jagged arrays", 8);
    addTable(s, [
      ["Feature family", "Examples", "Why it helps"],
      ["Energy totals", "ecal_total_signal_gev, hcal_total_signal_gev, visible_signal_gev", "First-order energy scale."],
      ["Hit intensity", "max_hit_gev, effective_n_hits, top-N energy fractions", "Separates diffuse and concentrated showers."],
      ["Centroid / RMS", "centroid_x/y/z, rms_x/y/z", "Encodes shower position and spread."],
      ["Depth profile", "2 ECAL groups, 8 HCAL groups, cumulative depth quantiles", "Captures shower start, peak, and back leakage."],
      ["Axis/PCA", "line-fit slopes, axis_u, residual RMS, PCA eigenvalue fractions", "Approximates incoming direction and shower elongation."],
      ["Leakage / boundary", "axis_exit_x/y, exit margins, hcal_back_leakage_proxy", "Flags events likely to leak out of the detector volume."],
      ["Quality flags", "empty, degenerate, no_detector_signal", "Makes zero/degenerate cases explicit instead of silent."],
    ], 45, 146, [210, 470, 430], 52, { fontSize: 10.8 });
    addCallout(s, "Feature count", "The final manifest has 195 detector-only scalar features. All source branches are ECAL/HCAL hit positions/signals; truth features are disallowed.", 805, 570, 350, 72);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Feature distribution", "What the focus-test hit summaries look like", 9);
    addTable(s, [
      ["Feature", "p05", "median", "p95", "Plain reading"],
      ["visible_signal_gev", "0.68", "2.91", "14.48", "Calorimeter deposits are much smaller than neutron total energy; regression is essential."],
      ["hcal_signal_fraction", "0.11", "0.92", "1.00", "Most visible signal sits in HCAL, as expected for neutrons."],
      ["all_n_hits", "504", "1,908", "3,429", "Each event is a large variable-length hit cloud."],
      ["hcal_back_energy_frac", "0.00", "0.00006", "0.030", "Back leakage is usually small but important for tails."],
      ["axis_exit_min_margin_cm", "-24.19", "4.02", "27.16", "Some fitted axes leave the detector footprint; margin is a risk feature."],
    ], 55, 157, [230, 90, 90, 90, 560], 59, { fontSize: 11.2 });
    addText(s, "Interpretation", { left: 70, top: 545, width: 180, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addText(s, "The model is not doing simple E_visible -> E_true scaling. It combines visible energy with shower location, direction, depth development, concentration, and leakage proxies.", { left: 215, top: 545, width: 830, height: 52 }, { fontSize: 15, color: body });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "The math, part 1", "Training target: log kinetic energy plus true direction", 10);
    addFormulaBox(s, "Truth quantities", [
      "m_n = 0.93956542052 GeV",
      "E_true = sqrt(px_true^2 + py_true^2 + pz_true^2 + m_n^2)",
      "K_true = E_true - m_n",
      "u_true = p_true / ||p_true|| = (ux, uy, uz)",
    ], 70, 160, 535, 180);
    addFormulaBox(s, "Target vector used by XGBoost", [
      "y = [ log1p(K_true), ux_true, uy_true, uz_true ]",
      "log1p(K) = log(1 + K)",
      "Why log kinetic energy? It keeps low energy resolution visible",
      "while still representing the full 0-300 GeV support.",
    ], 675, 160, 535, 180);
    addText(s, "Why not train E, px, py, pz directly?", { left: 90, top: 410, width: 420, height: 28 }, { fontSize: 18, bold: true, color: blue });
    addBullet(s, "Direct four-vector regression can produce physically impossible outputs that violate the neutron mass relation.", 90, 452, 505, 15);
    addBullet(s, "Separating kinetic energy from direction gives the model an easier structure: one positive scale plus a unit vector.", 90, 510, 505, 15);
    addBullet(s, "The final conversion guarantees an on-shell neutron four-vector after calibration.", 90, 568, 505, 15);
    addCallout(s, "Target names in code", "log1p_kinetic, ux, uy, uz. The saved champion model contains one XGBoost booster per target head.", 745, 442, 355, 112, "#EAF2F8");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "The math, part 2", "Prediction is projected back to an on-shell neutron", 11);
    addFormulaBox(s, "Raw model outputs", [
      "y_hat_K = model_K(features)",
      "v_hat = [model_ux(features), model_uy(features), model_uz(features)]",
      "K_hat_raw = max(expm1(y_hat_K), 0)",
      "u_hat = v_hat / ||v_hat||",
    ], 68, 160, 535, 188);
    addFormulaBox(s, "Physics projection", [
      "E_hat_raw = K_hat_raw + m_n",
      "|p_hat| = sqrt(max(E_hat_raw^2 - m_n^2, 0))",
      "p_hat = |p_hat| * u_hat",
      "four-vector = (E_hat_raw, px_hat, py_hat, pz_hat)",
    ], 675, 160, 535, 188);
    addFormulaBox(s, "Validation energy calibration", [
      "E_hat_cal = max(0.988213 * E_hat_raw + 3.103, m_n)",
      "direction is kept from p_hat_raw",
      "p_hat_cal = sqrt(E_hat_cal^2 - m_n^2) * u_hat",
      "source: validation focus after model selection",
    ], 68, 430, 535, 150, paleOrange);
    addFormulaBox(s, "Mass-shell QA", [
      "residual = E_hat^2 - px_hat^2 - py_hat^2 - pz_hat^2 - m_n^2",
      "max |residual| on focus test = 3.28e-11 GeV^2",
      "This checks numerical consistency, not predictive accuracy.",
    ], 675, 430, 535, 150);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "The ML method", "XGBoost here means four boosted-tree regressors plus physics postprocessing", 12);
    addFlow(s, [
      ["195 features", "fixed vector from ECAL/HCAL hits"],
      ["Booster 1", "predict log1p kinetic energy"],
      ["Boosters 2-4", "predict ux, uy, uz direction heads"],
      ["Normalize", "turn direction heads into unit vector"],
      ["Project", "build on-shell neutron four-vector"],
      ["Calibrate", "validation affine correction on total energy"],
    ], 70, 170, 1080, 116);
    addText(s, "How boosting works", { left: 80, top: 365, width: 300, height: 28 }, { fontSize: 18, bold: true, color: blue });
    addBullet(s, "Start with a simple prediction, then add small decision trees that correct the remaining errors.", 80, 407, 520, 15);
    addBullet(s, "Each head trains independently but receives the same feature matrix and the same event weights.", 80, 466, 520, 15);
    addBullet(s, "The final four-vector is not just the raw tree output; the physics layer enforces nonnegative kinetic energy, unit direction, and neutron mass.", 80, 525, 520, 15);
    addCallout(s, "Important caveat", "This accepted result is scalar-feature XGBoost. It is not the newer dual-grid neural model requested in the original one-shot; no dual-grid neural artifact is claimed here.", 725, 405, 410, 120);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Training setup", "Every major parameter needed to rebuild the accepted run", 13);
    addTable(s, [
      ["Setting", "Value", "Meaning"],
      ["target", "log1p(K) + ux,uy,uz", "four heads, later converted to on-shell four-vector"],
      ["support candidates", "focus_only; full_support", "train on 50-250 only or include shoulders with lower weight"],
      ["energy bin balance", "true", "equalizes training influence across required energy bins"],
      ["objective", "reg:squarederror", "squared-error loss per head"],
      ["eval_metric", "rmse", "validation monitor used for early stopping"],
      ["tree_method / device", "hist / cpu", "histogram tree builder on CPU Vertex job"],
      ["learning_rate", "0.04", "small contribution from each added tree"],
      ["max_depth", "7", "maximum tree depth"],
      ["min_child_weight", "20", "regularizes small leaves"],
      ["subsample / colsample", "0.9 / 0.9", "random event and feature subsampling per tree"],
      ["reg_lambda / reg_alpha", "3.0 / 0.0", "L2 and L1 regularization"],
      ["max rounds / early stop", "2500 / 80", "hard cap and stop patience"],
      ["seed", "20260710", "reproducible split/config seed"],
    ], 55, 144, [220, 250, 620], 36, { fontSize: 10.3 });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Selection policy", "Validation chooses the model; test is opened once", 14);
    imagePromises.push(addImage(s, plots.leaderboard, { left: 650, top: 154, width: 540, height: 360 }, "Validation leaderboard"));
    addText(s, "Candidate path", { left: 70, top: 165, width: 240, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addBullet(s, "Baselines: visible-sum axis, constrained ridge, direct ridge diagnostic.", 70, 204, 500, 14.5);
    addBullet(s, "XGBoost candidates: M1_xgb_focus_only and M1_xgb_full_support.", 70, 260, 500, 14.5);
    addBullet(s, "Ranking metric: validation-focus macro RMS relative four-vector error.", 70, 316, 500, 14.5);
    addBullet(s, "Champion: M1_xgb_focus_only, validation macro RMS 0.2039.", 70, 372, 500, 14.5);
    addCallout(s, "Calibration order", "Tuning ends before calibration and test access. The selected model receives an affine validation energy calibration, then the test split is unlocked once.", 95, 500, 430, 92);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Scoring", "The exact metrics used in the deck", 15);
    addTable(s, [
      ["Metric", "Definition", "Plain reading"],
      ["relative four-vector error", "||p_hat^mu - p_true^mu||_2 / max(E_true, eps)", "one event-level four-vector miss, scaled by true energy"],
      ["macro RMS rel. 4-vector", "mean over 25-GeV focus bins of sqrt(mean(error^2))", "headline score; prevents dense bins from dominating"],
      ["energy relative RMSE", "sqrt(mean((E_hat/E_true - 1)^2))", "fractional energy scatter, including bias"],
      ["energy width68", "0.5 * (q84 - q16) of E_hat/E_true - 1", "central 68% half-width of energy response"],
      ["angular error", "1000 * arccos(u_true dot u_hat)", "direction error in milliradians"],
      ["mass-shell residual", "E_hat^2 - px_hat^2 - py_hat^2 - pz_hat^2 - m_n^2", "physics consistency check after projection"],
    ], 50, 152, [240, 430, 470], 58, { fontSize: 10.8 });
    addCallout(s, "Focus bins", "Required bin edges: 50, 75, 100, 125, 150, 175, 200, 225, 250 GeV. Empty bins are a hard error.", 770, 566, 360, 72, "#EAF2F8");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Boosting curves", "Overall train and validation loss vs boosting round", 16);
    imagePromises.push(addImage(s, plots.lossOverall, { left: 85, top: 150, width: 750, height: 430 }, "Overall train validation loss vs boosting"));
    addText(s, "Best validation point", { left: 890, top: 174, width: 260, height: 26 }, { fontSize: 17, bold: true, color: blue });
    addMetric(s, "round 735", "best validation round", 890, 225, 210, 90);
    addMetric(s, "0.2143", "validation rel. 4-vector RMSE", 890, 335, 210, 90);
    addMetric(s, "+0.0235", "validation minus train gap", 890, 445, 210, 90, orange);
    addText(s, "The gap is positive but not exploding. The validation curve improves with training and does not separate sharply from train loss.", { left: 860, top: 555, width: 315, height: 60 }, { fontSize: 12.5, color: body });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Boosting curves", "Separate E, px, py, pz train/validation losses", 17);
    imagePromises.push(addImage(s, plots.lossE, { left: 45, top: 148, width: 560, height: 230 }, "E loss vs boosting"));
    imagePromises.push(addImage(s, plots.lossPx, { left: 660, top: 148, width: 560, height: 230 }, "px loss vs boosting"));
    imagePromises.push(addImage(s, plots.lossPy, { left: 45, top: 405, width: 560, height: 230 }, "py loss vs boosting"));
    imagePromises.push(addImage(s, plots.lossPz, { left: 660, top: 405, width: 560, height: 230 }, "pz loss vs boosting"));
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Boosting curves", "Native head losses and train-validation gaps", 18);
    imagePromises.push(addImage(s, plots.nativeGrid, { left: 45, top: 150, width: 560, height: 250 }, "Native target loss grid"));
    imagePromises.push(addImage(s, plots.lossGap, { left: 675, top: 150, width: 500, height: 220 }, "Overall loss gap"));
    imagePromises.push(addImage(s, plots.componentGaps, { left: 70, top: 425, width: 520, height: 190 }, "Component train validation gaps"));
    imagePromises.push(addImage(s, plots.bestRound, { left: 690, top: 415, width: 470, height: 200 }, "Best round train validation bars"));
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Headline result", "Locked focus-test performance for M1_xgb_focus_only", 19);
    addMetric(s, "0.2044", "macro RMS relative four-vector error", 70, 165, 220, 106);
    addMetric(s, "0.2186", "micro RMS relative four-vector error", 330, 165, 220, 106);
    addMetric(s, "11.48", "energy MAE, GeV", 590, 165, 220, 106);
    addMetric(s, "15.44%", "energy relative RMSE", 850, 165, 220, 106);
    addMetric(s, "+2.38%", "mean energy response bias", 70, 322, 220, 106, orange);
    addMetric(s, "7.15%", "central-68 energy width", 330, 322, 220, 106);
    addMetric(s, "5.87", "median angular error, mrad", 590, 322, 220, 106);
    addMetric(s, "16.62", "95% angular error, mrad", 850, 322, 220, 106);
    addCallout(s, "Read this slide carefully", "These are final locked-test metrics on 50-250 GeV events. They are not validation numbers and they are not previous-model comparison numbers.", 180, 515, 760, 82, "#EAF2F8");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Results", "Predicted vs true components", 20);
    imagePromises.push(addImage(s, plots.predTrue, { left: 55, top: 145, width: 1120, height: 475 }, "Component predicted vs true"));
    addText(s, "The diagonal pattern shows the four outputs track truth across the focus population. Energy and pz are harder because forward energy and longitudinal momentum carry the main scale.", { left: 100, top: 620, width: 980, height: 28 }, { fontSize: 12.5, color: muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Results", "Component residual sizes explain where the error lives", 21);
    imagePromises.push(addImage(s, plots.residuals, { left: 50, top: 148, width: 540, height: 330 }, "Component residuals"));
    imagePromises.push(addImage(s, plots.componentBars, { left: 650, top: 148, width: 540, height: 330 }, "Component metric bars"));
    addTable(s, [
      ["Component", "MAE GeV", "RMSE GeV", "R2", "p95 abs err GeV"],
      ["E", "11.48", "20.06", "0.879", "42.86"],
      ["px", "2.37", "5.06", "0.968", "9.85"],
      ["py", "2.38", "5.06", "0.967", "10.11"],
      ["pz", "10.89", "18.81", "0.887", "40.24"],
    ], 132, 525, [160, 120, 120, 100, 165], 32, { fontSize: 10.8, align: ["left", "right", "right", "right", "right"] });
    addText(s, "Focus test only", { left: 840, top: 542, width: 200, height: 22 }, { fontSize: 13, bold: true, color: blue });
    addText(s, "Transverse components are much tighter than E and pz; that is normal for a forward neutron where most momentum is longitudinal.", { left: 840, top: 568, width: 300, height: 55 }, { fontSize: 12.5, color: body });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Energy behavior", "Response density and one-dimensional residual view", 22);
    imagePromises.push(addImage(s, plots.energyDensity, { left: 45, top: 150, width: 560, height: 380 }, "Energy response density"));
    imagePromises.push(addImage(s, plots.basicResidual, { left: 680, top: 165, width: 470, height: 320 }, "Focus energy residual histogram"));
    addBullet(s, "Mean response: 1.0238; median response: 1.0166.", 92, 560, 470, 13.5);
    addBullet(s, "Central 68% width of relative energy response: 7.15%.", 92, 600, 470, 13.5);
    addBullet(s, "Energy MAE is 11.48 GeV on the focus test population.", 720, 560, 420, 13.5);
    addBullet(s, "The residual tail drives RMSE above the central width, so slice and tail plots matter.", 720, 600, 420, 13.5);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Energy slices", "Bias and resolution by generator-energy region", 23);
    imagePromises.push(addImage(s, plots.energySlices, { left: 55, top: 145, width: 760, height: 440 }, "Energy bias resolution slices"));
    imagePromises.push(addImage(s, plots.sliceDiag, { left: 850, top: 170, width: 340, height: 275 }, "Focus energy slice diagnostics"));
    addText(s, "Why this matters", { left: 870, top: 485, width: 250, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addBullet(s, "A single headline error can hide low-energy or high-energy slice problems.", 870, 525, 290, 12.8);
    addBullet(s, "The model is selected on macro RMS across focus bins to keep slices visible.", 870, 585, 290, 12.8);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Momentum slices", "Component bias and resolution by energy", 24);
    imagePromises.push(addImage(s, plots.componentSlices, { left: 45, top: 145, width: 1120, height: 465 }, "Component bias resolution slices"));
    addText(s, "px and py behave similarly and remain much narrower than pz. Longitudinal momentum follows the energy scale, so pz inherits much of the energy-resolution challenge.", { left: 92, top: 620, width: 1000, height: 28 }, { fontSize: 12.5, color: muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Direction", "Angular error is small for the focus-test population", 25);
    imagePromises.push(addImage(s, plots.angular, { left: 90, top: 150, width: 660, height: 420 }, "Angular error plot"));
    addMetric(s, "1.000", "valid direction fraction", 850, 175, 200, 88, green);
    addMetric(s, "5.87", "median angular error, mrad", 850, 285, 200, 88);
    addMetric(s, "7.98", "68% angular error, mrad", 850, 395, 200, 88);
    addMetric(s, "16.62", "95% angular error, mrad", 850, 505, 200, 88, orange);
    addText(s, "Angular error is computed from the dot product of true and predicted unit directions, then converted from radians to milliradians.", { left: 94, top: 595, width: 780, height: 30 }, { fontSize: 12.5, color: muted });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Physics QA", "Mass-shell residual confirms the projection is numerically clean", 26);
    imagePromises.push(addImage(s, plots.shell, { left: 120, top: 150, width: 610, height: 420 }, "Mass shell residual plot"));
    addFormulaBox(s, "Check", [
      "residual = E_hat^2 - px_hat^2 - py_hat^2 - pz_hat^2 - m_n^2",
      "max |residual| = 3.277e-11 GeV^2",
      "RMS residual = 5.62e-12 GeV^2",
    ], 800, 210, 330, 150);
    addCallout(s, "Meaning", "This does not say the model is perfect. It says the prediction is physically formatted as a neutron after postprocessing, so downstream analysis does not receive impossible four-vectors.", 790, 420, 360, 112);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Interpretation", "Which features does XGBoost use most?", 27);
    imagePromises.push(addImage(s, plots.importance, { left: 55, top: 145, width: 730, height: 460 }, "Feature importance"));
    addText(s, "Top mean-gain features", { left: 835, top: 165, width: 260, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addTable(s, [
      ["Rank", "Feature", "Mean gain"],
      ["1", "hcal_total_signal_gev", "47.41"],
      ["2", "hcal_density_bin02_energy_frac", "11.27"],
      ["3", "hcal_top20_energy_frac", "4.95"],
      ["4", "all_centroid_y_cm", "4.59"],
      ["5", "hcal_centroid_x_cm", "4.54"],
      ["6", "hcal_effective_n_hits", "4.38"],
      ["7", "axis_exit_min_margin_cm", "3.78"],
    ], 835, 205, [60, 225, 90], 34, { fontSize: 9.8, align: ["right", "left", "right"] });
    addCallout(s, "Honest read", "HCAL total signal dominates, but the model also uses shower concentration, centroid, effective hit count, and edge/leakage information.", 835, 500, 355, 92, "#EAF2F8");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Error drivers", "Tail events line up with leakage and shower-shape features", 28);
    imagePromises.push(addImage(s, plots.errorDrivers, { left: 45, top: 145, width: 545, height: 235 }, "Error driver correlations"));
    imagePromises.push(addImage(s, plots.tailContrast, { left: 660, top: 145, width: 545, height: 235 }, "Tail feature contrast"));
    imagePromises.push(addImage(s, plots.featureError, { left: 350, top: 415, width: 560, height: 220 }, "Top feature error correlations"));
    addText(s, "Use these as diagnostic clues, not causal proof. They point to which event shapes should be inspected when errors get large.", { left: 170, top: 635, width: 940, height: 24 }, { fontSize: 12.2, color: muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Study range", "Focus behavior vs full 0-300 GeV test support", 29);
    imagePromises.push(addImage(s, plots.focusAll, { left: 45, top: 148, width: 545, height: 360 }, "Focus vs all component metrics"));
    imagePromises.push(addImage(s, plots.heatmap, { left: 660, top: 148, width: 545, height: 360 }, "Resolution heatmap"));
    addCallout(s, "Why focus is the headline", "The one-shot target is 50-250 GeV. The model can be evaluated on all 0-300 GeV test rows, but the accepted claim is the locked focus-test result.", 120, 550, 440, 82);
    addCallout(s, "Do not extrapolate", "No slide in this deck claims validity for other particle species, real-detector electronics, or data outside the simulated distribution.", 710, 550, 440, 82, "#EAF2F8");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Uncertainty", "Empirical validation intervals were checked once on test", 30);
    addTable(s, [
      ["Nominal interval", "Validation abs-energy width", "Focus-test coverage", "Interpretation"],
      ["68%", "10.02 GeV", "68.08%", "matches target closely"],
      ["90%", "27.99 GeV", "90.21%", "matches target closely"],
      ["95%", "43.11 GeV", "95.06%", "matches target closely"],
    ], 90, 170, [170, 240, 210, 420], 60, { fontSize: 12.3, align: ["left", "right", "right", "left"] });
    addFormulaBox(s, "Calibration source", [
      "Validation focus is reused for model selection and calibration.",
      "interval_width_c = quantile(|E_true - E_hat_cal|, c)",
      "coverage_c = mean(|E_true - E_hat_cal| <= interval_width_c) on test",
    ], 110, 435, 520, 146);
    addCallout(s, "Caveat", "These are empirical intervals, not a formal split-conformal guarantee, because there is no independent calibration split after model selection.", 700, 445, 370, 126);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "QA and QC", "What was checked before accepting the result", 31);
    addTable(s, [
      ["Gate", "Status", "Evidence"],
      ["Repository/read-me intake", "pass", "read task files and repo structure before continuing"],
      ["Local source sanity", "pass", "compileall, unittest, pytest, Ruff, smoke from clean package"],
      ["Data staging", "pass", "local ROOT matches US-CENTRAL1 GCS object"],
      ["Truth convention", "pass", "single neutron; total-energy GeV mass-shell closure"],
      ["Hit unit contract", "pass", "ecal_energy/hcal_energy locked as GeV simulated deposits"],
      ["Split integrity", "pass", "group-safe deterministic split; no duplicate fingerprint leakage"],
      ["Model selection", "pass", "validation-focus macro score selects M1_xgb_focus_only"],
      ["Test unlock", "pass", "test read occurs after selection and calibration"],
      ["Physics output", "pass", "mass-shell residual max 3.28e-11 GeV^2"],
      ["Presentation QA", "pass", "render, montage, overflow test, and visual inspection"],
    ], 65, 150, [250, 90, 720], 42, { fontSize: 10.7 });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Rebuild recipe", "How a colleague can reproduce this if they have the data", 32);
    addText(s, "1. Data", { left: 70, top: 155, width: 160, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addText(s, "Place the ROOT file in GCS or local disk. Expected object: myTree_20251117_765k_0to300GeV_neutron_All.root, SHA-256 b7c666040e42352e158a9a3f78158d147cb2e056c6c88248d892c956f5c7b533.", { left: 210, top: 154, width: 920, height: 50 }, { fontSize: 12.5, color: body });
    addText(s, "2. Config", { left: 70, top: 230, width: 160, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addText(s, "Use configs/legacy_vertex_default.yaml. Critical values: neutron mass 0.93956542052 GeV, focus 50-250 GeV, train/validation/test 80/10/10, ECAL/HCAL signal scale 1.0, position scale 0.1 cm, 195 scalar detector features, XGBoost params from slide 13.", { left: 210, top: 230, width: 920, height: 72 }, { fontSize: 12.5, color: body });
    addText(s, "3. Run on Vertex", { left: 70, top: 330, width: 150, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addFormulaBox(s, "Command", [
      "DATA_GCS=gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root",
      "OUT_GCS=gs://asiop-zdc-1-zdc-reco-us-central1/runs/rebuild-<DATE>/outputs",
      "python -m zdc_reco.cli run-all-gcs \\",
      "  --data-gcs $DATA_GCS --output-gcs $OUT_GCS \\",
      "  --config configs/legacy_vertex_default.yaml \\",
      "  --workdir /tmp/zdc_run",
    ], 250, 320, 850, 142);
    addText(s, "4. Verify and present", { left: 70, top: 500, width: 180, height: 24 }, { fontSize: 17, bold: true, color: blue });
    addBullet(s, "Verify outputs: inspection report, schema lock, targets, splits, feature manifest, leaderboard, champion, calibration, test metrics, interval coverage, and plots.", 210, 500, 870, 12.8);
    addBullet(s, "Expected headline result for this accepted run: macro RMS 0.2044, energy MAE 11.48 GeV, angular median 5.87 mrad, on-shell residual max 3.28e-11 GeV^2.", 210, 562, 870, 12.8);
  }

  await Promise.all(imagePromises);
  return deck;
}

async function main() {
  await ensureDirs();
  const deck = await buildDeck();
  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(PREVIEW_DIR, `${stem}.png`), await deck.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  await writeBlob(path.join(QA_DIR, "deck-montage.webp"), await deck.export({ format: "webp", montage: true, scale: 1 }));
  const inspect = await deck.inspect({ kind: "slide,textbox,shape,image,table,chart", maxChars: 20000 });
  await fs.writeFile(path.join(QA_DIR, "deck-inspect.ndjson"), inspect.ndjson, "utf8");
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
