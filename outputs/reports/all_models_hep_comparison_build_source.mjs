import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/Julia/OneDrive/Desktop/coding/ASIoP/ML ZDC all 1";
const TMP = "C:/Users/Julia/AppData/Local/Temp/codex-presentations/manual-zdc-model-comparison/tmp";
const INPUT = `${TMP}/input`;
const ASSETS = `${TMP}/assets`;
const PREVIEW = `${TMP}/preview`;
const LAYOUT = `${TMP}/layout`;
const QA = `${TMP}/qa`;
const OUT = `${ROOT}/outputs/ZDC_All_Models_HEP_Comparison.pptx`;

const W = 1280;
const H = 720;
const C = {
  ink: "#101820",
  body: "#303841",
  muted: "#68717A",
  paper: "#FFFFFF",
  panel: "#F3F5F7",
  rule: "#C7CDD3",
  blue: "#2F7ED8",
  blueLight: "#BFDDF4",
  orange: "#D96C2F",
  orangeLight: "#F4D2BF",
  green: "#4C9A62",
  greenLight: "#CFE9D6",
  red: "#BF3A3A",
  redLight: "#F4CDCD",
  gray: "#7A8793",
  darkGray: "#53606B",
};
const FONT = "Arial";

const assets = {
  pred: `${ASSETS}/component_pred_vs_true.png`,
  residual: `${ASSETS}/component_residuals.png`,
  energySlices: `${ASSETS}/energy_bias_resolution.png`,
  componentSlices: `${ASSETS}/component_bias_resolution.png`,
  angular: `${ASSETS}/angular_error.png`,
  importance: `${ASSETS}/feature_importance.png`,
  pencil: `${ASSETS}/pencil_vs_all_neutron.png`,
  shell: `${ASSETS}/mass_shell.png`,
  energyDensity: `${ASSETS}/energy_response_density.png`,
  lossOverall: `${ASSETS}/loss_overall.png`,
  lossComponents: `${ASSETS}/loss_components.png`,
  lossNative: `${ASSETS}/loss_native_heads.png`,
  errorCorrelations: `${ASSETS}/error_correlations.png`,
  tailFeatures: `${ASSETS}/tail_features.png`,
  focusSlices: `${ASSETS}/focus_slices.png`,
  previousRuns: `${ASSETS}/previous_runs.png`,
};

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function imageBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
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
    fontSize: style.fontSize ?? 16,
    bold: style.bold ?? false,
    color: style.color ?? C.body,
    alignment: style.alignment ?? "left",
    typeface: style.typeface ?? FONT,
  };
  return shape;
}

function addRect(slide, position, fill = C.paper, stroke = "none", width = 1) {
  return slide.shapes.add({
    geometry: "rect",
    position,
    fill,
    line: { style: "solid", fill: stroke, width: stroke === "none" ? 0 : width },
  });
}

function addRule(slide, y) {
  addRect(slide, { left: 41, top: y, width: 1198, height: 1 }, C.rule, "none");
}

function addFooter(slide, number, source = "") {
  addText(slide, source || "ASIoP ZDC all-neutron reconstruction studies", { left: 42, top: 679, width: 1000, height: 16 }, { fontSize: 9.5, color: C.muted });
  addText(slide, String(number), { left: 1180, top: 679, width: 54, height: 16 }, { fontSize: 10, color: C.muted, alignment: "right" });
}

function addHeader(slide, section, title, number, subtitle = "") {
  addText(slide, section.toUpperCase(), { left: 42, top: 28, width: 380, height: 18 }, { fontSize: 11.5, bold: true, color: C.blue });
  addText(slide, title, { left: 42, top: 52, width: 1140, height: 46 }, { fontSize: 36, bold: true, color: C.ink });
  if (subtitle) addText(slide, subtitle, { left: 42, top: 101, width: 1110, height: 22 }, { fontSize: 13, color: C.muted });
  addRule(slide, subtitle ? 130 : 116);
  addFooter(slide, number);
}

function addImage(slide, filePath, position, alt, fit = "contain") {
  return imageBytes(filePath).then((blob) => {
    slide.images.add({ blob, contentType: "image/png", alt, fit, position });
  });
}

function addMetric(slide, value, label, position, accent = C.blue) {
  addRect(slide, position, C.paper, C.rule, 1);
  addRect(slide, { left: position.left, top: position.top, width: position.width, height: 5 }, accent, "none");
  addText(slide, value, { left: position.left + 12, top: position.top + 20, width: position.width - 24, height: 34 }, { fontSize: 27, bold: true, color: accent, alignment: "center" });
  addText(slide, label, { left: position.left + 12, top: position.top + 61, width: position.width - 24, height: position.height - 70 }, { fontSize: 12, color: C.muted, alignment: "center" });
}

