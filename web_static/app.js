const removeState = {
  file: null,
  files: [],
  sourceUrl: "",
  resultUrl: "",
  resultBlob: null,
  resultFilename: "",
};

const spriteState = {
  image: null,
  imageUrl: "",
  currentFrame: 0,
  timer: 0,
  playing: false,
  alignedImage: null,
  alignedUrl: "",
  previewSheetUrl: "",
  analyses: [],
  baseFrame: 0,
};

const videoState = {
  file: null,
  videoUrl: "",
  sheetUrl: "",
  duration: 0,
  generating: false,
};

const processState = {
  file: null,
  sourceUrl: "",
  resultUrl: "",
  naturalWidth: 0,
  naturalHeight: 0,
  aspectRatio: 1,
  syncingDimensions: false,
};

const $ = (id) => document.getElementById(id);

const imageInput = $("imageInput");
const imageDropZone = $("imageDropZone");
const sourcePreview = $("sourcePreview");
const resultPreview = $("resultPreview");
const removeButton = $("removeButton");
const downloadResult = $("downloadResult");
const importRemovedToProcess = $("importRemovedToProcess");
const removeFeedback = $("removeFeedback");
const removeStatus = $("removeStatus");

const spriteInput = $("spriteInput");
const spriteDropZone = $("spriteDropZone");
const spriteCanvas = $("spriteCanvas");
const spriteContext = spriteCanvas.getContext("2d");
const sheetCanvas = $("sheetCanvas");
const sheetContext = sheetCanvas.getContext("2d");
const spriteStatus = $("spriteStatus");
const spriteFeedback = $("spriteFeedback");
const spriteMetrics = $("spriteMetrics");
const playButton = $("playButton");
const prevFrameButton = $("prevFrameButton");
const nextFrameButton = $("nextFrameButton");
const frameSlider = $("frameSlider");
const frameOutput = $("frameOutput");
const speedSlider = $("speedSlider");
const speedOutput = $("speedOutput");
const spriteViewModeInput = $("spriteViewModeInput");
const baseFrameInput = $("baseFrameInput");
const noiseAreaInput = $("noiseAreaInput");
const footBandInput = $("footBandInput");
const ignoreShadowInput = $("ignoreShadowInput");
const showDetectionInput = $("showDetectionInput");
const setBaseFrameButton = $("setBaseFrameButton");
const analyzeAlignmentButton = $("analyzeAlignmentButton");
const generateAlignedSheetButton = $("generateAlignedSheetButton");
const downloadAlignedSheet = $("downloadAlignedSheet");
const generatePreviewSheetButton = $("generatePreviewSheetButton");
const downloadPreviewSheet = $("downloadPreviewSheet");
const alignmentFeedback = $("alignmentFeedback");
const videoInput = $("videoInput");
const videoDropZone = $("videoDropZone");
const videoPreview = $("videoPreview");
const videoStatus = $("videoStatus");
const videoRangeOutput = $("videoRangeOutput");
const videoStartInput = $("videoStartInput");
const videoEndInput = $("videoEndInput");
const videoFpsInput = $("videoFpsInput");
const videoColumnsInput = $("videoColumnsInput");
const videoFrameWidthInput = $("videoFrameWidthInput");
const videoSizeValue = $("videoSizeValue");
const videoDurationValue = $("videoDurationValue");
const videoFrameCountValue = $("videoFrameCountValue");
const generateVideoFramesButton = $("generateVideoFramesButton");
const downloadVideoSheet = $("downloadVideoSheet");
const videoFeedback = $("videoFeedback");
const videoSheetCanvas = $("videoSheetCanvas");
const videoSheetContext = videoSheetCanvas.getContext("2d");
const videoFrameCanvas = $("videoFrameCanvas");
const videoFrameContext = videoFrameCanvas.getContext("2d");
const videoSheetMetrics = $("videoSheetMetrics");
const processInput = $("processInput");
const processDropZone = $("processDropZone");
const processSourcePreview = $("processSourcePreview");
const processResultPreview = $("processResultPreview");
const processStatus = $("processStatus");
const processFeedback = $("processFeedback");
const processButton = $("processButton");
const downloadProcessed = $("downloadProcessed");
const processSourceMetrics = $("processSourceMetrics");
const processOutputMetrics = $("processOutputMetrics");
const processWidthInput = $("processWidthInput");
const processHeightInput = $("processHeightInput");
const processKeepAspectInput = $("processKeepAspectInput");
const processResizeInput = $("processResizeInput");
const processCompressInput = $("processCompressInput");
const processPngModeInput = $("processPngModeInput");
const processPaletteColorsInput = $("processPaletteColorsInput");
const navLinks = Array.from(document.querySelectorAll("[data-nav-link]"));
const toolSections = navLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

const feedbackClasses = ["text-slate-500", "text-red-600", "text-emerald-700"];
const dropActiveClasses = ["border-indigo-400", "bg-white"];
const linkReadyClasses = ["cursor-pointer", "text-slate-700", "hover:bg-white"];
const linkDisabledClasses = ["cursor-not-allowed", "text-slate-400"];

function addClasses(element, classes) {
  element.classList.add(...classes);
}

function removeClasses(element, classes) {
  element.classList.remove(...classes);
}

function setFeedback(element, message, kind = "") {
  element.textContent = message;
  removeClasses(element, feedbackClasses);
  if (kind === "error") {
    addClasses(element, ["text-red-600"]);
  } else if (kind === "success") {
    addClasses(element, ["text-emerald-700"]);
  } else {
    addClasses(element, ["text-slate-500"]);
  }
}

function revokeUrl(key, state) {
  if (state[key]) {
    URL.revokeObjectURL(state[key]);
    state[key] = "";
  }
}

function disableDownloadLink(link) {
  link.removeAttribute("href");
  link.removeAttribute("download");
  removeClasses(link, linkReadyClasses);
  addClasses(link, linkDisabledClasses);
  link.setAttribute("aria-disabled", "true");
}

function enableDownloadLink(link, href, filename) {
  link.href = href;
  link.download = filename;
  removeClasses(link, linkDisabledClasses);
  addClasses(link, linkReadyClasses);
  link.setAttribute("aria-disabled", "false");
}

function setActiveNav(targetId) {
  navLinks.forEach((link) => {
    const isActive = link.getAttribute("href") === `#${targetId}`;
    if (isActive) {
      link.setAttribute("aria-current", "true");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}

function wireNavigation() {
  if (!navLinks.length || !toolSections.length) return;

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const targetId = link.getAttribute("href").slice(1);
      setActiveNav(targetId);
    });
  });

  if (!("IntersectionObserver" in window)) {
    setActiveNav((window.location.hash || navLinks[0].getAttribute("href")).slice(1));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      const visibleEntry = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visibleEntry) {
        setActiveNav(visibleEntry.target.id);
      }
    },
    {
      rootMargin: "-35% 0px -55% 0px",
      threshold: [0, 0.25, 0.5],
    },
  );

  toolSections.forEach((section) => observer.observe(section));
  setActiveNav((window.location.hash || navLinks[0].getAttribute("href")).slice(1));
}

function wireDropZone(zone, input, onFiles) {
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    addClasses(zone, dropActiveClasses);
  });

  zone.addEventListener("dragleave", () => {
    removeClasses(zone, dropActiveClasses);
  });

  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    removeClasses(zone, dropActiveClasses);
    onFiles(event.dataTransfer.files);
  });

  input.addEventListener("change", () => onFiles(input.files));
}

