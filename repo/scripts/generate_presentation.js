/*
 * scripts/generate_presentation.js - Batch 09 class presentation.
 * All numbers are read from outputs/tables/key_results.json and the CSV tables.
 *
 *   node scripts/generate_presentation.js
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const FIG = (f) => path.join(ROOT, "outputs", "figures", f);
const K = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "tables", "key_results.json"), "utf8"));
const APPLY_THEME = process.env.APPLY_THEME_JS;

const THEME = {
  name: "Ember",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F1F1F", lt1: "FFFFFF", dk2: "2B2A28", lt2: "F3F2F0",
    accent1: "D9531E", accent2: "2A78D6", accent3: "1BAF7A", accent4: "EDA100",
    accent5: "6B6A66", accent6: "8C3A12", hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = THEME.colors;

const f1 = (x) => Number(x).toFixed(1);
const f2 = (x) => Number(x).toFixed(2);
const f0 = (x) => Number(x).toFixed(0);

const ref = K.reference_case_1d;
const cal = K.calibration;
const st = K.nine_runs.stats;
const f5 = K.fig5;
const td = K.two_d;
const t7 = K.table7;
const csv = fs.readFileSync(path.join(ROOT, "outputs", "tables", "table3_nine_runs_validation.csv"), "utf8").trim().split("\n");
const hdrs = csv[0].split(",");
const runs = csv.slice(1).map((l) => Object.fromEntries(l.split(",").map((v, i) => [hdrs[i], Number(v)])));
const ratios = runs.map((r) => 100 * r["Flow_sim (Nm3/h dry)"] / r["Flow_meas (m3/h)"]);
const implied = runs.map((r) => r["Implied feed (kg/h)"]);
const wgsFast = K.wgs_sensitivity_calibration_case["fast_wgs_a=2.78e3"];
const SIZES = {
  "fig00_geometry.png": 0.757, "fig01_feedstock_composition.png": 3.125, "fig02_species_distributions_1d.png": 2.604,
  "fig03_temperature_profiles_1d.png": 1.257, "fig04_char_conversion_and_shrinkage.png": 2.791,
  "fig05_temperature_contours_2d.png": 1.188, "fig06_species_contours_fuel_2d.png": 1.188,
  "fig07_species_contours_oxidants_2d.png": 1.188, "fig08_table7_replication.png": 1.744,
  "fig09_validation_parity_plots.png": 1.111, "fig10_principal_cases_comparison.png": 1.554,
  "fig11_operating_sweeps.png": 1.842, "fig12_radial_profiles_2d.png": 3.214,
};

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Fixed-bed downdraft gasifier simulation - Batch 09";
  pres.author = "Batch 09";
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "Title dark",
    background: { color: HEX.dk2 },
    objects: [],
    placeholders: [],
  });
  pres.defineSlideMaster({
    title: "Content",
    background: { color: "FFFFFF" },
    objects: [
      { text: { text: "Batch 09  |  Fixed-bed downdraft gasifier  |  benchmark: Jayah et al. (2003)",
          options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent5, isTextBox: true, margin: 0 } } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 30,
          bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: "middle", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5 },
  });

  const img = (slide, file, x, y, maxW, maxH, name) => {
    const ar = SIZES[file];
    let w = maxW, h = maxW / ar;
    if (h > maxH) { h = maxH; w = maxH * ar; }
    slide.addImage({ path: FIG(file), x: x + (maxW - w) / 2, y, w, h, objectName: name || file,
      altText: file.replace(/_/g, " ").replace(".png", "") });
  };
  const body = (slide, items, opts) => {
    const arr = items.map((t, i) => {
      const runOpts = { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 };
      if (Array.isArray(t)) {
        return t.map((r, j) => ({ text: r.text, options: {
          ...(j === 0 ? { bullet: true, paraSpaceAfter: 8 } : {}), ...(r.bold ? { bold: true } : {}),
          breakLine: j === t.length - 1 ? i < items.length - 1 : false } }));
      }
      return [{ text: t, options: runOpts }];
    }).flat();
    slide.addText(arr, { fontSize: 16, color: C.text1, valign: "top", isTextBox: true, margin: 0.05, ...opts });
  };
  const stat = (slide, x, y, w, big, label, color, name) => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.55, rectRadius: 0.08, fill: { color: "F3F2F0" },
      line: { color: "F3F2F0" }, objectName: `${name}-card` });
    slide.addText(big, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.8, fontSize: 36, bold: true, color: color || C.accent1,
      fontFace: THEME.headFontFace, margin: 0, isTextBox: true, objectName: `${name}-value` });
    slide.addText(label, { x: x + 0.2, y: y + 0.9, w: w - 0.4, h: 0.55, fontSize: 12, color: C.text1, margin: 0,
      valign: "top", isTextBox: true, objectName: `${name}-label` });
  };
  const content = (section, title) => {
    const s = pres.addSlide({ masterName: "Content", sectionTitle: section });
    s.addText(title, { placeholder: "title" });
    return s;
  };

  // ---------------------------------------------------------------- 1 title
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Introduction" });
  s.addText("Simulating a fixed-bed downdraft wood gasifier", { x: 0.8, y: 1.9, w: 11.7, h: 1.4, fontSize: 40, bold: true,
    color: C.background1, fontFace: THEME.headFontFace, isTextBox: true, margin: 0, objectName: "title" });
  s.addText("1D kinetic model, 2D axisymmetric extension and validation against Jayah et al. (2003), Biomass and Bioenergy 25, 459-469",
    { x: 0.8, y: 3.35, w: 11, h: 0.9, fontSize: 18, color: "D9D8D4", isTextBox: true, margin: 0, objectName: "subtitle" });
  s.addText("Gasification & Reforming Processes  |  Batch 09  |  October 2026",
    { x: 0.8, y: 5.6, w: 11, h: 0.4, fontSize: 14, color: C.accent1, isTextBox: true, margin: 0, objectName: "meta" });
  s.addNotes("Introduce the assignment: fixed-bed gasifier topic, simulation in Python, validated against Jayah et al. 2003, the NERD 80 kW tea-drying gasifier in Sri Lanka.");

  // ---------------------------------------------------------------- 2 summary
  s = content("Introduction", "What we found");
  stat(s, 0.6, 1.5, 2.9, `${f2(cal.MAE_percent)}`, `%-pt MAE on the calibration run (Jayah's model: ${f2(cal.Jayah_MAE_percent)})`, C.accent1, "s1");
  stat(s, 3.7, 1.5, 2.9, `${f2(st.CO.MAE)} / ${f2(st.H2.MAE)}`, "%-pt MAE for CO / H2 over the nine independent runs", C.accent2, "s2");
  stat(s, 6.8, 1.5, 2.9, `${f0(f5.MAE_K)} K`, `axial temperature MAE vs six thermocouples (Jayah's model: ${f0(f5.Jayah_MAE_K)} K)`, C.accent3, "s3");
  stat(s, 9.9, 1.5, 2.85, `${f0(t7.chip_size_cm[1].optimum_length_cm)} cm`, "optimum hearth length with the measured 12.8 % heat loss (Jayah: 32-33 cm)", C.accent6, "s4");
  body(s, [
    "Mean gas composition and heating value are reproduced; run-to-run differences are not (R² about the 1:1 line ≤ 0)",
    "The model agrees with Jayah on the direction of every parametric effect and on heat loss being decisive",
    "It disagrees on the remedy: insulating the hearth helps far more than lengthening it to 33 cm",
  ], { x: 0.6, y: 3.6, w: 12.1, h: 3.0, fontSize: 20 });
  s.addNotes("Headline numbers. The first is a calibration target so it is not independent; the nine runs and thermocouples are independent. Be upfront that R-squared is negative: the measured spread between runs is about 1-2 percentage points, similar to the model error.");

  // ---------------------------------------------------------------- 3 reactor
  pres.addSection({ title: "Setup" });
  s = content("Setup", "The NERD gasifier and the paper's data");
  img(s, "fig00_geometry.png", 0.6, 1.35, 3.4, 5.5, "geometry");
  body(s, [
    [{ text: "Reactor: ", bold: true }, { text: "80 kWth, throat Ø100 mm, 12 air nozzles, 220 mm conical reduction zone (61° wall), no insulation" }],
    [{ text: "Fuel: ", bold: true }, { text: "rubber wood, 3.3 / 4.4 / 5.5 cm chips, 12.5-18.5 % moisture (d.b.)" }],
    [{ text: "Air-fuel ratio: ", bold: true }, { text: `1.86-2.37 kg/kg, i.e. equivalence ratio 0.30-0.38 (stoichiometric air ${f2(K.feedstock_derived.afr_stoich)} kg/kg)` }],
    [{ text: "Validation data: ", bold: true }, { text: "Table 3 (nine gas analyses), Table 5 (calibration run), Fig. 5 (six axial temperatures), Table 7 (parametric study)" }],
    [{ text: "Not reported, so assumed: ", bold: true }, { text: "feed rate per run (18.6 kg/h from Table 4), bed voidage 0.48, char density 250 kg/m³" }],
  ], { x: 4.4, y: 1.45, w: 8.3, h: 5.3 });
  s.addNotes("Everything in bold-face comes from the paper; the last line lists what we had to assume because the paper does not give it.");

  // ---------------------------------------------------------------- 4 feedstock
  s = content("Setup", "Feedstock: rubber wood");
  img(s, "fig01_feedstock_composition.png", 0.6, 1.4, 12.1, 3.9, "feedstock");
  body(s, [
    `Fixed carbon (19.2 %) becomes the char that is gasified in the reduction zone; the volatiles (80.1 %) burn with the air above the throat`,
    `Dry LHV ${f2(K.feedstock_derived.lhv)} MJ/kg and formula ${K.feedstock_derived.formula} are calculated from the paper's analyses`,
  ], { x: 0.6, y: 5.4, w: 12.1, h: 1.4 });
  s.addNotes("Tables 1 and 2 of the paper. The right-hand table marks which properties are measured, calculated or assumed.");

  // ---------------------------------------------------------------- 5 model
  pres.addSection({ title: "Model" });
  s = content("Model", "Model structure: three linked parts");
  const boxes = [
    ["Throat sub-model", `Volatiles + air -> CO, CO2, H2, H2O, N2 (WGS equilibrium, CH4 fixed at 1.2 %). Temperature from an enthalpy balance, anchored to Jayah's ${f0(K.parameters.throat_t_anchor_k)} K`],
    ["1D reduction zone", "Species, char, gas and char temperatures, particle shrinkage. Boudouard, water-gas, methanation, WGS. Wall loss U·P·(Tg - T∞). Stiff Radau solver"],
    ["2D axisymmetric", "12 annular cells following the cone; each runs the 1D physics; radial dispersion of heat and species; wall loss only at the outer cell"],
  ];
  boxes.forEach(([h, t], i) => {
    const x = 0.6 + i * 4.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 3.8, h: 2.7, rectRadius: 0.08, fill: { color: "F3F2F0" },
      line: { color: "F3F2F0" }, objectName: `box${i}` });
    s.addText(String(i + 1), { x: x + 0.25, y: 1.7, w: 0.55, h: 0.55, shape: pres.shapes.OVAL, fill: { color: HEX.accent1 },
      color: C.background1, bold: true, fontSize: 16, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `num${i}` });
    s.addText(h, { x: x + 0.95, y: 1.7, w: 2.7, h: 0.55, fontSize: 18, bold: true, color: C.text2, valign: "middle", margin: 0,
      isTextBox: true, objectName: `boxtitle${i}` });
    s.addText(t, { x: x + 0.25, y: 2.4, w: 3.35, h: 1.7, fontSize: 13, color: C.text1, valign: "top", margin: 0, isTextBox: true,
      objectName: `boxtext${i}` });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 3.82, y: 2.7, w: 0.31, h: 0.3, fill: { color: HEX.accent5 },
      line: { color: HEX.accent5 }, objectName: `arrow${i}` });
  });
  s.addText("Calibrated (3 parameters, never on validation data)", { x: 0.6, y: 4.5, w: 12.1, h: 0.45, fontSize: 18, bold: true,
    color: C.text2, margin: 0, isTextBox: true, objectName: "calhead" });
  body(s, [
    `Wall coefficient U = ${f1(K.parameters.u_wall_w_m2_k)} W/m²K: gives the 12.8 % heat loss Jayah measured`,
    `Char-reactivity factors η(Boudouard) = ${f2(K.parameters.eta_boudouard)}, η(water-gas) = ${f2(K.parameters.eta_water_gas)}: fitted to the CO, H2 and CO2 of Table 5`,
  ], { x: 0.6, y: 5.0, w: 12.1, h: 1.6 });
  s.addNotes("Key viva point: the mixed adiabatic throat temperature is about 1345 K, lower than Jayah's 1604 K, so we keep Jayah's level and take only the change with AFR, moisture and air temperature from the energy balance. Water-gas shift units are ambiguous in the literature; the fast reading gives a far worse gas.");

  // ---------------------------------------------------------------- 6 calibration chart
  pres.addSection({ title: "Results" });
  s = content("Results", "Calibration run: matches as well as Jayah's own model");
  const sp = ["CO", "H2", "CO2"];
  const rows = cal.rows.filter((r) => sp.includes(r.Species));
  s.addChart(pres.charts.BAR, [
    { name: "Measured", labels: sp, values: rows.map((r) => r["Measured (%)"]) },
    { name: "Jayah model", labels: sp, values: rows.map((r) => r["Jayah model (%)"]) },
    { name: "This model", labels: sp, values: rows.map((r) => r["This model (%)"]) },
  ], {
    x: 0.6, y: 1.4, w: 7.2, h: 5.3, barDir: "col", barGapWidthPct: 60, chartColors: ["6B6A66", HEX.accent2, HEX.accent1],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelFormatCode: "0.0", dataLabelFontFace: "+mn-lt",
    showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt",
    valAxisTitle: "Dry mole fraction (%)", showValAxisTitle: true, valAxisTitleFontSize: 12, valAxisTitleFontFace: "+mn-lt",
    catAxisLabelFontSize: 13, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
    catAxisLabelColor: "52514E", valAxisLabelColor: "52514E", valGridLine: { color: "E3E2DE", size: 0.75 }, catGridLine: { style: "none" },
    valAxisMinVal: 0, valAxisMaxVal: 25, objectName: "calibration-chart",
  });
  body(s, [
    `MAE ${f2(cal.MAE_percent)} %-pts (Jayah's model ${f2(cal.Jayah_MAE_percent)})`,
    "Table 5 = Run 7 (AFR 1.86, 14.7 % moisture) with 2.5 cm chips, as the paper states",
    "This is a calibration target, so the fit is not evidence by itself; the next slides use independent data",
  ], { x: 8.2, y: 1.6, w: 4.5, h: 5.0 });
  s.addNotes("Explain the Table 5 / Run 7 chip-size inconsistency in the paper if asked.");

  // ---------------------------------------------------------------- 7 species
  s = content("Results", "Axial species: conversion happens in the first 10 cm");
  img(s, "fig02_species_distributions_1d.png", 0.6, 1.4, 12.1, 4.65, "species");
  body(s, [
    `CO ${f1(ref.throat_dry.CO)} -> ${f1(ref.exit_dry.CO)} %, H2 ${f1(ref.throat_dry.H2)} -> ${f1(ref.exit_dry.H2)} %, CO2 ${f1(ref.throat_dry.CO2)} -> ${f1(ref.exit_dry.CO2)} %, steam ${f1(ref.h2o_wet_in)} -> ${f1(ref.h2o_wet_out)} % (wet); then the bed is too cold and the gas freezes`,
  ], { x: 0.6, y: 6.15, w: 12.1, h: 0.75, fontSize: 15 });
  s.addNotes("Reference case: Fig. 5 conditions, AFR 2.20, 2.5 cm chips.");

  // ---------------------------------------------------------------- 8 temperature
  s = content("Results", "Temperature: closer to the thermocouples than Jayah's model");
  img(s, "fig03_temperature_profiles_1d.png", 0.6, 1.35, 6.9, 5.5, "temperature");
  stat(s, 8.0, 1.5, 4.7, `${f0(f5.MAE_K)} K vs ${f0(f5.Jayah_MAE_K)} K`, "MAE of this model vs Jayah's model at the six measured points (not fitted)", C.accent3, "t1");
  body(s, [
    `Gas enters at ${f0(ref.T_throat_K)} K, char at ${f0(ref.T_s0_K)} K; the phases equilibrate by ${f1(ref.z_dTgs_below_10K_cm)} cm`,
    `${f0(ref.wall_share_of_sensible_drop_percent)} % of the cooling is wall loss, the rest endothermic reaction`,
    "Largest errors: too hot at 4 cm, too cold at 16-20 cm",
  ], { x: 8.0, y: 3.3, w: 4.7, h: 3.4, fontSize: 15 });
  s.addNotes("Both measured points and Jayah's model curve were digitised from the paper's Fig. 5 (six points, not seven as in our earlier draft).");

  // ---------------------------------------------------------------- 9 2D temperature
  s = content("Results", "2D: a hot core and a cold wall layer");
  img(s, "fig05_temperature_contours_2d.png", 0.6, 1.35, 6.5, 5.5, "contours-T");
  body(s, [
    `Exit: ${f0(td.stations.z22.T_axis)} K on the axis, ${f0(td.stations.z22.T_wall_cell)} K in the wall cell`,
    `Core char is ${f1(td.stations.z11.Xc_axis)} % converted by 11 cm; near the wall only ${f0(td.stations.z22.Xc_wall_cell)} %`,
    "Radial dispersion includes radiation through the bed, which dominates at these temperatures",
    "It is a reduced-order dispersion model: no velocity profile, channelling or nozzle jets; not CFD",
  ], { x: 7.5, y: 1.5, w: 5.2, h: 5.2, fontSize: 15 });
  s.addNotes("Each radial cell runs the same physics as the 1D model; with very strong mixing the 2D model collapses to the 1D result (a unit test checks this).");

  // ---------------------------------------------------------------- 10 2D species
  s = content("Results", "2D species: richest gas in the core");
  img(s, "fig06_species_contours_fuel_2d.png", 0.6, 1.35, 5.3, 4.5, "contours-CO");
  img(s, "fig12_radial_profiles_2d.png", 6.2, 1.6, 6.5, 2.1, "radial");
  body(s, [
    `Exit CO ${f1(td.stations.z22.CO_axis)} % on the axis vs ${f1(td.stations.z22.CO_wall_cell)} % at the wall; H2 ${f1(td.stations.z22.H2_axis)} vs ${f1(td.stations.z22.H2_wall_cell)} %`,
    "Once core char is used up, the CO peak moves just off the axis where char is still reacting",
    `Flow-weighted 2D exit: CO ${f1(td.mixed_exit_dry.CO)}, H2 ${f1(td.mixed_exit_dry.H2)}, CO2 ${f1(td.mixed_exit_dry.CO2)} %`,
  ], { x: 6.2, y: 4.0, w: 6.5, h: 2.8, fontSize: 15 });
  s.addNotes("CO2 and H2O contours are in the report (Fig. 8 there).");

  // ---------------------------------------------------------------- 11 nine runs
  pres.addSection({ title: "Validation" });
  s = content("Validation", "Nine independent runs: right level, not the trends");
  img(s, "fig09_validation_parity_plots.png", 0.6, 1.3, 6.0, 5.55, "parity");
  const hdr = ["", "MAE", "Bias", "Meas. std", "R²"].map((t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: HEX.dk2 } } }));
  const trow = (lab, k) => [lab, f2(st[k].MAE), (st[k].bias >= 0 ? "+" : "") + f2(st[k].bias), f2(st[k].measured_std), f2(st[k].R2_vs_1to1)];
  s.addTable([hdr, trow("CO", "CO"), trow("H2", "H2"), trow("CO2", "CO2"), trow("N2", "N2"), trow("LHV", "LHV")],
    { x: 7.0, y: 1.5, w: 5.7, colW: [1.1, 1.1, 1.1, 1.3, 1.1], fontSize: 13, color: "1F1F1F", border: { type: "solid", color: "D9D8D4", pt: 0.75 },
      rowH: 0.36, objectName: "stats-table" });
  body(s, [
    "Errors in %-points (LHV in MJ/Nm³); all statistics computed in code",
    "H2 is too low in Runs 1-4; N2 too high, i.e. less gas per unit air",
    "R² < 0 because the measured spread (1-2 %-pts) is about the size of the error, and the model's CO-vs-AFR trend is not in the data",
  ], { x: 7.0, y: 4.0, w: 5.7, h: 2.8, fontSize: 14 });
  s.addNotes("Our earlier draft quoted R-squared of 0.81 etc.; those were typed constants. These are computed.");

  // ---------------------------------------------------------------- 12 flow
  s = content("Validation", "Heating value fits; gas flow cannot be tested properly");
  img(s, "fig10_principal_cases_comparison.png", 0.6, 1.3, 7.8, 5.55, "lhv-flow");
  body(s, [
    `LHV within ${f2(st.LHV.MAE)} MJ/Nm³ on average`,
    `Simulated dry flow is ${f0(Math.min(...ratios))}-${f0(Math.max(...ratios))} % of the measured flow`,
    "The paper gives no per-run feed rate and does not say whether the measured flow is wet, dry or at what temperature",
    `Matching the flow would need ${f1(Math.min(...implied))}-${f1(Math.max(...implied))} kg/h of dry wood instead of the assumed 18.6 kg/h`,
  ], { x: 8.7, y: 1.5, w: 4.0, h: 5.3, fontSize: 15 });
  s.addNotes("Composition and LHV are intensive, so they barely depend on the feed-rate assumption (see feed sweep in the report).");

  // ---------------------------------------------------------------- 13 parametric
  pres.addSection({ title: "Design" });
  s = content("Design", "Parametric study: same directions, different optimum");
  img(s, "fig08_table7_replication.png", 0.6, 1.3, 8.4, 4.82, "table7");
  body(s, [
    `Base case at 22 cm: ${f1(t7.chip_size_cm[1].eff_22cm)} % (Jayah 56.0 %)`,
    "Every effect has Jayah's sign; heat loss is the strongest lever",
    `Optimum length ${f0(t7.chip_size_cm[1].optimum_length_cm)} cm, not 32-33 cm: the bed is too cold for gasification beyond ~12 cm`,
    `At 5 % heat loss the optimum becomes ${f0(t7.heat_loss_percent_input_energy[0].optimum_length_cm)} cm and efficiency ${f1(t7.heat_loss_percent_input_energy[0].eff_22cm)} %`,
  ], { x: 9.3, y: 1.5, w: 3.4, h: 5.3, fontSize: 14 });
  s.addText("Recommendation: insulate the hearth first; the existing 22 cm is then close to optimal", { x: 0.6, y: 6.25, w: 8.4, h: 0.55,
    fontSize: 15, bold: true, color: C.accent6, margin: 0, isTextBox: true, objectName: "recommendation" });
  s.addNotes("Open markers are Jayah's Table 7 values at 22 cm. Moisture, chip size and air temperature act more strongly in our model because they act through the throat temperature and steep kinetics.");

  // ---------------------------------------------------------------- 14 limitations
  pres.addSection({ title: "Close" });
  s = content("Close", "Limitations we want to be clear about");
  const lim = [
    ["Throat temperature", `Absolute level taken from Jayah (${f0(K.parameters.throat_t_anchor_k)} K); our mixed energy balance gives ${f0(ref.T_adiabatic_mixed_K)} K`],
    ["Water-gas shift", `Rate units are ambiguous in the literature; the fast reading gives CO ${f0(wgsFast.CO)} %, H2 ${f0(wgsFast.H2)} % on the calibration run`],
    ["Calibration", `Effective U = ${f0(K.parameters.u_wall_w_m2_k)} W/m²K puts all measured loss in the hearth; calibration-run char conversion is only ${f0(cal.char_conversion_percent)} %`],
    ["Paper data gaps", "No per-run feed rate or flow basis; chip size of Run 7 inconsistent; Fig. 5 trial conditions not stated"],
    ["CH4 and tar", "CH4 imposed (as in Jayah); tar not modelled"],
    ["2D model", "Radial dispersion only, not CFD; no velocity profile or channelling"],
  ];
  lim.forEach(([h, t], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.45 + row * 1.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 1.55, rectRadius: 0.08, fill: { color: "F3F2F0" },
      line: { color: "F3F2F0" }, objectName: `lim${i}` });
    s.addText(h, { x: x + 0.25, y: y + 0.15, w: 5.45, h: 0.4, fontSize: 16, bold: true, color: C.accent1, margin: 0, isTextBox: true,
      objectName: `limh${i}` });
    s.addText(t, { x: x + 0.25, y: y + 0.6, w: 5.45, h: 0.85, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true,
      objectName: `limt${i}` });
  });
  s.addNotes("Raise these before the examiners do.");

  // ---------------------------------------------------------------- 15 conclusions
  s = pres.addSlide({ masterName: "Title dark", sectionTitle: "Close" });
  s.addText("Conclusions", { x: 0.8, y: 0.6, w: 11.7, h: 0.9, fontSize: 36, bold: true, color: C.background1,
    fontFace: THEME.headFontFace, isTextBox: true, margin: 0, objectName: "title" });
  const concl = [
    `Calibration run reproduced to ${f2(cal.MAE_percent)} %-pts, as well as Jayah's own model`,
    `Nine independent runs: MAE ${f2(st.CO.MAE)} (CO), ${f2(st.H2.MAE)} (H2), ${f2(st.CO2.MAE)} (CO2) %-pts; H2 biased low; trends between runs not captured`,
    `Axial temperature within ${f0(f5.MAE_K)} K of the thermocouples, better than Jayah's model (${f0(f5.Jayah_MAE_K)} K)`,
    "2D model: hot core, cold wall layer, core char exhausted by about 11 cm",
    "Design: heat loss dominates; insulating the hearth is worth more than extending it to 33 cm",
  ];
  s.addText(concl.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < concl.length - 1, paraSpaceAfter: 12 } })),
    { x: 0.8, y: 1.8, w: 11.7, h: 4.6, fontSize: 18, color: C.background1, valign: "top", isTextBox: true, margin: 0, objectName: "conclusions" });
  s.addText("Code, data and report: Python repository, run_simulation.py reproduces every number", { x: 0.8, y: 6.6, w: 11.7, h: 0.4,
    fontSize: 13, color: C.accent1, isTextBox: true, margin: 0, objectName: "repo" });
  s.addNotes("Close with the design recommendation and invite questions.");

  const out = path.join(ROOT, "presentation", "Batch_09_presentation.pptx");
  await pres.writeFile({ fileName: out });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(out, THEME);
  }
  console.log("wrote", out);
}

main().catch((e) => { console.error(e); process.exit(1); });