function addNote(slide, title, body, position, accent = C.blueLight) {
  addRect(slide, position, accent, C.rule, 0.8);
  addText(slide, title, { left: position.left + 15, top: position.top + 12, width: position.width - 30, height: 22 }, { fontSize: 14.5, bold: true, color: C.ink });
  addText(slide, body, { left: position.left + 15, top: position.top + 39, width: position.width - 30, height: position.height - 48 }, { fontSize: 12.5, color: C.body });
}

function addBullet(slide, text, left, top, width, color = C.body) {
  addRect(slide, { left, top: top + 6, width: 7, height: 7 }, C.blue, "none");
  addText(slide, text, { left: left + 17, top, width: width - 17, height: 46 }, { fontSize: 14, color });
}

function addTable(slide, rows, left, top, widths, rowHeight, opts = {}) {
  let total = 0;
  for (const width of widths) total += width;
  rows.forEach((row, rowIndex) => {
    const fill = rowIndex === 0 ? C.ink : rowIndex % 2 === 0 ? "#F8FAFB" : C.paper;
    let x = left;
    row.forEach((cell, colIndex) => {
      addRect(slide, { left: x, top: top + rowIndex * rowHeight, width: widths[colIndex], height: rowHeight }, fill, C.rule, 0.6);
      addText(slide, String(cell), { left: x + 6, top: top + rowIndex * rowHeight + 5, width: widths[colIndex] - 12, height: rowHeight - 8 }, {
        fontSize: opts.fontSize ?? 11.5,
        bold: rowIndex === 0,
        color: rowIndex === 0 ? C.paper : C.body,
        alignment: opts.align?.[colIndex] ?? "left",
      });
      x += widths[colIndex];
    });
  });
  addRect(slide, { left, top, width: total, height: rows.length * rowHeight }, "none", C.rule, 0.9);
}

function addFlow(slide, boxes, left, top, width, height) {
  const gap = 14;
  const boxW = (width - gap * (boxes.length - 1)) / boxes.length;
  boxes.forEach((item, index) => {
    const x = left + index * (boxW + gap);
    addRect(slide, { left: x, top, width: boxW, height }, index % 2 ? "#F5F7F9" : "#EAF3FA", C.rule, 0.8);
    addText(slide, item[0], { left: x + 10, top: top + 13, width: boxW - 20, height: 28 }, { fontSize: 13, bold: true, color: C.blue, alignment: "center" });
    addText(slide, item[1], { left: x + 12, top: top + 47, width: boxW - 24, height: height - 55 }, { fontSize: 11.5, color: C.body, alignment: "center" });
    if (index < boxes.length - 1) addText(slide, ">", { left: x + boxW, top: top + height / 2 - 14, width: gap + 8, height: 28 }, { fontSize: 20, bold: true, color: C.orange, alignment: "center" });
  });
}

function addChart(slide, chartType, config) {
  slide.charts.add(chartType, {
    chartFill: C.paper,
    chartLine: { style: "solid", fill: C.paper, width: 0 },
    plotAreaFill: { type: "none" },
    plotAreaLine: { style: "solid", fill: C.paper, width: 0 },
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { fontSize: 11, fill: C.body } },
    xAxis: { textStyle: { fontSize: 11, fill: C.body }, line: { style: "solid", fill: C.rule, width: 1 }, majorGridlines: null },
    yAxis: { textStyle: { fontSize: 11, fill: C.body }, line: { style: "solid", fill: C.paper, width: 0 }, majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 } },
    ...config,
  });
}

function compactCandidateRows(rows, suffix) {
  const labels = {
    B0_visible_sum_axis: "B0 visible sum",
    B1_ridge_constrained: "B1 ridge",
    M2_ridge_direct_projected: "M2 direct ridge",
    M1_xgb_focus_only: "M1 focus only",
    M1_xgb_full_support: "M1 full support",
  };
  return rows.map((row) => ({ label: labels[row.model_id] || row.model_id, value: Number(row.macro_rms_relative_fourvector_error), maer: Number(row.energy_mae_gev), support: suffix }));
}

function lossSeries(loss, component, split) {
  const rows = loss.filter((r) => r.component === component && r.split === split);
  return rows.map((r) => Number(r.rmse));
}