function handleImageFiles(files) {
  const selectedFiles = Array.from(files || []);
  const file = selectedFiles[0];
  if (!file) return;

  removeState.file = file;
  removeState.files = selectedFiles;
  revokeUrl("sourceUrl", removeState);
  revokeUrl("resultUrl", removeState);
  removeState.resultBlob = null;
  removeState.resultFilename = "";

  removeState.sourceUrl = URL.createObjectURL(file);
  sourcePreview.src = removeState.sourceUrl;
  sourcePreview.classList.remove("hidden");
  sourcePreview.classList.add("block");
  resultPreview.removeAttribute("src");
  resultPreview.classList.add("hidden");
  resultPreview.classList.remove("block");
  downloadResult.textContent = "下载 PNG";
  disableDownloadLink(downloadResult);
  importRemovedToProcess.disabled = true;
  removeButton.disabled = false;
  removeButton.textContent = selectedFiles.length > 1 ? "批量去背景" : "一键去背景";
  removeStatus.textContent = selectedFiles.length > 1 ? `已选择 ${selectedFiles.length} 张` : "已选择";
  setFeedback(
    removeFeedback,
    selectedFiles.length > 1 ? `已选择 ${selectedFiles.length} 张，预览第一张：${file.name}` : file.name,
  );
}

async function removeBackground() {
  if (!removeState.files.length) return;

  const isBatch = removeState.files.length > 1;
  const idleButtonText = isBatch ? "批量去背景" : "一键去背景";

  const form = new FormData();
  if (isBatch) {
    removeState.files.forEach((file) => form.append("images", file));
  } else {
    form.append("image", removeState.file);
  }
  form.append("mode", $("removeMode").value);
  form.append("threshold", $("thresholdInput").value);
  form.append("bg_color", $("bgColorInput").value.trim());
  form.append("tolerance", $("toleranceInput").value);

  removeButton.disabled = true;
  removeButton.textContent = "处理中...";
  removeStatus.textContent = "处理中";
  setFeedback(removeFeedback, isBatch ? `正在批量抠除 ${removeState.files.length} 张图片。` : "正在抠除背景。");

  try {
    const response = await fetch(isBatch ? "/api/remove-background/batch" : "/api/remove-background", {
      method: "POST",
      body: form,
    });

    if (!response.ok) {
      let message = "处理失败";
      try {
        const error = await response.json();
        message = error.detail || message;
      } catch {
        message = await response.text();
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    revokeUrl("resultUrl", removeState);
    removeState.resultUrl = URL.createObjectURL(blob);
    const removed = response.headers.get("X-Pixels-Removed") || "0";

    if (isBatch) {
      removeState.resultBlob = null;
      removeState.resultFilename = "";
      resultPreview.removeAttribute("src");
      resultPreview.classList.add("hidden");
      resultPreview.classList.remove("block");
      downloadResult.textContent = "下载 ZIP";
      enableDownloadLink(downloadResult, removeState.resultUrl, "removed-background-batch.zip");
      importRemovedToProcess.disabled = true;
    } else {
      removeState.resultBlob = blob;
      removeState.resultFilename = `${removeState.file.name.replace(/\.[^.]+$/, "") || "image"}-transparent.png`;
      resultPreview.src = removeState.resultUrl;
      resultPreview.classList.remove("hidden");
      resultPreview.classList.add("block");
      downloadResult.textContent = "下载 PNG";
      enableDownloadLink(
        downloadResult,
        removeState.resultUrl,
        removeState.resultFilename,
      );
      importRemovedToProcess.disabled = false;
    }

    removeStatus.textContent = "完成";
    const effectiveThreshold = response.headers.get("X-Effective-Threshold");
    const thresholdHint =
      effectiveThreshold &&
      !$("bgColorInput").value.trim() &&
      effectiveThreshold !== $("thresholdInput").value
        ? `，自动阈值 ${effectiveThreshold}`
        : "";
    const processedImages = response.headers.get("X-Images-Processed") || String(removeState.files.length);
    setFeedback(
      removeFeedback,
      isBatch
        ? `完成 ${processedImages} 张，合计抠除 ${Number(removed).toLocaleString()} 个像素，已打包 ZIP。`
        : `完成，抠除 ${Number(removed).toLocaleString()} 个像素${thresholdHint}。`,
      "success",
    );
  } catch (error) {
    removeStatus.textContent = "失败";
    setFeedback(removeFeedback, error.message, "error");
  } finally {
    removeButton.disabled = false;
    removeButton.textContent = idleButtonText;
  }
}

function importRemovedResultToProcess() {
  const blob = removeState.resultBlob;
  if (!blob) return;

  const file = new File([blob], removeState.resultFilename || "removed-background.png", { type: blob.type || "image/png" });
  handleProcessFiles([file]);
  setActiveNav("tool-process");
  document.getElementById("tool-process").scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetProcessedResult() {
  revokeUrl("resultUrl", processState);
  processResultPreview.removeAttribute("src");
  processResultPreview.classList.add("hidden");
  processResultPreview.classList.remove("block");
  disableDownloadLink(downloadProcessed);
  processOutputMetrics.textContent = "-";
}

function updateProcessResizeInputs() {
  const enabled = processResizeInput.checked;
  processWidthInput.disabled = !enabled;
  processHeightInput.disabled = !enabled;
  processKeepAspectInput.disabled = !enabled;
}

function updateProcessCompressionInputs() {
  const paletteEnabled = processCompressInput.checked && processPngModeInput.value === "palette";
  processPngModeInput.disabled = !processCompressInput.checked;
  processPaletteColorsInput.disabled = !paletteEnabled;
}

function syncProcessDimension(changedInput) {
  if (
    processState.syncingDimensions ||
    !processKeepAspectInput.checked ||
    !processState.naturalWidth ||
    !processState.naturalHeight
  ) {
    return;
  }

  const width = Number(processWidthInput.value);
  const height = Number(processHeightInput.value);
  processState.syncingDimensions = true;
  if (changedInput === processWidthInput && Number.isFinite(width) && width > 0) {
    processHeightInput.value = String(Math.max(1, Math.round(width / processState.aspectRatio)));
  } else if (changedInput === processHeightInput && Number.isFinite(height) && height > 0) {
    processWidthInput.value = String(Math.max(1, Math.round(height * processState.aspectRatio)));
  }
  processState.syncingDimensions = false;
}

function handleProcessFiles(files) {
  const file = files?.[0];
  if (!file) return;

  processState.file = file;
  processState.naturalWidth = 0;
  processState.naturalHeight = 0;
  processState.aspectRatio = 1;
  revokeUrl("sourceUrl", processState);
  resetProcessedResult();

  processState.sourceUrl = URL.createObjectURL(file);
  processSourcePreview.src = processState.sourceUrl;
  processSourcePreview.classList.remove("hidden");
  processSourcePreview.classList.add("block");
  processButton.disabled = true;
  processStatus.textContent = "读取中";
  processSourceMetrics.textContent = `${formatBytes(file.size)}`;
  setFeedback(processFeedback, "正在读取图片尺寸。");

  const image = new Image();
  image.onload = () => {
    processState.naturalWidth = image.naturalWidth;
    processState.naturalHeight = image.naturalHeight;
    processState.aspectRatio = image.naturalWidth / image.naturalHeight;
    processWidthInput.value = String(image.naturalWidth);
    processHeightInput.value = String(image.naturalHeight);
    processSourceMetrics.textContent = `${image.naturalWidth}x${image.naturalHeight}，${formatBytes(file.size)}`;
    processButton.disabled = false;
    processStatus.textContent = "已选择";
    setFeedback(processFeedback, file.name);
  };
  image.onerror = () => {
    processStatus.textContent = "失败";
    processButton.disabled = true;
    setFeedback(processFeedback, "图片无法读取。", "error");
  };
  image.src = processState.sourceUrl;
}

async function processImage() {
  if (!processState.file) return;

  const form = new FormData();
  form.append("image", processState.file);
  form.append("compress_enabled", processCompressInput.checked ? "true" : "false");
  form.append("resize_enabled", processResizeInput.checked ? "true" : "false");
  form.append("target_width", processWidthInput.value || "0");
  form.append("target_height", processHeightInput.value || "0");
  form.append("keep_aspect_ratio", processKeepAspectInput.checked ? "true" : "false");
  form.append("png_mode", processPngModeInput.value);
  form.append("palette_colors", processPaletteColorsInput.value);

  processButton.disabled = true;
  processButton.textContent = "处理中...";
  processStatus.textContent = "处理中";
  setFeedback(processFeedback, "正在压缩并生成 PNG。");

  try {
    const response = await fetch("/api/process-image", {
      method: "POST",
      body: form,
    });

    if (!response.ok) {
      let message = "处理失败";
      try {
        const error = await response.json();
        message = error.detail || message;
      } catch {
        message = await response.text();
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    revokeUrl("resultUrl", processState);
    processState.resultUrl = URL.createObjectURL(blob);
    processResultPreview.src = processState.resultUrl;
    processResultPreview.classList.remove("hidden");
    processResultPreview.classList.add("block");
    enableDownloadLink(
      downloadProcessed,
      processState.resultUrl,
      `${processState.file.name.replace(/\.[^.]+$/, "") || "image"}-processed.png`,
    );

    const outputWidth = response.headers.get("X-Output-Width") || "-";
    const outputHeight = response.headers.get("X-Output-Height") || "-";
    const sourceBytes = Number(response.headers.get("X-Source-Bytes") || processState.file.size);
    const outputBytes = Number(response.headers.get("X-Output-Bytes") || blob.size);
    const saved = sourceBytes > 0 ? Math.max(0, 100 - (outputBytes / sourceBytes) * 100) : 0;
    processOutputMetrics.textContent = `${outputWidth}x${outputHeight}，${formatBytes(outputBytes)}`;
    processStatus.textContent = "完成";
    setFeedback(processFeedback, `完成，体积减少 ${saved.toFixed(1)}%。`, "success");
  } catch (error) {
    processStatus.textContent = "失败";
    setFeedback(processFeedback, error.message, "error");
  } finally {
    processButton.disabled = false;
    processButton.textContent = "处理图片";
  }
}

function numberValue(id, fallback) {
  const raw = $(id).value.trim();
  if (raw === "") return fallback;
  const value = Number(raw);
  return Number.isFinite(value) ? value : fallback;
}

function formatBytes(value) {
  const bytes = Math.max(0, Number(value) || 0);
  if (bytes < 1024) return `${bytes} B`;
  const kib = bytes / 1024;
  if (kib < 1024) return `${kib.toFixed(1)} KB`;
  return `${(kib / 1024).toFixed(2)} MB`;
}

function formatSeconds(value) {
  return `${(Math.round(value * 10) / 10).toFixed(1)}s`;
}

function getSpriteConfig() {
  const columns = Math.max(1, Math.floor(numberValue("columnsInput", 1)));
  const rows = Math.max(1, Math.floor(numberValue("rowsInput", 1)));
  const marginX = Math.max(0, Math.floor(numberValue("marginXInput", 0)));
  const marginY = Math.max(0, Math.floor(numberValue("marginYInput", 0)));
  const gapX = Math.max(0, Math.floor(numberValue("gapXInput", 0)));
  const gapY = Math.max(0, Math.floor(numberValue("gapYInput", 0)));
  const autoWidth = spriteState.image
    ? Math.floor((spriteState.image.naturalWidth - marginX * 2 - gapX * (columns - 1)) / columns)
    : 1;
  const autoHeight = spriteState.image
    ? Math.floor((spriteState.image.naturalHeight - marginY * 2 - gapY * (rows - 1)) / rows)
    : 1;
  const frameWidth = Math.max(1, Math.floor(numberValue("frameWidthInput", autoWidth)));
  const frameHeight = Math.max(1, Math.floor(numberValue("frameHeightInput", autoHeight)));
  const fps = Math.min(60, Math.max(1, Math.floor(numberValue("fpsInput", 8))));
  const contentThreshold = Math.min(255, Math.max(0, Math.floor(numberValue("contentThresholdInput", 248))));
  const alignPreview = $("alignPreviewInput").checked;
  const anchor = $("anchorInput").value;
  const viewMode = spriteViewModeInput.value;
  const noiseArea = Math.max(1, Math.floor(numberValue("noiseAreaInput", 160)));
  const footBandPercent = Math.min(40, Math.max(1, Math.floor(numberValue("footBandInput", 8))));
  const ignoreShadow = ignoreShadowInput.checked;
  const showDetection = showDetectionInput.checked;

  return {
    columns,
    rows,
    marginX,
    marginY,
    gapX,
    gapY,
    frameWidth,
    frameHeight,
    fps,
    contentThreshold,
    alignPreview,
    anchor,
    viewMode,
    noiseArea,
    footBandPercent,
    ignoreShadow,
    showDetection,
  };
}

function resetAlignmentState() {
  revokeUrl("alignedUrl", spriteState);
  spriteState.alignedImage = null;
  spriteState.analyses = [];
  spriteState.baseFrame = 0;
  downloadAlignedSheet.removeAttribute("href");
  downloadAlignedSheet.removeAttribute("download");
  removeClasses(downloadAlignedSheet, linkReadyClasses);
  addClasses(downloadAlignedSheet, linkDisabledClasses);
  downloadAlignedSheet.setAttribute("aria-disabled", "true");
  generateAlignedSheetButton.disabled = true;
  setFeedback(alignmentFeedback, "");
}

function resetPreviewSheetState() {
  revokeUrl("previewSheetUrl", spriteState);
  disableDownloadLink(downloadPreviewSheet);
}

function invalidateAlignment() {
  if (!spriteState.image) return;
  resetAlignmentState();
  resetPreviewSheetState();
  updateAlignmentControls();
  drawSheetInspector();
  drawSpriteFrame();
}

function updateAlignmentControls() {
  const config = getSpriteConfig();
  const total = spriteState.image ? config.columns * config.rows : 0;
  const hasImage = Boolean(spriteState.image && total > 0);
  baseFrameInput.max = String(Math.max(1, total));
  if (hasImage) {
    const base = Math.min(total, Math.max(1, Math.floor(numberValue("baseFrameInput", spriteState.currentFrame + 1))));
    baseFrameInput.value = String(base);
  }
  setBaseFrameButton.disabled = !hasImage;
  analyzeAlignmentButton.disabled = !hasImage;
  generateAlignedSheetButton.disabled = !hasImage || spriteState.analyses.length !== total;
  generatePreviewSheetButton.disabled = !hasImage;
}

function updateFrameOutput() {
  const { columns, rows } = getSpriteConfig();
  const total = spriteState.image ? columns * rows : 0;
  frameSlider.max = String(Math.max(0, total - 1));
  frameSlider.value = String(spriteState.currentFrame);
  frameOutput.textContent = `${total ? spriteState.currentFrame + 1 : 0} / ${total}`;
  updateAlignmentControls();
}

function syncSpriteSpeedControls() {
  const fps = Math.min(60, Math.max(1, Math.floor(numberValue("fpsInput", 8))));
  $("fpsInput").value = String(fps);
  speedSlider.value = String(Math.min(Number(speedSlider.max), Math.max(Number(speedSlider.min), fps)));
  speedOutput.textContent = `${fps} FPS`;
}

function updateSpriteMetrics(config) {
  if (!spriteState.image) {
    spriteMetrics.textContent = "未加载";
    return;
  }

  const usedWidth = config.marginX * 2 + config.columns * config.frameWidth + config.gapX * (config.columns - 1);
  const usedHeight = config.marginY * 2 + config.rows * config.frameHeight + config.gapY * (config.rows - 1);
  const leftoverX = spriteState.image.naturalWidth - usedWidth;
  const leftoverY = spriteState.image.naturalHeight - usedHeight;
  const status = leftoverX < 0 || leftoverY < 0 ? "越界" : `余量 ${leftoverX}px / ${leftoverY}px`;

  spriteMetrics.textContent = `${config.frameWidth}x${config.frameHeight}，${config.columns * config.rows} 帧，${status}`;
}

function drawSheetInspector() {
  const image = spriteState.image;
  const config = getSpriteConfig();

  if (!image) {
    sheetContext.clearRect(0, 0, sheetCanvas.width, sheetCanvas.height);
    updateSpriteMetrics(config);
    return;
  }

  sheetCanvas.width = image.naturalWidth;
  sheetCanvas.height = image.naturalHeight;
  sheetContext.clearRect(0, 0, sheetCanvas.width, sheetCanvas.height);
  sheetContext.drawImage(image, 0, 0);

  const lineWidth = Math.max(2, Math.round(image.naturalWidth / 900));
  sheetContext.lineWidth = lineWidth;
  sheetContext.font = `${Math.max(14, lineWidth * 7)}px sans-serif`;
  sheetContext.textBaseline = "top";

  for (let row = 0; row < config.rows; row += 1) {
    for (let column = 0; column < config.columns; column += 1) {
      const index = row * config.columns + column;
      const x = config.marginX + column * (config.frameWidth + config.gapX);
      const y = config.marginY + row * (config.frameHeight + config.gapY);
      const isCurrent = index === spriteState.currentFrame;
      const isOut =
        x < 0 ||
        y < 0 ||
        x + config.frameWidth > image.naturalWidth ||
        y + config.frameHeight > image.naturalHeight;

      sheetContext.strokeStyle = isOut ? "rgba(180, 35, 24, 0.95)" : "rgba(37, 99, 235, 0.85)";
      sheetContext.strokeRect(x + lineWidth / 2, y + lineWidth / 2, config.frameWidth - lineWidth, config.frameHeight - lineWidth);

      if (isCurrent) {
        sheetContext.fillStyle = "rgba(249, 115, 22, 0.14)";
        sheetContext.fillRect(x, y, config.frameWidth, config.frameHeight);
        sheetContext.strokeStyle = "rgba(249, 115, 22, 0.98)";
        sheetContext.lineWidth = lineWidth * 2;
        sheetContext.strokeRect(
          x + lineWidth,
          y + lineWidth,
          config.frameWidth - lineWidth * 2,
          config.frameHeight - lineWidth * 2,
        );
        sheetContext.lineWidth = lineWidth;
      }

      sheetContext.fillStyle = isCurrent ? "rgba(194, 65, 12, 0.98)" : "rgba(30, 41, 59, 0.72)";
      sheetContext.fillText(String(index + 1), x + lineWidth * 2, y + lineWidth * 2);

      const analysis = spriteState.analyses[index];
      if (config.showDetection && analysis?.valid) {
        const box = analysis.bounds;
        const anchor = analysis.anchor;
        const isOutlier = analysis.outlier;
        sheetContext.strokeStyle = isOutlier ? "rgba(220, 38, 38, 0.95)" : "rgba(5, 150, 105, 0.95)";
        sheetContext.lineWidth = lineWidth;
        sheetContext.strokeRect(x + box.x, y + box.y, box.width, box.height);
        sheetContext.beginPath();
        sheetContext.moveTo(x + box.x, y + anchor.y);
        sheetContext.lineTo(x + box.x + box.width, y + anchor.y);
        sheetContext.moveTo(x + anchor.x - lineWidth * 3, y + anchor.y);
        sheetContext.lineTo(x + anchor.x + lineWidth * 3, y + anchor.y);
        sheetContext.moveTo(x + anchor.x, y + anchor.y - lineWidth * 3);
        sheetContext.lineTo(x + anchor.x, y + anchor.y + lineWidth * 3);
        sheetContext.stroke();
        sheetContext.fillStyle = isOutlier ? "rgba(185, 28, 28, 0.98)" : "rgba(4, 120, 87, 0.98)";
        sheetContext.fillText(`dx ${analysis.dx} dy ${analysis.dy}`, x + lineWidth * 2, y + config.frameHeight - lineWidth * 9);
      }
    }
  }

  updateSpriteMetrics(config);
}

function findContentBounds(imageData, threshold) {
  const { data, width, height } = imageData;
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const index = (y * width + x) * 4;
      const alpha = data[index + 3];
      const isBackground =
        alpha < 8 ||
        (data[index] >= threshold && data[index + 1] >= threshold && data[index + 2] >= threshold);

      if (!isBackground) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
    }
  }

  if (maxX < minX || maxY < minY) return null;
  return {
    x: minX,
    y: minY,
    width: maxX - minX + 1,
    height: maxY - minY + 1,
  };
}

function isSpriteBackgroundPixel(data, index, threshold, ignoreShadow) {
  const r = data[index];
  const g = data[index + 1];
  const b = data[index + 2];
  const alpha = data[index + 3];
  if (alpha < 8) return true;
  if (r >= threshold && g >= threshold && b >= threshold) return true;

  if (ignoreShadow) {
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    if (max > 110 && max - min < 28) return true;
  }

  return false;
}

function getFrameSourceRect(frameIndex, config) {
  const column = frameIndex % config.columns;
  const row = Math.floor(frameIndex / config.columns);
  return {
    x: config.marginX + column * (config.frameWidth + config.gapX),
    y: config.marginY + row * (config.frameHeight + config.gapY),
    column,
    row,
  };
}

function drawFrameToCanvas(image, frameIndex, config, canvas) {
  const source = getFrameSourceRect(frameIndex, config);
  canvas.width = config.frameWidth;
  canvas.height = config.frameHeight;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.clearRect(0, 0, config.frameWidth, config.frameHeight);
  context.drawImage(
    image,
    source.x,
    source.y,
    config.frameWidth,
    config.frameHeight,
    0,
    0,
    config.frameWidth,
    config.frameHeight,
  );
  return { canvas, context, source };
}

function analyzeFrameComponent(imageData, config) {
  const { data, width, height } = imageData;
  const total = width * height;
  const foreground = new Uint8Array(total);
  const visited = new Uint8Array(total);

  for (let point = 0; point < total; point += 1) {
    if (!isSpriteBackgroundPixel(data, point * 4, config.contentThreshold, config.ignoreShadow)) {
      foreground[point] = 1;
    }
  }

  let best = null;
  const stack = [];
  const component = [];

  for (let point = 0; point < total; point += 1) {
    if (!foreground[point] || visited[point]) continue;

    stack.length = 0;
    component.length = 0;
    stack.push(point);
    visited[point] = 1;

    let minX = width;
    let minY = height;
    let maxX = -1;
    let maxY = -1;

    while (stack.length) {
      const current = stack.pop();
      component.push(current);
      const x = current % width;
      const y = Math.floor(current / width);
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);

      const left = current - 1;
      const right = current + 1;
      const up = current - width;
      const down = current + width;
      if (x > 0 && foreground[left] && !visited[left]) {
        visited[left] = 1;
        stack.push(left);
      }
      if (x < width - 1 && foreground[right] && !visited[right]) {
        visited[right] = 1;
        stack.push(right);
      }
      if (y > 0 && foreground[up] && !visited[up]) {
        visited[up] = 1;
        stack.push(up);
      }
      if (y < height - 1 && foreground[down] && !visited[down]) {
        visited[down] = 1;
        stack.push(down);
      }
    }

    if (component.length < config.noiseArea) continue;

    if (!best || component.length > best.area) {
      best = {
        area: component.length,
        points: component.slice(),
        bounds: {
          x: minX,
          y: minY,
          width: maxX - minX + 1,
          height: maxY - minY + 1,
        },
      };
    }
  }

  if (!best) return null;

  const bottomBand = Math.max(1, Math.round(best.bounds.height * (config.footBandPercent / 100)));
  const bottomStart = best.bounds.y + best.bounds.height - bottomBand;
  let footMinX = width;
  let footMaxX = -1;

  for (const point of best.points) {
    const x = point % width;
    const y = Math.floor(point / width);
    if (y >= bottomStart) {
      footMinX = Math.min(footMinX, x);
      footMaxX = Math.max(footMaxX, x);
    }
  }

  if (footMaxX < footMinX) {
    footMinX = best.bounds.x;
    footMaxX = best.bounds.x + best.bounds.width - 1;
  }

  return {
    valid: true,
    area: best.area,
    bounds: best.bounds,
    anchor: {
      x: Math.round((footMinX + footMaxX) / 2),
      y: best.bounds.y + best.bounds.height - 1,
    },
  };
}

function fillAlignedFrameBackground(frameCanvas, targetContext) {
  const context = frameCanvas.getContext("2d", { willReadFrequently: true });
  const sampleX = Math.min(2, frameCanvas.width - 1);
  const sampleY = Math.min(2, frameCanvas.height - 1);
  const [r, g, b, alpha] = context.getImageData(sampleX, sampleY, 1, 1).data;
  if (alpha < 8) return;

  targetContext.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha / 255})`;
  targetContext.fillRect(0, 0, frameCanvas.width, frameCanvas.height);
}

function median(values) {
  if (!values.length) return 0;
  const sorted = values.slice().sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function analyzeSpriteAlignment() {
  if (!spriteState.image) return null;

  const config = getSpriteConfig();
  const total = config.columns * config.rows;
  const baseIndex = Math.min(total - 1, Math.max(0, Math.floor(numberValue("baseFrameInput", spriteState.currentFrame + 1)) - 1));
  const frameCanvas = document.createElement("canvas");
  const analyses = [];

  for (let frameIndex = 0; frameIndex < total; frameIndex += 1) {
    const { context } = drawFrameToCanvas(spriteState.image, frameIndex, config, frameCanvas);
    const component = analyzeFrameComponent(context.getImageData(0, 0, config.frameWidth, config.frameHeight), config);
    analyses.push(component || { valid: false, dx: 0, dy: 0, rawDx: 0, rawDy: 0, outlier: true });
  }

  const base = analyses[baseIndex];
  if (!base?.valid) {
    setFeedback(alignmentFeedback, `第 ${baseIndex + 1} 帧没有检测到稳定主体，请换一帧作为基准。`, "error");
    return null;
  }

  for (const analysis of analyses) {
    if (!analysis.valid) continue;
    analysis.rawDx = Math.round(base.anchor.x - analysis.anchor.x);
    analysis.rawDy = Math.round(base.anchor.y - analysis.anchor.y);
    analysis.dx = analysis.rawDx;
    analysis.dy = analysis.rawDy;
  }

  const valid = analyses.filter((analysis) => analysis.valid);
  const medianDx = median(valid.map((analysis) => analysis.rawDx));
  const medianDy = median(valid.map((analysis) => analysis.rawDy));
  const outlierDistance = Math.max(18, Math.round(Math.max(config.frameWidth, config.frameHeight) * 0.14));

  for (const analysis of analyses) {
    if (!analysis.valid) {
      analysis.outlier = true;
      continue;
    }
    analysis.outlier =
      Math.abs(analysis.rawDx - medianDx) > outlierDistance ||
      Math.abs(analysis.rawDy - medianDy) > outlierDistance;
  }

  for (let index = 1; index < analyses.length - 1; index += 1) {
    const prev = analyses[index - 1];
    const current = analyses[index];
    const next = analyses[index + 1];
    if (!current.valid || current.outlier || !prev.valid || prev.outlier || !next.valid || next.outlier) continue;
    current.dx = Math.round((prev.rawDx + current.rawDx * 2 + next.rawDx) / 4);
    current.dy = Math.round((prev.rawDy + current.rawDy * 2 + next.rawDy) / 4);
  }

  spriteState.analyses = analyses;
  spriteState.baseFrame = baseIndex;
  resetPreviewSheetState();
  setFeedback(
    alignmentFeedback,
    `已分析 ${valid.length}/${total} 帧，基准帧 ${baseIndex + 1}，异常 ${analyses.filter((analysis) => analysis.outlier).length} 帧。`,
    "success",
  );
  updateAlignmentControls();
  drawSheetInspector();
  drawSpriteFrame();
  return analyses;
}

function drawAdvancedAlignedFrame(image, frameIndex, config, targetContext) {
  const analysis = spriteState.analyses[frameIndex];
  if (!analysis?.valid) {
    const source = getFrameSourceRect(frameIndex, config);
    targetContext.drawImage(image, source.x, source.y, config.frameWidth, config.frameHeight, 0, 0, config.frameWidth, config.frameHeight);
    return;
  }

  const frameCanvas = document.createElement("canvas");
  drawFrameToCanvas(image, frameIndex, config, frameCanvas);
  fillAlignedFrameBackground(frameCanvas, targetContext);
  targetContext.drawImage(frameCanvas, analysis.dx, analysis.dy);
}

async function generateAlignedSheet() {
  if (!spriteState.image) return;

  resetPreviewSheetState();
  let analyses = spriteState.analyses;
  const config = getSpriteConfig();
  const total = config.columns * config.rows;
  if (analyses.length !== total) {
    analyses = analyzeSpriteAlignment();
  }
  if (!analyses) return;

  const output = document.createElement("canvas");
  output.width = config.columns * config.frameWidth;
  output.height = config.rows * config.frameHeight;
  const outputContext = output.getContext("2d");
  outputContext.clearRect(0, 0, output.width, output.height);

  for (let frameIndex = 0; frameIndex < total; frameIndex += 1) {
    const { column, row } = getFrameSourceRect(frameIndex, config);
    outputContext.save();
    outputContext.beginPath();
    outputContext.rect(column * config.frameWidth, row * config.frameHeight, config.frameWidth, config.frameHeight);
    outputContext.clip();
    outputContext.translate(column * config.frameWidth, row * config.frameHeight);
    drawAdvancedAlignedFrame(spriteState.image, frameIndex, config, outputContext);
    outputContext.restore();
  }

  const blob = await canvasToBlob(output);
  revokeUrl("alignedUrl", spriteState);
  spriteState.alignedUrl = URL.createObjectURL(blob);
  downloadAlignedSheet.href = spriteState.alignedUrl;
  downloadAlignedSheet.download = "aligned-sprite-sheet.png";
  removeClasses(downloadAlignedSheet, linkDisabledClasses);
  addClasses(downloadAlignedSheet, linkReadyClasses);
  downloadAlignedSheet.setAttribute("aria-disabled", "false");

  const image = new Image();
  image.onload = () => {
    spriteState.alignedImage = image;
    spriteViewModeInput.value = "fixed";
    drawSpriteFrame();
    setFeedback(alignmentFeedback, `修正版已生成：${output.width}x${output.height}，${total} 帧。`, "success");
  };
  image.onerror = () => {
    setFeedback(alignmentFeedback, "修正版 PNG 无法读取。", "error");
  };
  image.src = spriteState.alignedUrl;
}

function drawAlignedFrame(image, sx, sy, config, targetContext) {
  const frameCanvas = document.createElement("canvas");
  frameCanvas.width = config.frameWidth;
  frameCanvas.height = config.frameHeight;
  const frameContext = frameCanvas.getContext("2d", { willReadFrequently: true });
  frameContext.drawImage(image, sx, sy, config.frameWidth, config.frameHeight, 0, 0, config.frameWidth, config.frameHeight);

  if (!config.alignPreview) {
    targetContext.drawImage(frameCanvas, 0, 0);
    return;
  }

  const bounds = findContentBounds(
    frameContext.getImageData(0, 0, config.frameWidth, config.frameHeight),
    config.contentThreshold,
  );

  if (!bounds) {
    targetContext.drawImage(frameCanvas, 0, 0);
    return;
  }

  const dx = Math.round((config.frameWidth - bounds.width) / 2);
  const dy =
    config.anchor === "center"
      ? Math.round((config.frameHeight - bounds.height) / 2)
      : config.frameHeight - bounds.height;

  targetContext.drawImage(
    frameCanvas,
    bounds.x,
    bounds.y,
    bounds.width,
    bounds.height,
    dx,
    dy,
    bounds.width,
    bounds.height,
  );
}

function drawPreviewFrame(frameIndex, config, targetContext) {
  const total = config.columns * config.rows;
  const useFixed = config.viewMode === "fixed" && spriteState.alignedImage;
  const image = useFixed ? spriteState.alignedImage : spriteState.image;
  if (!image || total < 1) return false;

  const column = frameIndex % config.columns;
  const row = Math.floor(frameIndex / config.columns);
  const sx = config.marginX + column * (config.frameWidth + config.gapX);
  const sy = config.marginY + row * (config.frameHeight + config.gapY);

  if (useFixed || config.viewMode === "raw" || !config.alignPreview) {
    const sourceX = useFixed ? column * config.frameWidth : sx;
    const sourceY = useFixed ? row * config.frameHeight : sy;
    targetContext.drawImage(image, sourceX, sourceY, config.frameWidth, config.frameHeight, 0, 0, config.frameWidth, config.frameHeight);
  } else if (config.viewMode === "smart" && spriteState.analyses.length === total) {
    drawAdvancedAlignedFrame(image, frameIndex, config, targetContext);
  } else {
    drawAlignedFrame(image, sx, sy, config, targetContext);
  }

  return true;
}

async function generatePreviewSheet() {
  const config = getSpriteConfig();
  const total = config.columns * config.rows;
  if (!spriteState.image || total < 1) return;

  generatePreviewSheetButton.disabled = true;
  generatePreviewSheetButton.textContent = "导出中...";

  try {
    const output = document.createElement("canvas");
    output.width = config.columns * config.frameWidth;
    output.height = config.rows * config.frameHeight;
    const outputContext = output.getContext("2d");
    outputContext.clearRect(0, 0, output.width, output.height);

    for (let frameIndex = 0; frameIndex < total; frameIndex += 1) {
      const column = frameIndex % config.columns;
      const row = Math.floor(frameIndex / config.columns);
      outputContext.save();
      outputContext.beginPath();
      outputContext.rect(column * config.frameWidth, row * config.frameHeight, config.frameWidth, config.frameHeight);
      outputContext.clip();
      outputContext.translate(column * config.frameWidth, row * config.frameHeight);
      drawPreviewFrame(frameIndex, config, outputContext);
      outputContext.restore();
    }

    const blob = await canvasToBlob(output);
    revokeUrl("previewSheetUrl", spriteState);
    spriteState.previewSheetUrl = URL.createObjectURL(blob);
    enableDownloadLink(downloadPreviewSheet, spriteState.previewSheetUrl, "preview-sprite-sheet.png");
    setFeedback(spriteFeedback, `预览 Sheet 已导出：${output.width}x${output.height}，${total} 帧。`, "success");
  } catch (error) {
    setFeedback(spriteFeedback, error.message, "error");
  } finally {
    updateAlignmentControls();
    generatePreviewSheetButton.textContent = "导出预览 Sheet";
  }
}

function drawSpriteFrame() {
  const config = getSpriteConfig();
  const total = config.columns * config.rows;
  const image = spriteState.image;
  if (!image || total < 1) {
    spriteContext.clearRect(0, 0, spriteCanvas.width, spriteCanvas.height);
    updateFrameOutput();
    drawSheetInspector();
    return;
  }

  spriteState.currentFrame = Math.min(spriteState.currentFrame, total - 1);
  spriteCanvas.width = config.frameWidth;
  spriteCanvas.height = config.frameHeight;
  spriteContext.clearRect(0, 0, config.frameWidth, config.frameHeight);
  drawPreviewFrame(spriteState.currentFrame, config, spriteContext);

  updateFrameOutput();
  drawSheetInspector();
}

function stopSprite() {
  if (spriteState.timer) {
    window.clearInterval(spriteState.timer);
    spriteState.timer = 0;
  }
  spriteState.playing = false;
  playButton.textContent = "播放";
}

function startSprite() {
  if (!spriteState.image) return;

  stopSprite();
  spriteState.playing = true;
  playButton.textContent = "暂停";
  spriteState.timer = window.setInterval(() => {
    const { columns, rows } = getSpriteConfig();
    const total = columns * rows;
    spriteState.currentFrame = (spriteState.currentFrame + 1) % total;
    drawSpriteFrame();
  }, 1000 / getSpriteConfig().fps);
}

function toggleSprite() {
  if (spriteState.playing) {
    stopSprite();
  } else {
    startSprite();
  }
}

function stepFrame(offset) {
  const { columns, rows } = getSpriteConfig();
  const total = columns * rows;
  if (!spriteState.image || total < 1) return;
  spriteState.currentFrame = (spriteState.currentFrame + offset + total) % total;
  drawSpriteFrame();
}

function handleSpriteFiles(files) {
  const file = files?.[0];
  if (!file) return;

  loadSpriteFile(file);
}

function loadSpriteFile(file) {
  stopSprite();
  revokeUrl("imageUrl", spriteState);
  spriteState.imageUrl = URL.createObjectURL(file);
  resetAlignmentState();
  resetPreviewSheetState();

  const image = new Image();
  image.onload = () => {
    spriteState.image = image;
    spriteState.currentFrame = 0;
    playButton.disabled = false;
    prevFrameButton.disabled = false;
    nextFrameButton.disabled = false;
    frameSlider.disabled = false;
    spriteStatus.textContent = "已选择";
    setFeedback(spriteFeedback, `${file.name}，尺寸 ${image.naturalWidth} x ${image.naturalHeight}`);
    updateAlignmentControls();
    drawSpriteFrame();
  };
  image.onerror = () => {
    spriteStatus.textContent = "失败";
    setFeedback(spriteFeedback, "图片无法读取。", "error");
  };
  image.src = spriteState.imageUrl;
}

function loadSpriteFromBlob(blob, options = {}) {
  stopSprite();
  revokeUrl("imageUrl", spriteState);
  spriteState.imageUrl = URL.createObjectURL(blob);
  resetAlignmentState();
  resetPreviewSheetState();

  const image = new Image();
  image.onload = () => {
    spriteState.image = image;
    spriteState.currentFrame = 0;
    if (options.columns) $("columnsInput").value = String(options.columns);
    if (options.rows) $("rowsInput").value = String(options.rows);
    if (options.frameWidth) $("frameWidthInput").value = String(options.frameWidth);
    if (options.frameHeight) $("frameHeightInput").value = String(options.frameHeight);
    if (options.fps) $("fpsInput").value = String(options.fps);
    syncSpriteSpeedControls();
    $("marginXInput").value = "0";
    $("marginYInput").value = "0";
    $("gapXInput").value = "0";
    $("gapYInput").value = "0";
    playButton.disabled = false;
    prevFrameButton.disabled = false;
    nextFrameButton.disabled = false;
    frameSlider.disabled = false;
    spriteStatus.textContent = "视频生成";
    setFeedback(spriteFeedback, `已从视频生成 ${options.totalFrames || options.columns * options.rows} 帧，可直接播放检查。`, "success");
    updateAlignmentControls();
    drawSpriteFrame();
  };
  image.onerror = () => {
    spriteStatus.textContent = "失败";
    setFeedback(spriteFeedback, "生成的 sprite sheet 无法读取。", "error");
  };
  image.src = spriteState.imageUrl;
}

function getVideoConfig() {
  const start = Math.max(0, Math.min(videoState.duration, Number(videoStartInput.value) || 0));
  const end = Math.max(0, Math.min(videoState.duration, Number(videoEndInput.value) || 0));
  const fps = Math.min(60, Math.max(1, Math.floor(numberValue("videoFpsInput", 12))));
  const columns = Math.min(24, Math.max(1, Math.floor(numberValue("videoColumnsInput", 6))));
  const naturalWidth = videoPreview.videoWidth || 1;
  const naturalHeight = videoPreview.videoHeight || 1;
  const targetWidth = Math.max(1, Math.floor(numberValue("videoFrameWidthInput", naturalWidth)));
  const scale = targetWidth / naturalWidth;
  const targetHeight = Math.max(1, Math.round(naturalHeight * scale));
  const segmentDuration = Math.max(0, end - start);
  const frameCount = segmentDuration > 0 ? Math.max(1, Math.floor(segmentDuration * fps) + 1) : 0;

  return { start, end, fps, columns, naturalWidth, naturalHeight, targetWidth, targetHeight, segmentDuration, frameCount };
}

function updateVideoSummary(preserveFeedback = false) {
  const config = getVideoConfig();
  const hasVideo = Boolean(videoState.file && videoState.duration > 0);
  const validRange = hasVideo && config.end > config.start;
  const tooManyFrames = config.frameCount > 600;

  videoRangeOutput.textContent = `${formatSeconds(config.start)} - ${formatSeconds(config.end)}`;
  videoSizeValue.textContent = hasVideo ? `${config.naturalWidth} x ${config.naturalHeight}` : "-";
  videoDurationValue.textContent = formatSeconds(config.segmentDuration);
  videoFrameCountValue.textContent = String(config.frameCount);
  generateVideoFramesButton.disabled = !validRange || tooManyFrames || videoState.generating;

  if (!hasVideo) {
    setFeedback(videoFeedback, "");
    return;
  }
  if (!validRange) {
    setFeedback(videoFeedback, "结束时间必须大于开始时间。", "error");
    return;
  }
  if (tooManyFrames) {
    setFeedback(videoFeedback, "预计帧数超过 600，请降低 FPS 或缩短片段。", "error");
    return;
  }
  if (!videoState.generating && !preserveFeedback) {
    setFeedback(videoFeedback, `片段 ${formatSeconds(config.segmentDuration)}，预计生成 ${config.frameCount} 帧。`);
  }
}

function handleVideoFiles(files) {
  const file = files?.[0];
  if (!file) return;

  if (!file.type.startsWith("video/")) {
    videoStatus.textContent = "失败";
    setFeedback(videoFeedback, "请选择浏览器可播放的视频文件。", "error");
    return;
  }

  revokeUrl("videoUrl", videoState);
  revokeUrl("sheetUrl", videoState);
  videoState.file = file;
  videoState.duration = 0;
  videoState.videoUrl = URL.createObjectURL(file);
  videoPreview.src = videoState.videoUrl;
  videoStatus.textContent = "载入中";
  videoSheetContext.clearRect(0, 0, videoSheetCanvas.width, videoSheetCanvas.height);
  videoSheetMetrics.textContent = "未生成";
  downloadVideoSheet.removeAttribute("href");
  downloadVideoSheet.removeAttribute("download");
  removeClasses(downloadVideoSheet, linkReadyClasses);
  addClasses(downloadVideoSheet, linkDisabledClasses);
  downloadVideoSheet.setAttribute("aria-disabled", "true");
  setFeedback(videoFeedback, file.name);
}

function onVideoLoaded() {
  videoState.duration = Number.isFinite(videoPreview.duration) ? videoPreview.duration : 0;
  const duration = Math.max(0, Math.floor(videoState.duration * 10) / 10);
  videoStartInput.disabled = false;
  videoEndInput.disabled = false;
  videoStartInput.max = String(duration);
  videoEndInput.max = String(duration);
  videoStartInput.value = "0";
  videoEndInput.value = String(duration);
  videoStatus.textContent = "已选择";
  updateVideoSummary();
}

function clampVideoRange(changedInput) {
  const minGap = 0.1;
  let start = Number(videoStartInput.value) || 0;
  let end = Number(videoEndInput.value) || 0;

  if (changedInput === videoStartInput && start >= end) {
    start = Math.max(0, end - minGap);
    videoStartInput.value = String(Math.round(start * 10) / 10);
  }
  if (changedInput === videoEndInput && end <= start) {
    end = Math.min(videoState.duration, start + minGap);
    videoEndInput.value = String(Math.round(end * 10) / 10);
  }

  updateVideoSummary();
}

function seekVideo(time) {
  return new Promise((resolve, reject) => {
    const targetTime = Math.min(Math.max(time, 0), Math.max(videoState.duration - 0.01, 0));
    if (videoPreview.readyState >= 2 && Math.abs(videoPreview.currentTime - targetTime) < 0.001) {
      requestAnimationFrame(resolve);
      return;
    }

    const timeout = window.setTimeout(() => {
      cleanup();
      reject(new Error("视频 seek 超时，请换一个更短或更常见编码的视频。"));
    }, 8000);

    function cleanup() {
      window.clearTimeout(timeout);
      videoPreview.removeEventListener("seeked", handleSeeked);
      videoPreview.removeEventListener("error", handleError);
    }

    function handleSeeked() {
      cleanup();
      resolve();
    }

    function handleError() {
      cleanup();
      reject(new Error("视频无法定位到指定时间。"));
    }

    videoPreview.addEventListener("seeked", handleSeeked, { once: true });
    videoPreview.addEventListener("error", handleError, { once: true });
    videoPreview.currentTime = targetTime;
  });
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob);
      } else {
        reject(new Error("无法生成 PNG。"));
      }
    }, "image/png");
  });
}

async function generateVideoFrames() {
  const config = getVideoConfig();
  if (!videoState.file || config.end <= config.start || config.frameCount < 1 || config.frameCount > 600) {
    updateVideoSummary();
    return;
  }

  videoState.generating = true;
  generateVideoFramesButton.disabled = true;
  videoInput.disabled = true;
  generateVideoFramesButton.textContent = "生成中...";
  videoStatus.textContent = "生成中";
  revokeUrl("sheetUrl", videoState);
  videoPreview.pause();

  try {
    const rows = Math.ceil(config.frameCount / config.columns);
    videoFrameCanvas.width = config.targetWidth;
    videoFrameCanvas.height = config.targetHeight;
    videoSheetCanvas.width = config.columns * config.targetWidth;
    videoSheetCanvas.height = rows * config.targetHeight;
    videoSheetContext.clearRect(0, 0, videoSheetCanvas.width, videoSheetCanvas.height);

    for (let index = 0; index < config.frameCount; index += 1) {
      const time = Math.min(config.start + index / config.fps, config.end);
      setFeedback(videoFeedback, `正在生成 ${index + 1} / ${config.frameCount} 帧`);
      await seekVideo(time);
      videoFrameContext.clearRect(0, 0, config.targetWidth, config.targetHeight);
      videoFrameContext.drawImage(videoPreview, 0, 0, config.targetWidth, config.targetHeight);

      const column = index % config.columns;
      const row = Math.floor(index / config.columns);
      videoSheetContext.drawImage(
        videoFrameCanvas,
        column * config.targetWidth,
        row * config.targetHeight,
      );
      await new Promise((resolve) => requestAnimationFrame(resolve));
    }

    const blob = await canvasToBlob(videoSheetCanvas);
    videoState.sheetUrl = URL.createObjectURL(blob);
    downloadVideoSheet.href = videoState.sheetUrl;
    downloadVideoSheet.download = `${videoState.file.name.replace(/\.[^.]+$/, "") || "video"}-sprite-sheet.png`;
    removeClasses(downloadVideoSheet, linkDisabledClasses);
    addClasses(downloadVideoSheet, linkReadyClasses);
    downloadVideoSheet.setAttribute("aria-disabled", "false");
    videoSheetMetrics.textContent = `${videoSheetCanvas.width}x${videoSheetCanvas.height}，${config.frameCount} 帧`;
    setFeedback(videoFeedback, `完成：${config.frameCount} 帧，${rows} 行 x ${config.columns} 列。`, "success");
    videoStatus.textContent = "完成";

    loadSpriteFromBlob(blob, {
      columns: config.columns,
      rows,
      frameWidth: config.targetWidth,
      frameHeight: config.targetHeight,
      fps: config.fps,
      totalFrames: config.frameCount,
    });
  } catch (error) {
    videoStatus.textContent = "失败";
    setFeedback(videoFeedback, error.message, "error");
  } finally {
    videoState.generating = false;
    videoInput.disabled = false;
    generateVideoFramesButton.textContent = "生成序列帧";
    updateVideoSummary(true);
  }
}

wireDropZone(imageDropZone, imageInput, handleImageFiles);
wireDropZone(spriteDropZone, spriteInput, handleSpriteFiles);
wireDropZone(videoDropZone, videoInput, handleVideoFiles);
wireDropZone(processDropZone, processInput, handleProcessFiles);
wireNavigation();

removeButton.addEventListener("click", removeBackground);
importRemovedToProcess.addEventListener("click", importRemovedResultToProcess);
processButton.addEventListener("click", processImage);
playButton.addEventListener("click", toggleSprite);
prevFrameButton.addEventListener("click", () => stepFrame(-1));
nextFrameButton.addEventListener("click", () => stepFrame(1));
generateVideoFramesButton.addEventListener("click", generateVideoFrames);
setBaseFrameButton.addEventListener("click", () => {
  baseFrameInput.value = String(spriteState.currentFrame + 1);
  invalidateAlignment();
  setFeedback(alignmentFeedback, `已把第 ${spriteState.currentFrame + 1} 帧设为基准。`);
});
analyzeAlignmentButton.addEventListener("click", analyzeSpriteAlignment);
generateAlignedSheetButton.addEventListener("click", generateAlignedSheet);
generatePreviewSheetButton.addEventListener("click", generatePreviewSheet);
videoPreview.addEventListener("loadedmetadata", onVideoLoaded);
videoPreview.addEventListener("error", () => {
  videoStatus.textContent = "失败";
  setFeedback(videoFeedback, "浏览器无法读取这个视频，请换 MP4/WebM 或更常见编码。", "error");
});
frameSlider.addEventListener("input", () => {
  spriteState.currentFrame = Number(frameSlider.value);
  drawSpriteFrame();
});

[videoStartInput, videoEndInput].forEach((input) => {
  input.addEventListener("input", () => clampVideoRange(input));
});

["videoFpsInput", "videoColumnsInput", "videoFrameWidthInput"].forEach((id) => {
  $(id).addEventListener("input", () => updateVideoSummary());
});

[processWidthInput, processHeightInput].forEach((input) => {
  input.addEventListener("input", () => {
    syncProcessDimension(input);
    resetProcessedResult();
  });
});

processResizeInput.addEventListener("change", () => {
  updateProcessResizeInputs();
  resetProcessedResult();
});
processKeepAspectInput.addEventListener("change", () => {
  if (processKeepAspectInput.checked) {
    syncProcessDimension(processWidthInput);
  }
  resetProcessedResult();
});
processCompressInput.addEventListener("change", () => {
  updateProcessCompressionInputs();
  resetProcessedResult();
});
processPngModeInput.addEventListener("change", () => {
  updateProcessCompressionInputs();
  resetProcessedResult();
});
processPaletteColorsInput.addEventListener("change", resetProcessedResult);

[
  "columnsInput",
  "rowsInput",
  "frameWidthInput",
  "frameHeightInput",
  "marginXInput",
  "marginYInput",
  "gapXInput",
  "gapYInput",
  "fpsInput",
  "contentThresholdInput",
  "anchorInput",
].forEach((id) => {
  $(id).addEventListener("input", () => {
    if (id !== "fpsInput") {
      resetPreviewSheetState();
    }
    if (
      [
        "columnsInput",
        "rowsInput",
        "frameWidthInput",
        "frameHeightInput",
        "marginXInput",
        "marginYInput",
        "gapXInput",
        "gapYInput",
        "contentThresholdInput",
      ].includes(id)
    ) {
      resetAlignmentState();
    }
    if (id === "fpsInput" && spriteState.playing) {
      syncSpriteSpeedControls();
      startSprite();
      return;
    }
    if (id === "fpsInput") {
      syncSpriteSpeedControls();
    }
    drawSpriteFrame();
  });
});

speedSlider.addEventListener("input", () => {
  $("fpsInput").value = speedSlider.value;
  syncSpriteSpeedControls();
  if (spriteState.playing) {
    startSprite();
  }
});

$("alignPreviewInput").addEventListener("change", () => {
  resetPreviewSheetState();
  drawSpriteFrame();
});
spriteViewModeInput.addEventListener("change", () => {
  resetPreviewSheetState();
  drawSpriteFrame();
});
baseFrameInput.addEventListener("input", invalidateAlignment);
noiseAreaInput.addEventListener("input", invalidateAlignment);
footBandInput.addEventListener("input", invalidateAlignment);
ignoreShadowInput.addEventListener("change", invalidateAlignment);
showDetectionInput.addEventListener("change", () => {
  drawSheetInspector();
});

downloadResult.addEventListener("click", (event) => {
  if (downloadResult.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
});

downloadProcessed.addEventListener("click", (event) => {
  if (downloadProcessed.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
});

downloadVideoSheet.addEventListener("click", (event) => {
  if (downloadVideoSheet.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
});

downloadAlignedSheet.addEventListener("click", (event) => {
  if (downloadAlignedSheet.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
});

downloadPreviewSheet.addEventListener("click", (event) => {
  if (downloadPreviewSheet.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
});

frameSlider.disabled = true;
syncSpriteSpeedControls();
drawSpriteFrame();
updateVideoSummary();
updateAlignmentControls();
updateProcessResizeInputs();
updateProcessCompressionInputs();