async function buildDeck(data) {
  const deck = Presentation.create({ slideSize: { width: W, height: H } });
  const imageJobs = [];
  const logCandidates = compactCandidateRows(data.log_validation, "log1p(K)");
  const rawCandidates = compactCandidateRows(data.raw_validation, "K");
  const componentKeys = ["E", "px", "py", "pz"];
  const componentRMSELog = componentKeys.map((k) => data.components[k].accepted.rmse);
  const componentRMSERaw = componentKeys.map((k) => data.components[k].raw.rmse);
  const componentNRMSELog = componentKeys.map((k) => data.components[k].accepted.nrmse);
  const componentNRMSERaw = componentKeys.map((k) => data.components[k].raw.nrmse);
  const componentR2Log = componentKeys.map((k) => data.components[k].accepted.r2);
  const componentR2Raw = componentKeys.map((k) => data.components[k].raw.r2);
  const componentP10Log = componentKeys.map((k) => data.components[k].accepted.p10);
  const componentP10Raw = componentKeys.map((k) => data.components[k].raw.p10);

  {
    const s = deck.slides.add();
    s.background.fill = C.paper;
    imageJobs.push(addImage(s, assets.pred, { left: 570, top: 0, width: 710, height: 720 }, "Four-vector component prediction-versus-truth density plots", "cover"));
    addRect(s, { left: 0, top: 0, width: 570, height: 720 }, C.paper, "none");
    addRect(s, { left: 0, top: 0, width: W, height: 8 }, C.blue, "none");
    addText(s, "ASIoP ZDC", { left: 48, top: 78, width: 260, height: 22 }, { fontSize: 13, bold: true, color: C.blue });
    addText(s, "All-model\nHEP analysis", { left: 48, top: 165, width: 470, height: 140 }, { fontSize: 56, bold: true, color: C.ink });
    addText(s, "Archived ML ZDC all results, ML ZDC all 1 results, historical Vertex runs, and the direct-kinetic-MSE retrain", { left: 48, top: 338, width: 460, height: 70 }, { fontSize: 18, color: C.body });
    addText(s, "Simulation study: single-neutron ZDC reconstruction of (E, px, py, pz)", { left: 48, top: 585, width: 470, height: 24 }, { fontSize: 13.5, color: C.muted });
    addText(s, "Focus range: 50-250 GeV", { left: 48, top: 616, width: 470, height: 20 }, { fontSize: 13.5, color: C.muted });
    addFooter(s, 1, "Sources: ML ZDC all archive + ML ZDC all 1 Vertex artifacts");
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Study map", "The two folders are linked by a shared finalfix2 artifact set", 2);
    addFlow(s, [
      ["ML ZDC all", "Archived presentation bundle: finalfix2 model, plots, loss curves, pencil-beam comparison."],
      ["ML ZDC all 1", "Source, locked data contract, expanded diagnostics, historical Vertex run records."],
      ["finalfix2", "The same accepted M1 XGBoost focus-only model appears in both folders."],
      ["raw-K retrain", "New Vertex output in ML ZDC all 1: direct kinetic-energy target, same event IDs."],
    ], 55, 175, 1170, 138);
    addNote(s, "Deck handling", "The shared finalfix2 artifact is displayed once. Historical runs are labeled by run ID. The direct-K retrain is shown as a separate target-parameterization result.", { left: 100, top: 420, width: 470, height: 105 }, C.blueLight);
    addNote(s, "What is included", "Trained models with saved results: B0, B1, M2, log-target M1 focus/full support, direct-K M1 focus/full support, and the archived run-level variants. Pencil-beam is labeled as a different energy-only task.", { left: 650, top: 420, width: 470, height: 105 }, C.greenLight);
    addText(s, "The N1 dual-grid network, H1 blend, and G1 Deep Sets/GNN appear in the design record but have no saved model output or performance metric in the supplied artifacts.", { left: 165, top: 580, width: 960, height: 30 }, { fontSize: 13, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Event contract", "Common data, split, and scoring range", 3);
    addMetric(s, "764,940", "events in myTree;865", { left: 65, top: 165, width: 210, height: 100 });
    addMetric(s, "80/10/10", "train / validation / locked test split", { left: 315, top: 165, width: 210, height: 100 });
    addMetric(s, "50-250", "headline generator-energy range, GeV", { left: 565, top: 165, width: 210, height: 100 });
    addMetric(s, "50,685", "focus-test events", { left: 815, top: 165, width: 210, height: 100 });
    addTable(s, [
      ["Object", "Recorded contract"],
      ["Particle", "Exactly one neutron per selected event, PDG 2112."],
      ["Detector inputs", "Jagged ECAL/HCAL hit positions and deposited signals; position scale 0.1 to cm; signal scale 1.0 GeV."],
      ["Truth", "mcPar_energy and mcPar_momX/Y/Z create E, px, py, pz targets. Truth is not an inference feature."],
      ["Features", "195 archived scalar detector features: totals, hit counts, shower centroid/RMS, depth, axis/PCA, leakage and quality flags."],
      ["Evaluation", "Macro RMS relative four-vector error on locked 50-250 GeV test rows; component metrics use final calibrated physical GeV outputs."],
    ], 65, 325, [210, 860], 48, { fontSize: 12.2 });
  }

  {
    const s = deck.slides.add();
addHeader(s, "Physics constraint", "Common on-shell neutron reconstruction", 4);
    addFlow(s, [
      ["ECAL + HCAL hits", "positions and deposited energies"],
      ["Feature builder", "fixed-length detector-only scalar vector"],
      ["Model heads", "energy head plus direction heads"],
      ["Direction unit vector", "u_hat = v_hat / ||v_hat||"],
      ["On-shell projection", "E_hat = K_hat + m_n; |p_hat| = sqrt(K_hat(K_hat+2m_n))"],
      ["Four-vector", "(E_hat, px_hat, py_hat, pz_hat)"],
    ], 35, 170, 1210, 126);
    addTable(s, [
      ["Constraint", "Expression"],
      ["Neutron mass", "m_n = 0.93956542052 GeV"],
      ["Momentum", "p_hat = |p_hat| u_hat"],
      ["Shell check", "E_hat^2 - px_hat^2 - py_hat^2 - pz_hat^2 - m_n^2 = 0 up to floating-point precision"],
    ], 115, 385, [270, 800], 53, { fontSize: 13 });
    addNote(s, "Reported numerical check", "The finalfix2 focus-test maximum mass-shell residual is 3.277e-11 GeV^2. The raw-K retrain value is 2.550e-11 GeV^2.", { left: 300, top: 600, width: 680, height: 66 }, C.greenLight);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Model families", "Trained candidates in the archived studies", 5);
    addTable(s, [
      ["ID", "Model", "Energy head", "Direction / output", "Saved status"],
      ["B0", "Visible-sum + axis baseline", "positive linear ECAL+HCAL visible signal", "analytic shower axis; on-shell", "validation and test artifacts"],
      ["B1", "Ridge constrained baseline", "regularized linear scalar-feature head", "three unit-direction components; on-shell", "validation and historical-champion artifacts"],
      ["M2", "Ridge direct four-vector diagnostic", "four direct linear outputs", "direction from predicted p; projected on shell", "diagnostic validation artifact"],
      ["M1 log", "XGBoost focus-only / full-support", "log1p(K)", "ux, uy, uz tree heads; calibrated on shell", "finalfix2 archived results"],
      ["M1 raw", "XGBoost focus-only / full-support", "K in GeV", "ux, uy, uz tree heads; calibrated on shell", "raw-kinetic-MSE Vertex result"],
      ["N1 / H1 / G1", "dual-grid network / blend / GNN", "design record only", "no trained artifact or metric in supplied folders", "not measured"],
    ], 32, 147, [90, 260, 270, 360, 230], 63, { fontSize: 11.2 });
  }

  {
    const s = deck.slides.add();
addHeader(s, "XGBoost variants", "Measured M1 target and support variants", 6);
    addTable(s, [
      ["Variant", "Energy target used by XGBoost", "Training rows", "Support weighting", "Direction target"],
      ["M1 log focus-only", "log1p(K)", "50-250 GeV focus only", "focus bins balanced", "ux, uy, uz"],
      ["M1 log full-support", "log1p(K)", "0-300 GeV", "shoulder events weighted 0.25", "ux, uy, uz"],
      ["M1 raw focus-only", "K [GeV]", "50-250 GeV focus only", "focus bins balanced", "ux, uy, uz"],
      ["M1 raw full-support", "K [GeV]", "0-300 GeV", "shoulder events weighted 0.25", "ux, uy, uz"],
    ], 65, 155, [255, 275, 240, 250, 180], 59, { fontSize: 12 });
    addNote(s, "Squared-error training", "Each XGBoost head uses reg:squarederror. The log-target energy loss is squared error in log1p(K); the raw-target energy loss is squared error in K [GeV].", { left: 90, top: 505, width: 520, height: 96 }, C.blueLight);
    addNote(s, "Shared postprocessing", "Both target choices normalize the direction and rebuild an on-shell four-vector. Locked-test component metrics are evaluated after this reconstruction and energy calibration.", { left: 670, top: 505, width: 520, height: 96 }, C.orangeLight);
  }

  {
    const s = deck.slides.add();
addHeader(s, "Model operation", "Four scalar heads before physics reconstruction", 7);
    addFlow(s, [
      ["x", "195 engineered hit features"],
      ["f_E(x)", "energy head: log1p(K) or K"],
      ["f_x/y/z(x)", "three direction-component heads"],
      ["K_hat, v_hat", "decode energy; stack direction components"],
      ["u_hat", "normalize direction vector"],
      ["p_hat^mu", "rebuild (E, px, py, pz) on shell"],
    ], 42, 180, 1195, 126);
    addTable(s, [
      ["Stage", "Formula"],
      ["log target decode", "K_hat = max(expm1(f_E(x)), 0)"],
      ["raw target decode", "K_hat = max(f_E(x), 0)"],
      ["direction", "u_hat = v_hat / ||v_hat||"],
      ["energy and momentum", "E_hat = K_hat + m_n; p_hat = sqrt(K_hat(K_hat + 2m_n)) u_hat"],
    ], 150, 390, [330, 720], 49, { fontSize: 13 });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Log-target candidates", "Validation macro RMS relative four-vector error", 8, "Same 50-250 GeV validation focus events; archived finalfix2 candidate table.");
    addChart(s, "bar", {
      position: { left: 70, top: 160, width: 720, height: 420 },
      categories: logCandidates.map((r) => r.label),
      series: [{ name: "Macro RMS", values: logCandidates.map((r) => r.value), fill: C.blue }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 44 },
      yAxis: { title: "macro RMS relative four-vector error", min: 0, max: 0.5, majorUnit: 0.1, majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      xAxis: { textStyle: { fontSize: 11, fill: C.body }, line: { style: "solid", fill: C.rule, width: 1 }, majorGridlines: null },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 10, fill: C.body } },
    });
    addTable(s, [
      ["Candidate", "Energy rel. RMSE", "Energy MAE [GeV]"],
      ...data.log_validation.map((r) => [r.model_id, Number(r.energy_relative_rmse).toFixed(4), Number(r.energy_mae_gev).toFixed(2)]),
    ], 810, 180, [175, 135, 135], 48, { fontSize: 10.8, align: ["left", "right", "right"] });
    addText(s, "M2 is a direct-four-vector diagnostic and is marked non-deployable in the archived validation table.", { left: 820, top: 510, width: 390, height: 42 }, { fontSize: 12.5, color: C.muted });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Direct-K candidates", "Validation macro RMS relative four-vector error", 9, "Same 50-250 GeV validation focus events; raw-kinetic-MSE Vertex candidate table.");
    addChart(s, "bar", {
      position: { left: 70, top: 160, width: 720, height: 420 },
      categories: rawCandidates.map((r) => r.label),
      series: [{ name: "Macro RMS", values: rawCandidates.map((r) => r.value), fill: C.orange }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 44 },
      yAxis: { title: "macro RMS relative four-vector error", min: 0, max: 0.5, majorUnit: 0.1, majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      xAxis: { textStyle: { fontSize: 11, fill: C.body }, line: { style: "solid", fill: C.rule, width: 1 }, majorGridlines: null },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 10, fill: C.body } },
    });
    addTable(s, [
      ["Candidate", "Energy rel. RMSE", "Energy MAE [GeV]"],
      ...data.raw_validation.map((r) => [r.model_id, Number(r.energy_relative_rmse).toFixed(4), Number(r.energy_mae_gev).toFixed(2)]),
    ], 810, 180, [175, 135, 135], 48, { fontSize: 10.8, align: ["left", "right", "right"] });
    addText(s, "The raw-target XGBoost model file is stored as kinetic_energy.json; the log-target model file is stored as log1p_kinetic.json.", { left: 820, top: 510, width: 390, height: 42 }, { fontSize: 12.5, color: C.muted });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Vertex run history", "Saved focus-test metrics across base, finalfix, and finalfix2 runs", 10);
    imageJobs.push(addImage(s, assets.previousRuns, { left: 45, top: 150, width: 620, height: 420 }, "Archived Vertex run comparison chart"));
    addTable(s, [
      ["Run", "Champion", "Macro RMS", "E MAE GeV", "Angular 68 mrad"],
      ...data.run_history.map((r) => [r.label, r.champion, Number(r.macro_rms_relative_fourvector_error).toFixed(4), Number(r.energy_mae_gev).toFixed(2), Number(r.angular_68_mrad).toFixed(2)]),
    ], 700, 190, [120, 135, 85, 95, 115], 55, { fontSize: 10.2, align: ["left", "left", "right", "right", "right"] });
    addNote(s, "Run labels", "base full-cpu and finalfix selected B1 ridge constrained. finalfix2 selected M1 XGBoost focus-only. All values are archived locked focus-test metrics.", { left: 720, top: 490, width: 450, height: 88 }, C.blueLight);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Accepted log-target response", "Finalfix2 predicted-versus-true component densities", 11);
    imageJobs.push(addImage(s, assets.pred, { left: 65, top: 145, width: 1135, height: 495 }, "Four panels of component predicted versus true density"));
    addText(s, "Final calibrated physical components on the locked focus test. The red line is the identity reference in each panel.", { left: 120, top: 645, width: 1020, height: 20 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Accepted log-target residuals", "Energy and longitudinal residuals occupy wider GeV ranges", 12);
    imageJobs.push(addImage(s, assets.residual, { left: 55, top: 145, width: 680, height: 410 }, "Four component residual distributions"));
    addTable(s, [
      ["Component", "MAE [GeV]", "RMSE [GeV]", "R2", "p95 abs. error [GeV]"],
      ["E", "11.48", "20.06", "0.879", "42.86"],
      ["px", "2.37", "5.06", "0.968", "9.85"],
      ["py", "2.38", "5.06", "0.967", "10.11"],
      ["pz", "10.89", "18.81", "0.887", "40.24"],
    ], 715, 185, [125, 95, 95, 65, 130], 48, { fontSize: 10.6, align: ["left", "right", "right", "right", "right"] });
    addNote(s, "Definition", "These are final calibrated physical GeV residuals: component prediction minus component truth. No log-energy values are used in this table.", { left: 730, top: 475, width: 450, height: 88 }, C.blueLight);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Slice diagnostics", "Focus-bin energy and component behavior", 13);
    imageJobs.push(addImage(s, assets.energySlices, { left: 55, top: 150, width: 560, height: 370 }, "Energy bias and resolution versus true energy"));
    imageJobs.push(addImage(s, assets.componentSlices, { left: 665, top: 150, width: 560, height: 370 }, "Component bias and resolution versus true energy"));
    addText(s, "Focus-bin edges: 50, 75, 100, 125, 150, 175, 200, 225, 250 GeV. Macro scoring averages the bin-level RMS values.", { left: 100, top: 555, width: 1080, height: 22 }, { fontSize: 13, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Direction and shell QA", "Angular residuals and mass-shell closure are separate checks", 14);
    imageJobs.push(addImage(s, assets.angular, { left: 55, top: 150, width: 555, height: 365 }, "Angular residual distribution and energy slices"));
    imageJobs.push(addImage(s, assets.shell, { left: 690, top: 150, width: 500, height: 365 }, "Mass shell residual histogram"));
    addMetric(s, "5.87 mrad", "accepted median angular error", { left: 125, top: 555, width: 190, height: 86 }, C.green);
    addMetric(s, "16.62 mrad", "accepted angular 95%", { left: 370, top: 555, width: 190, height: 86 }, C.orange);
    addMetric(s, "3.28e-11", "accepted max shell residual, GeV^2", { left: 785, top: 555, width: 210, height: 86 }, C.green);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Boosting history", "Boosting loss versus rounds", 15, "Overall relative four-vector RMS diagnostic from the archived Vertex loss-curve job.");
    imageJobs.push(addImage(s, assets.lossOverall, { left: 45, top: 150, width: 620, height: 430 }, "Overall train and validation boosting loss"));
    addTable(s, [
      ["Quantity", "Best validation round", "Validation RMSE", "Train RMSE at that round"],
      ["overall relative four-vector", "735", "0.2143", "0.1908"],
      ["E [GeV]", "980", "20.408", "17.719"],
      ["px [GeV]", "2499", "5.178", "5.987"],
      ["py [GeV]", "2499", "5.208", "5.837"],
      ["pz [GeV]", "980", "19.136", "16.595"],
    ], 705, 180, [175, 125, 100, 120], 49, { fontSize: 10.4, align: ["left", "right", "right", "right"] });
    addText(s, "The overall curve is a physics-space diagnostic. It is distinct from the native XGBoost head target RMSE.", { left: 715, top: 500, width: 460, height: 50 }, { fontSize: 12.5, color: C.muted });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Boosting history", "Component and native-head learning curves", 16);
    imageJobs.push(addImage(s, assets.lossComponents, { left: 45, top: 145, width: 570, height: 420 }, "Physics-space component train validation loss curves"));
    imageJobs.push(addImage(s, assets.lossNative, { left: 665, top: 145, width: 570, height: 420 }, "Native XGBoost head target loss curves"));
    addText(s, "Left: final physical-component RMSE in GeV. Right: native head RMSE for log1p(K), ux, uy, and uz. The axes therefore have different units and are not directly interchangeable.", { left: 90, top: 600, width: 1100, height: 28 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Feature diagnostics", "Saved feature-gain and error-association views", 17);
    imageJobs.push(addImage(s, assets.importance, { left: 45, top: 145, width: 550, height: 300 }, "XGBoost feature importance by mean gain"));
    imageJobs.push(addImage(s, assets.errorCorrelations, { left: 680, top: 145, width: 500, height: 300 }, "Feature correlations with test focus error"));
    imageJobs.push(addImage(s, assets.tailFeatures, { left: 355, top: 475, width: 570, height: 160 }, "Feature contrast between tail and rest"));
    addText(s, "The gain chart is an XGBoost split-usage summary. Correlations and tail contrasts are descriptive associations computed on the test focus population.", { left: 115, top: 642, width: 1040, height: 20 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Target comparison", "Direct-K and log-target final physical RMSE", 18, "Both rows use the same calibrated locked focus-test event IDs. Values are GeV, not training-space target units.");
    addChart(s, "bar", {
      position: { left: 60, top: 160, width: 540, height: 410 },
      categories: componentKeys,
      series: [
        { name: "log1p(K) target", values: componentRMSELog, fill: C.blue },
        { name: "direct K target", values: componentRMSERaw, fill: C.orange },
      ],
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 50 },
      yAxis: { title: "RMSE [GeV]", min: 0, max: 24, majorUnit: 4, majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 10, fill: C.body } },
    });
    addChart(s, "bar", {
      position: { left: 680, top: 160, width: 540, height: 410 },
      categories: componentKeys,
      series: [
        { name: "log1p(K) target", values: componentKeys.map((k) => data.components[k].accepted.mse), fill: C.blue },
        { name: "direct K target", values: componentKeys.map((k) => data.components[k].raw.mse), fill: C.orange },
      ],
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 50 },
      yAxis: { title: "MSE [GeV^2]", min: 0, max: 450, majorUnit: 75, majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      dataLabels: { showValue: false },
    });
    addText(s, "Component values: E RMSE 20.059 / 19.926, px 5.062 / 5.026, py 5.059 / 5.024, pz 18.811 / 18.690 GeV for log / direct-K respectively.", { left: 105, top: 610, width: 1070, height: 24 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Target comparison", "Normalized component metrics and tolerance fractions", 19, "Normalization is residual divided by true total energy, avoiding a singular px/py component denominator near zero.");
    addChart(s, "bar", {
      position: { left: 60, top: 165, width: 540, height: 400 },
      categories: componentKeys,
      series: [
        { name: "log1p(K) target", values: componentNRMSELog, fill: C.blue },
        { name: "direct K target", values: componentNRMSERaw, fill: C.orange },
      ],
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 50 },
      yAxis: { title: "normalized RMSE", min: 0, max: 0.19, majorUnit: 0.03, numberFormatCode: "0.00", majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 10, fill: C.body } },
    });
    addChart(s, "bar", {
      position: { left: 680, top: 165, width: 540, height: 400 },
      categories: componentKeys,
      series: [
        { name: "log1p(K) target", values: componentP10Log, fill: C.blue },
        { name: "direct K target", values: componentP10Raw, fill: C.orange },
      ],
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 50 },
      yAxis: { title: "fraction within 10% of E_true", min: 0, max: 1, majorUnit: 0.2, numberFormatCode: "0%", majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 10, fill: C.body } },
    });
    addText(s, "R2 values are also recorded: log/direct E 0.8789/0.8805, px 0.9676/0.9681, py 0.9671/0.9676, pz 0.8872/0.8887.", { left: 105, top: 610, width: 1070, height: 22 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Energy response comparison", "Binned energy response and relative RMSE", 20);
    const bins = data.energy_bins.accepted.map((r) => r.label);
    addChart(s, "line", {
      position: { left: 60, top: 165, width: 545, height: 395 },
      categories: bins,
      series: [
        { name: "log1p(K) target", values: data.energy_bins.accepted.map((r) => r.mean_response), line: { style: "solid", fill: C.blue, width: 3 }, marker: { symbol: "circle", size: 6 } },
        { name: "direct K target", values: data.energy_bins.raw.map((r) => r.mean_response), line: { style: "solid", fill: C.orange, width: 3 }, marker: { symbol: "square", size: 6 } },
      ],
      yAxis: { title: "mean E_hat / E_true", min: 0.9, max: 1.2, majorUnit: 0.05, numberFormatCode: "0.00", majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      lineOptions: { grouping: "standard" },
    });
    addChart(s, "line", {
      position: { left: 680, top: 165, width: 545, height: 395 },
      categories: bins,
      series: [
        { name: "log1p(K) target", values: data.energy_bins.accepted.map((r) => r.relative_rmse), line: { style: "solid", fill: C.blue, width: 3 }, marker: { symbol: "circle", size: 6 } },
        { name: "direct K target", values: data.energy_bins.raw.map((r) => r.relative_rmse), line: { style: "solid", fill: C.orange, width: 3 }, marker: { symbol: "square", size: 6 } },
      ],
      yAxis: { title: "relative energy RMSE", min: 0.08, max: 0.36, majorUnit: 0.04, numberFormatCode: "0.00", majorGridlines: { style: "solid", fill: "#E5E9ED", width: 1 }, textStyle: { fontSize: 11, fill: C.body } },
      lineOptions: { grouping: "standard" },
    });
    addText(s, "Eight 25-GeV focus bins. Both curves are built from final calibrated test predictions on the same event IDs.", { left: 110, top: 610, width: 1060, height: 22 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Target comparison", "Exact locked focus-test component metrics", 21, "Physical GeV quantities after calibration and on-shell reconstruction; n = 50,685 for both rows.");
    addTable(s, [
      ["Component", "Target", "MSE GeV^2", "RMSE GeV", "MAE GeV", "Norm. RMSE", "R2", "within 10% E_true"],
      ["E", "log1p(K)", "402.369", "20.059", "11.480", "0.15435", "0.8789", "75.127%"],
      ["E", "direct K", "397.044", "19.926", "11.419", "0.16470", "0.8805", "75.997%"],
      ["px", "log1p(K)", "25.619", "5.062", "2.370", "0.03891", "0.9676", "96.881%"],
      ["px", "direct K", "25.263", "5.026", "2.383", "0.04168", "0.9681", "96.747%"],
      ["py", "log1p(K)", "25.597", "5.059", "2.375", "0.03911", "0.9671", "96.685%"],
      ["py", "direct K", "25.242", "5.024", "2.388", "0.04214", "0.9676", "96.514%"],
      ["pz", "log1p(K)", "353.842", "18.811", "10.891", "0.14468", "0.8872", "76.220%"],
      ["pz", "direct K", "349.318", "18.690", "10.826", "0.15418", "0.8887", "77.023%"],
    ], 36, 145, [110, 130, 140, 130, 120, 130, 90, 160], 46, { fontSize: 11.2, align: ["left", "left", "right", "right", "right", "right", "right", "right"] });
    addText(s, "The direct-K row is trained with squared error in kinetic energy. The log-target row is trained with squared error in log1p(K), but all values above use reconstructed total energy and momentum in GeV.", { left: 105, top: 600, width: 1070, height: 32 }, { fontSize: 12.5, color: C.muted, alignment: "center" });
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Scope comparison", "Pencil-beam and all-neutron scopes", 22);
    imageJobs.push(addImage(s, assets.pencil, { left: 45, top: 165, width: 550, height: 390 }, "Pencil-beam and all-neutron energy comparison chart"));
    addTable(s, [
      ["Dataset/model", "Scope", "Energy MAE [GeV]", "Energy RMSE [GeV]", "Energy R2"],
      ["Pencil beam", "100k neutrons, 50-250 GeV, energy-only", "4.425", "7.365", "0.9838"],
      ["All neutron", "765k broad-angle neutrons, focus 50-250 GeV, E+px+py+pz", "11.480", "20.059", "0.8789"],
    ], 640, 195, [115, 170, 90, 90, 75], 62, { fontSize: 10.4, align: ["left", "left", "right", "right", "right"] });
    addNote(s, "Task boundary", "The pencil-beam comparison is retained as an energy-only reference. It does not provide px, py, pz, angular, or four-vector metrics and is not merged into the all-neutron model ranking.", { left: 680, top: 445, width: 450, height: 105 }, C.blueLight);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Calibration and coverage", "Locked-test interval coverage", 23);
    addTable(s, [
      ["Model", "Nominal", "Validation abs-energy width [GeV]", "Focus-test coverage"],
      ["finalfix2 log target", "68%", "10.017", "68.077%"],
      ["finalfix2 log target", "90%", "27.994", "90.212%"],
      ["finalfix2 log target", "95%", "43.114", "95.056%"],
      ["direct-K retrain", "68%", "stored calibration", "68.200%"],
      ["direct-K retrain", "90%", "stored calibration", "90.038%"],
      ["direct-K retrain", "95%", "stored calibration", "95.178%"],
    ], 90, 170, [240, 140, 330, 260], 58, { fontSize: 12.5, align: ["left", "right", "right", "right"] });
    addNote(s, "Procedure", "A linear energy calibration is fitted after validation model selection. The direction is retained, kinetic energy is recomputed, and the output is projected on shell before test scoring.", { left: 120, top: 550, width: 450, height: 94 }, C.greenLight);
    addNote(s, "Coverage label", "These are empirical validation-residual intervals verified once on test. They are not presented as a separate formal split-conformal guarantee.", { left: 700, top: 550, width: 450, height: 94 }, C.orangeLight);
  }

  {
    const s = deck.slides.add();
    addHeader(s, "Record", "Artifacts, metrics, and model status in one view", 24);
    addTable(s, [
      ["Artifact class", "Location", "What it contains"],
      ["Archived finalfix2", "ML ZDC all / outputs/presentation_analysis/all_neutron_finalfix2", "candidate models, calibrated predictions, validation leaderboard, locked test metrics, plots"],
      ["Loss-curve extension", "ML ZDC all / outputs/presentation_analysis/loss_curves_vertex", "overall/component/native losses, feature-error diagnostics, slice diagnostics"],
      ["Historical Vertex runs", "ML ZDC all 1 / outputs/reports/previous_vertex_jobs", "base full-cpu, finalfix, finalfix2 job records and metrics"],
      ["Direct-K retrain", "Vertex gs://.../runs/raw-kinetic-mse-20260713-51b0ff0/outputs", "raw kinetic target models, calibration, locked test metrics, component comparison"],
      ["Design-only entries", "ML ZDC all 1 / docs/MODEL_DESIGN.md", "N1 dual-grid, H1 blend, G1 Deep Sets/GNN definitions without archived training result"],
    ], 50, 150, [220, 460, 500], 68, { fontSize: 11.5 });
    addText(s, "Presentation evidence: saved Vertex artifacts and archived diagnostic figures. No new model training is performed for this deck.", { left: 120, top: 610, width: 1040, height: 22 }, { fontSize: 13, color: C.muted, alignment: "center" });
  }

  await Promise.all(imageJobs);
  return deck;
}

async function main() {
  const data = JSON.parse(await fs.readFile(`${INPUT}/deck_data.json`, "utf8"));
  await fs.mkdir(PREVIEW, { recursive: true });
  await fs.mkdir(LAYOUT, { recursive: true });
  await fs.mkdir(QA, { recursive: true });
  await fs.mkdir(path.dirname(OUT), { recursive: true });
  const deck = await buildDeck(data);
  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(`${PREVIEW}/${stem}.png`, await deck.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(`${LAYOUT}/${stem}.layout.json`, await layout.text(), "utf8");
  }
  await writeBlob(`${QA}/deck-montage.webp`, await deck.export({ format: "webp", montage: true, scale: 1 }));
  const inspect = await deck.inspect({ kind: "slide,textbox,shape,image,table,chart,layout", maxChars: 40000 });
  await fs.writeFile(`${QA}/deck-inspect.ndjson`, inspect.ndjson, "utf8");
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
