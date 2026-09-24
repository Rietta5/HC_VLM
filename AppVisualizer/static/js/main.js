// VLM Model Visualizer Frontend JavaScript Logic

let boardData = null;
let modelsList = [];
let wordsList = [];
let currentWordIndex = 0;
let currentWordData = null;

let activeView = 'single'; // 'single' | 'compare' | 'benchmark'
let activeModel = '';
let compareModelA = '';
let compareModelB = '';

// Toggles
let showHeatmap = true;
let showCounts = true;
let showConsensus = true;
let showMedian = true;

// DOM Elements
const tabSingle = document.getElementById('tab-single');
const tabCompare = document.getElementById('tab-compare');
const tabBenchmark = document.getElementById('tab-benchmark');

const statTotalModels = document.getElementById('stat-total-models');
const statTotalWords = document.getElementById('stat-total-words');

const sidebar = document.getElementById('sidebar');
const singleViewContainer = document.getElementById('single-view-container');
const compareViewContainer = document.getElementById('compare-view-container');
const benchmarkViewContainer = document.getElementById('benchmark-view-container');

// Pickers & Controls
const modelSelect = document.getElementById('model-select');
const singleModelPicker = document.getElementById('single-model-picker');
const compareModelPickers = document.getElementById('compare-model-pickers');
const compareModelSelectA = document.getElementById('compare-model-a');
const compareModelSelectB = document.getElementById('compare-model-b');

const wordSelect = document.getElementById('word-select');
const wordSearch = document.getElementById('word-search');
const wordCounterBadge = document.getElementById('word-counter-badge');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const randomBtn = document.getElementById('random-btn');

// Single Summary Elements
const singleSummaryCard = document.getElementById('single-summary-card');
const topPredictionsCard = document.getElementById('top-predictions-card');
const activeModelBadge = document.getElementById('active-model-badge');
const wordTitle = document.getElementById('word-title');
const totalSamplesVal = document.getElementById('total-samples-val');
const uniqueCellsVal = document.getElementById('unique-cells-val');
const entropyVal = document.getElementById('entropy-val');
const modePctVal = document.getElementById('mode-pct-val');

const consensusVal = document.getElementById('consensus-val');
const consensusSwatch = document.getElementById('consensus-swatch');
const consensusSub = document.getElementById('consensus-sub');

const medianVal = document.getElementById('median-val');
const medianSwatch = document.getElementById('median-swatch');
const medianDistSub = document.getElementById('median-dist-sub');

const topCoordsList = document.getElementById('top-coords-list');

// Compare Summary Elements
const comparisonSummaryCard = document.getElementById('comparison-summary-card');
const compareWordTitle = document.getElementById('compare-word-title');
const cmpAgreementVal = document.getElementById('cmp-agreement-val');
const cmpMedAgreementVal = document.getElementById('cmp-med-agreement-val');
const cmpOverlapVal = document.getElementById('cmp-overlap-val');
const cmpGridDistVal = document.getElementById('cmp-grid-dist-val');
const cmpRgbDistVal = document.getElementById('cmp-rgb-dist-val');
const cmpColAName = document.getElementById('cmp-col-a-name');
const cmpColBName = document.getElementById('cmp-col-b-name');
const cmpSwatchA = document.getElementById('cmp-swatch-a');
const cmpSwatchB = document.getElementById('cmp-swatch-b');
const cmpCoordA = document.getElementById('cmp-coord-a');
const cmpCoordB = document.getElementById('cmp-coord-b');
const cmpPctA = document.getElementById('cmp-pct-a');
const cmpPctB = document.getElementById('cmp-pct-b');
const cmpMedA = document.getElementById('cmp-med-a');
const cmpMedB = document.getElementById('cmp-med-b');

// Board Grids
const boardGrid = document.getElementById('board-grid');
const boardGridA = document.getElementById('board-grid-a');
const boardGridB = document.getElementById('board-grid-b');
const boardTitleA = document.getElementById('board-title-a');
const boardTitleB = document.getElementById('board-title-b');
const currentBoardWord = document.getElementById('current-board-word');

// Toggles
const toggleHeatmap = document.getElementById('toggle-heatmap');
const toggleCounts = document.getElementById('toggle-counts');
const toggleConsensus = document.getElementById('toggle-consensus');
const toggleMedian = document.getElementById('toggle-median');

// Benchmark elements
const benchmarkSearch = document.getElementById('benchmark-search');
const benchmarkFilterAgreement = document.getElementById('benchmark-filter-agreement');
const benchmarkTable = document.getElementById('benchmark-table');
const benchmarkTheadRow = document.getElementById('benchmark-thead-row');
const benchmarkTbody = document.getElementById('benchmark-tbody');

// Tooltip
const cellTooltip = document.getElementById('cell-tooltip');

// Benchmark cached data
let benchmarkDataCache = null;

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await fetchModels();
    await fetchBoardData();
    await fetchWordsList();

    if (wordsList.length > 0) {
        await loadCurrentWord();
    }
});

function setupEventListeners() {
    // Tab switching
    tabSingle.addEventListener('click', () => switchView('single'));
    tabCompare.addEventListener('click', () => switchView('compare'));
    tabBenchmark.addEventListener('click', () => switchView('benchmark'));

    // Model selection
    modelSelect.addEventListener('change', (e) => {
        activeModel = e.target.value;
        loadCurrentWord();
    });

    compareModelSelectA.addEventListener('change', (e) => {
        compareModelA = e.target.value;
        loadCurrentWord();
    });

    compareModelSelectB.addEventListener('change', (e) => {
        compareModelB = e.target.value;
        loadCurrentWord();
    });

    // Word selector
    wordSelect.addEventListener('change', (e) => {
        const idx = wordsList.findIndex(w => w.word === e.target.value);
        if (idx !== -1) {
            currentWordIndex = idx;
            loadCurrentWord();
        }
    });

    // Word search filtering
    wordSearch.addEventListener('input', (e) => {
        const query = e.target.value.trim().toUpperCase();
        filterWordDropdown(query);
    });

    // Navigation buttons
    prevBtn.addEventListener('click', () => {
        if (wordsList.length === 0) return;
        currentWordIndex = (currentWordIndex - 1 + wordsList.length) % wordsList.length;
        loadCurrentWord();
    });

    nextBtn.addEventListener('click', () => {
        if (wordsList.length === 0) return;
        currentWordIndex = (currentWordIndex + 1) % wordsList.length;
        loadCurrentWord();
    });

    randomBtn.addEventListener('click', () => {
        if (wordsList.length <= 1) return;
        let newIdx;
        do {
            newIdx = Math.floor(Math.random() * wordsList.length);
        } while (newIdx === currentWordIndex);
        currentWordIndex = newIdx;
        loadCurrentWord();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
        if (e.key === 'ArrowLeft') {
            prevBtn.click();
        } else if (e.key === 'ArrowRight') {
            nextBtn.click();
        }
    });

    // Toggles
    toggleHeatmap.addEventListener('change', (e) => {
        showHeatmap = e.target.checked;
        updateBoardOverlays();
    });

    toggleCounts.addEventListener('change', (e) => {
        showCounts = e.target.checked;
        updateBoardOverlays();
    });

    toggleConsensus.addEventListener('change', (e) => {
        showConsensus = e.target.checked;
        updateBoardOverlays();
    });

    toggleMedian.addEventListener('change', (e) => {
        showMedian = e.target.checked;
        updateBoardOverlays();
    });

    // Benchmark search and filter
    benchmarkSearch.addEventListener('input', renderBenchmarkTableRows);
    benchmarkFilterAgreement.addEventListener('change', renderBenchmarkTableRows);
}

// Switch between Single, Compare, and Benchmark views
function switchView(viewName) {
    activeView = viewName;

    tabSingle.classList.toggle('active', viewName === 'single');
    tabCompare.classList.toggle('active', viewName === 'compare');
    tabBenchmark.classList.toggle('active', viewName === 'benchmark');

    if (viewName === 'single') {
        sidebar.classList.remove('hidden');
        singleViewContainer.classList.remove('hidden');
        compareViewContainer.classList.add('hidden');
        benchmarkViewContainer.classList.add('hidden');

        singleModelPicker.classList.remove('hidden');
        compareModelPickers.classList.add('hidden');
        singleSummaryCard.classList.remove('hidden');
        topPredictionsCard.classList.remove('hidden');
        comparisonSummaryCard.classList.add('hidden');

        loadCurrentWord();
    } else if (viewName === 'compare') {
        sidebar.classList.remove('hidden');
        singleViewContainer.classList.add('hidden');
        compareViewContainer.classList.remove('hidden');
        benchmarkViewContainer.classList.add('hidden');

        singleModelPicker.classList.add('hidden');
        compareModelPickers.classList.remove('hidden');
        singleSummaryCard.classList.add('hidden');
        topPredictionsCard.classList.add('hidden');
        comparisonSummaryCard.classList.remove('hidden');

        loadCurrentWord();
    } else if (viewName === 'benchmark') {
        sidebar.classList.add('hidden');
        singleViewContainer.classList.add('hidden');
        compareViewContainer.classList.add('hidden');
        benchmarkViewContainer.classList.remove('hidden');

        loadBenchmarkView();
    }
}

// Fetch available models
async function fetchModels() {
    try {
        const res = await fetch('/api/models');
        const data = await res.json();
        modelsList = data.models || [];

        statTotalModels.textContent = modelsList.length;

        // Populate Model Selectors
        modelSelect.innerHTML = '';
        compareModelSelectA.innerHTML = '';
        compareModelSelectB.innerHTML = '';

        modelsList.forEach((m) => {
            const opt1 = new Option(m, m);
            const opt2 = new Option(m, m);
            const opt3 = new Option(m, m);
            modelSelect.add(opt1);
            compareModelSelectA.add(opt2);
            compareModelSelectB.add(opt3);
        });

        if (modelsList.length > 0) {
            activeModel = modelsList[0];
            compareModelA = modelsList[0];
            compareModelB = modelsList.length > 1 ? modelsList[1] : modelsList[0];

            modelSelect.value = activeModel;
            compareModelSelectA.value = compareModelA;
            compareModelSelectB.value = compareModelB;
        }
    } catch (err) {
        console.error('Error fetching models:', err);
    }
}

// Fetch Board Grid Data
async function fetchBoardData() {
    try {
        const res = await fetch('/api/board');
        boardData = await res.json();

        // Build base HTML structure for boards
        renderBoardSkeleton(boardGrid, 'single');
        renderBoardSkeleton(boardGridA, 'compareA');
        renderBoardSkeleton(boardGridB, 'compareB');
    } catch (err) {
        console.error('Error fetching board data:', err);
    }
}

// Render Board Skeleton (Grid cells with row & column headers)
function renderBoardSkeleton(container, prefix) {
    if (!boardData) return;
    container.innerHTML = '';

    // Corner cell
    const corner = document.createElement('div');
    corner.className = 'grid-corner';
    container.appendChild(corner);

    // Column Headers (1 to 30)
    boardData.cols.forEach(col => {
        const colHead = document.createElement('div');
        colHead.className = 'grid-col-header';
        colHead.textContent = col;
        container.appendChild(colHead);
    });

    // Rows and Cells (A to P)
    boardData.rows.forEach(row => {
        // Row Header
        const rowHead = document.createElement('div');
        rowHead.className = 'grid-row-header';
        rowHead.textContent = row;
        container.appendChild(rowHead);

        // 30 Cells for this row
        for (let c = 1; c <= 30; c++) {
            const coord = `${row}${c}`;
            const cellInfo = boardData.cell_map[coord];

            const cell = document.createElement('div');
            cell.className = 'board-cell';
            cell.id = `${prefix}-cell-${coord}`;
            cell.dataset.coord = coord;
            cell.dataset.prefix = prefix;
            cell.style.backgroundColor = cellInfo ? cellInfo.hex : '#222';

            // Overlay layer for heatmap
            const overlay = document.createElement('div');
            overlay.className = 'cell-overlay';
            overlay.id = `${prefix}-overlay-${coord}`;
            cell.appendChild(overlay);

            // Badge for pick count
            const badge = document.createElement('span');
            badge.className = 'cell-badge';
            badge.id = `${prefix}-badge-${coord}`;
            cell.appendChild(badge);

            // Mode Crown Marker (👑)
            const marker = document.createElement('span');
            marker.className = 'mode-marker hidden';
            marker.id = `${prefix}-marker-${coord}`;
            marker.textContent = '👑';
            cell.appendChild(marker);

            // Median Target Marker (🎯)
            const medMarker = document.createElement('span');
            medMarker.className = 'median-marker hidden';
            medMarker.id = `${prefix}-medmarker-${coord}`;
            medMarker.textContent = '🎯';
            cell.appendChild(medMarker);

            // Event Listeners for Tooltips
            cell.addEventListener('mouseenter', (e) => showCellTooltip(e, coord, prefix));
            cell.addEventListener('mousemove', (e) => positionTooltip(e));
            cell.addEventListener('mouseleave', hideCellTooltip);

            container.appendChild(cell);
        }
    });
}

// Fetch Words List
async function fetchWordsList() {
    try {
        const res = await fetch('/api/words');
        wordsList = await res.json();

        statTotalWords.textContent = wordsList.length;
        populateWordDropdown(wordsList);
    } catch (err) {
        console.error('Error fetching words list:', err);
    }
}

function populateWordDropdown(list) {
    wordSelect.innerHTML = '';
    list.forEach((item, idx) => {
        const opt = new Option(`${idx + 1}. ${item.word}`, item.word);
        wordSelect.add(opt);
    });
    if (list.length > 0 && currentWordIndex < list.length) {
        wordSelect.value = list[currentWordIndex].word;
    }
}

function filterWordDropdown(query) {
    const filtered = wordsList.filter(w => w.word.includes(query));
    populateWordDropdown(filtered);
    if (filtered.length > 0) {
        const matchIdx = wordsList.findIndex(w => w.word === filtered[0].word);
        if (matchIdx !== -1) {
            currentWordIndex = matchIdx;
            loadCurrentWord();
        }
    }
}

// Load Current Word Analysis
async function loadCurrentWord() {
    if (wordsList.length === 0) return;
    const currentWord = wordsList[currentWordIndex].word;
    wordSelect.value = currentWord;
    wordCounterBadge.textContent = `${currentWordIndex + 1} / ${wordsList.length}`;
    currentBoardWord.textContent = currentWord;

    try {
        const res = await fetch(`/api/word/${encodeURIComponent(currentWord)}`);
        currentWordData = await res.json();

        if (activeView === 'single') {
            renderSingleWordView();
        } else if (activeView === 'compare') {
            renderCompareWordView();
        }
    } catch (err) {
        console.error('Error loading word analysis:', err);
    }
}

// Render Single Model View
function renderSingleWordView() {
    if (!currentWordData || !currentWordData.models) return;

    const modelAnalysis = currentWordData.models[activeModel];
    wordTitle.textContent = currentWordData.word;
    activeModelBadge.textContent = activeModel;

    if (!modelAnalysis) {
        totalSamplesVal.textContent = '0';
        uniqueCellsVal.textContent = '0';
        entropyVal.textContent = '0.00';
        modePctVal.textContent = '0%';
        consensusVal.textContent = '-';
        consensusSwatch.style.backgroundColor = 'transparent';
        consensusSub.textContent = '';
        medianVal.textContent = '-';
        medianSwatch.style.backgroundColor = 'transparent';
        medianDistSub.textContent = '';
        topCoordsList.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;">No data for this model</div>';
        clearBoardGrid('single');
        return;
    }

    // Populate stats
    totalSamplesVal.textContent = modelAnalysis.total_samples;
    uniqueCellsVal.textContent = modelAnalysis.unique_coords_count;
    entropyVal.textContent = modelAnalysis.entropy.toFixed(2);
    modePctVal.textContent = `${modelAnalysis.mode_percentage}%`;
    
    // Mode
    consensusVal.textContent = modelAnalysis.mode_coord || '-';
    consensusSwatch.style.backgroundColor = modelAnalysis.mode_hex || 'transparent';
    consensusSub.textContent = `(${modelAnalysis.mode_percentage}%)`;

    // Median (Manhattan)
    medianVal.textContent = modelAnalysis.median_coord || '-';
    medianSwatch.style.backgroundColor = modelAnalysis.median_hex || 'transparent';
    medianDistSub.textContent = `dist media: ${modelAnalysis.median_avg_dist}`;

    // Populate Top Predictions
    topCoordsList.innerHTML = '';
    const top5 = modelAnalysis.top_coords.slice(0, 5);
    top5.forEach((item, idx) => {
        const row = document.createElement('div');
        row.className = 'top-coord-row';
        row.innerHTML = `
            <div class="top-coord-left">
                <span class="coord-rank">#${idx + 1}</span>
                <span class="color-swatch-sm" style="background-color: ${item.hex};"></span>
                <span class="coord-name">${item.coordinate}</span>
            </div>
            <div class="top-coord-right">
                <div class="coord-bar-wrap">
                    <div class="coord-bar-fill" style="width: ${item.percentage}%;"></div>
                </div>
                <span class="coord-pct">${item.percentage}%</span>
            </div>
        `;
        topCoordsList.appendChild(row);
    });

    // Render Grid
    updateBoardData('single', modelAnalysis);
}

// Render Compare View
function renderCompareWordView() {
    if (!currentWordData || !currentWordData.models) return;

    const analysisA = currentWordData.models[compareModelA];
    const analysisB = currentWordData.models[compareModelB];

    compareWordTitle.textContent = currentWordData.word;
    boardTitleA.textContent = compareModelA;
    boardTitleB.textContent = compareModelB;
    cmpColAName.textContent = compareModelA;
    cmpColBName.textContent = compareModelB;

    if (analysisA && analysisB) {
        const modeA = analysisA.mode_coord;
        const modeB = analysisB.mode_coord;
        const isModeMatch = modeA === modeB;

        cmpAgreementVal.textContent = isModeMatch ? 'MATCH' : 'DIVERGENCE';
        cmpAgreementVal.className = `m-val badge ${isModeMatch ? 'match' : 'diff'}`;

        const medA = analysisA.median_coord;
        const medB = analysisB.median_coord;
        const isMedMatch = medA === medB;
        cmpMedAgreementVal.textContent = isMedMatch ? 'MATCH' : 'DIVERGENCE';
        cmpMedAgreementVal.className = `m-val badge ${isMedMatch ? 'match' : 'diff'}`;

        // Overlap
        const c1 = analysisA.counts_per_coord;
        const c2 = analysisB.counts_per_coord;
        const allCoords = new Set([...Object.keys(c1), ...Object.keys(c2)]);
        let overlap = 0;
        allCoords.forEach(k => {
            overlap += Math.min((c1[k] || 0) / analysisA.total_samples, (c2[k] || 0) / analysisB.total_samples);
        });
        cmpOverlapVal.textContent = `${(overlap * 100).toFixed(1)}%`;

        // Distances
        if (currentWordData.comparison) {
            const gd = currentWordData.comparison.mode_grid_distance;
            const cd = currentWordData.comparison.mode_rgb_distance;
            cmpGridDistVal.textContent = gd !== null ? `${gd} cells` : '-';
            cmpRgbDistVal.textContent = cd !== null ? `${cd}` : '-';
        }

        // Versus Swatches
        cmpSwatchA.style.backgroundColor = analysisA.mode_hex;
        cmpCoordA.textContent = modeA;
        cmpPctA.textContent = `${analysisA.mode_percentage}%`;
        cmpMedA.textContent = `🎯 ${analysisA.median_coord} (d: ${analysisA.median_avg_dist})`;

        cmpSwatchB.style.backgroundColor = analysisB.mode_hex;
        cmpCoordB.textContent = modeB;
        cmpPctB.textContent = `${analysisB.mode_percentage}%`;
        cmpMedB.textContent = `🎯 ${analysisB.median_coord} (d: ${analysisB.median_avg_dist})`;
    }

    // Render both grids
    if (analysisA) updateBoardData('compareA', analysisA);
    else clearBoardGrid('compareA');

    if (analysisB) updateBoardData('compareB', analysisB);
    else clearBoardGrid('compareB');
}

// Update Board Data on Grid
function updateBoardData(prefix, modelAnalysis) {
    if (!boardData) return;

    const counts = modelAnalysis ? modelAnalysis.counts_per_coord : {};
    const maxCount = modelAnalysis ? modelAnalysis.max_count : 1;
    const modeCoord = modelAnalysis ? modelAnalysis.mode_coord : null;
    const medianCoord = modelAnalysis ? modelAnalysis.median_coord : null;

    boardData.cells.forEach(cellInfo => {
        const coord = cellInfo.coord;
        const count = counts[coord] || 0;
        const pct = count / (modelAnalysis ? modelAnalysis.total_samples : 100);

        const cell = document.getElementById(`${prefix}-cell-${coord}`);
        const overlay = document.getElementById(`${prefix}-overlay-${coord}`);
        const badge = document.getElementById(`${prefix}-badge-${coord}`);
        const marker = document.getElementById(`${prefix}-marker-${coord}`);
        const medMarker = document.getElementById(`${prefix}-medmarker-${coord}`);

        const isMode = coord === modeCoord;
        const isMedian = coord === medianCoord;

        // Cell glow classes
        if (cell) {
            cell.classList.toggle('cell-is-mode', isMode && showConsensus);
            cell.classList.toggle('cell-is-median', isMedian && showMedian);
        }

        // Heatmap overlay
        if (overlay) {
            if (count > 0 && showHeatmap) {
                const alpha = Math.min(0.88, 0.25 + (count / maxCount) * 0.65);
                if (pct > 0.4) {
                    overlay.style.backgroundColor = `rgba(239, 68, 68, ${alpha})`;
                } else if (pct > 0.15) {
                    overlay.style.backgroundColor = `rgba(251, 191, 36, ${alpha})`;
                } else {
                    overlay.style.backgroundColor = `rgba(255, 255, 255, ${alpha * 0.7})`;
                }
            } else {
                overlay.style.backgroundColor = 'transparent';
            }
        }

        // Badge
        if (badge) {
            if (count > 0 && showCounts) {
                badge.textContent = count;
                badge.style.display = 'block';
            } else {
                badge.textContent = '';
                badge.style.display = 'none';
            }
        }

        // Mode Crown Marker (👑)
        if (marker) {
            if (isMode && count > 0 && showConsensus) {
                marker.classList.remove('hidden');
            } else {
                marker.classList.add('hidden');
            }
        }

        // Median Target Marker (🎯)
        if (medMarker) {
            if (isMedian && showMedian) {
                medMarker.classList.remove('hidden');
            } else {
                medMarker.classList.add('hidden');
            }
        }
    });
}

function clearBoardGrid(prefix) {
    if (!boardData) return;
    boardData.cells.forEach(cellInfo => {
        const coord = cellInfo.coord;
        const cell = document.getElementById(`${prefix}-cell-${coord}`);
        const overlay = document.getElementById(`${prefix}-overlay-${coord}`);
        const badge = document.getElementById(`${prefix}-badge-${coord}`);
        const marker = document.getElementById(`${prefix}-marker-${coord}`);
        const medMarker = document.getElementById(`${prefix}-medmarker-${coord}`);
        if (cell) {
            cell.classList.remove('cell-is-mode', 'cell-is-median');
        }
        if (overlay) overlay.style.backgroundColor = 'transparent';
        if (badge) badge.textContent = '';
        if (marker) marker.classList.add('hidden');
        if (medMarker) medMarker.classList.add('hidden');
    });
}

function updateBoardOverlays() {
    if (activeView === 'single') {
        const modelAnalysis = currentWordData && currentWordData.models ? currentWordData.models[activeModel] : null;
        updateBoardData('single', modelAnalysis);
    } else if (activeView === 'compare') {
        const aA = currentWordData && currentWordData.models ? currentWordData.models[compareModelA] : null;
        const aB = currentWordData && currentWordData.models ? currentWordData.models[compareModelB] : null;
        updateBoardData('compareA', aA);
        updateBoardData('compareB', aB);
    }
}

// Benchmark Table View
async function loadBenchmarkView() {
    try {
        if (!benchmarkDataCache) {
            const res = await fetch('/api/benchmark');
            benchmarkDataCache = await res.json();
        }

        renderBenchmarkTableStructure();
        renderBenchmarkTableRows();
    } catch (err) {
        console.error('Error loading benchmark:', err);
    }
}

function renderBenchmarkTableStructure() {
    if (!benchmarkDataCache) return;
    const models = benchmarkDataCache.models;

    benchmarkTheadRow.innerHTML = `
        <th style="width: 50px;">#</th>
        <th style="width: 160px;">Word</th>
        ${models.map(m => `<th>👑 ${m} Mode</th><th>🎯 ${m} Media</th>`).join('')}
        ${models.length >= 2 ? '<th>Mode Agreement</th><th>Median Agreement</th>' : ''}
        <th style="width: 100px;">Action</th>
    `;
}

function renderBenchmarkTableRows() {
    if (!benchmarkDataCache) return;

    const query = benchmarkSearch.value.trim().toUpperCase();
    const filter = benchmarkFilterAgreement.value;
    const rows = benchmarkDataCache.rows;
    const models = benchmarkDataCache.models;

    benchmarkTbody.innerHTML = '';

    let displayedCount = 0;
    rows.forEach((row, idx) => {
        if (query && !row.word.includes(query)) return;
        if (filter === 'match' && !row.agreement) return;
        if (filter === 'diff' && row.agreement) return;

        displayedCount++;
        const tr = document.createElement('tr');

        let modelsColsHtml = '';
        models.forEach(m => {
            const mode = row[`${m}_mode`] || '-';
            const pct = row[`${m}_pct`] || 0;
            const hex = row[`${m}_hex`] || '#888888';
            
            const median = row[`${m}_median`] || '-';
            const medHex = row[`${m}_med_hex`] || '#888888';
            const medDist = row[`${m}_med_dist`] || 0;

            modelsColsHtml += `
                <td>
                    <div class="mode-cell-wrap">
                        <span class="color-swatch-sm" style="background-color: ${hex}; width: 18px; height: 18px;"></span>
                        <span class="font-mono font-bold">${mode}</span>
                        <span style="font-size:0.75rem;color:var(--text-muted);">(${pct}%)</span>
                    </div>
                </td>
                <td>
                    <div class="mode-cell-wrap">
                        <span class="color-swatch-sm" style="background-color: ${medHex}; width: 18px; height: 18px;"></span>
                        <span class="font-mono font-bold" style="color:var(--accent-cyan);">${median}</span>
                        <span style="font-size:0.72rem;color:var(--text-muted);">(d:${medDist})</span>
                    </div>
                </td>
            `;
        });

        let comparisonColsHtml = '';
        if (models.length >= 2) {
            const isMatch = row.agreement;
            const isMedMatch = row.med_agreement;
            comparisonColsHtml = `
                <td><span class="badge ${isMatch ? 'match' : 'diff'}">${isMatch ? 'MATCH' : 'DIFF'}</span></td>
                <td><span class="badge ${isMedMatch ? 'match' : 'diff'}">${isMedMatch ? 'MATCH' : 'DIFF'}</span></td>
            `;
        }

        tr.innerHTML = `
            <td style="color:var(--text-muted);">${idx + 1}</td>
            <td>
                <button class="benchmark-word-btn" onclick="jumpToWord('${row.word}')">${row.word}</button>
            </td>
            ${modelsColsHtml}
            ${comparisonColsHtml}
            <td>
                <button class="btn btn-sm" onclick="jumpToWord('${row.word}')">View 🔍</button>
            </td>
        `;

        benchmarkTbody.appendChild(tr);
    });

    if (displayedCount === 0) {
        benchmarkTbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:2rem;color:var(--text-muted);">No words matching search or filter criteria.</td></tr>`;
    }
}

// Jump to word from Benchmark table
window.jumpToWord = function(word) {
    const idx = wordsList.findIndex(w => w.word === word);
    if (idx !== -1) {
        currentWordIndex = idx;
        switchView('single');
    }
};

// Hover Tooltip Handlers
function showCellTooltip(e, coord, prefix) {
    if (!boardData) return;
    const cell = boardData.cell_map[coord];
    if (!cell) return;

    let modelName = activeModel;
    if (prefix === 'compareA') modelName = compareModelA;
    if (prefix === 'compareB') modelName = compareModelB;

    const analysis = currentWordData && currentWordData.models ? currentWordData.models[modelName] : null;
    const count = analysis && analysis.counts_per_coord ? (analysis.counts_per_coord[coord] || 0) : 0;
    const total = analysis ? analysis.total_samples : 100;
    const pct = ((count / total) * 100).toFixed(1);
    
    const isMode = analysis && analysis.mode_coord === coord;
    const isMedian = analysis && analysis.median_coord === coord;

    let badgesHtml = '';
    if (isMode) badgesHtml += `<span style="color: var(--accent-gold); font-size: 0.75rem; font-weight: 700;">👑 Moda</span> `;
    if (isMedian) badgesHtml += `<span style="color: var(--accent-cyan); font-size: 0.75rem; font-weight: 700;">🎯 Media Manhattan</span>`;

    cellTooltip.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;">
            <div class="tooltip-coord">${coord}</div>
            <span class="color-swatch-sm" style="background-color: ${cell.hex}; width: 18px; height: 18px;"></span>
        </div>
        ${badgesHtml ? `<div style="margin-top: 2px;">${badgesHtml}</div>` : ''}
        <div class="tooltip-stat-row">
            <span>Hex / RGB:</span>
            <span class="val">${cell.hex}</span>
        </div>
        <div class="tooltip-stat-row">
            <span>Model:</span>
            <span class="val" style="color: #a5b4fc;">${modelName}</span>
        </div>
        <div class="tooltip-stat-row">
            <span>Picks:</span>
            <span class="val" style="color: var(--accent-gold); font-size: 0.85rem;">${count} / ${total} (${pct}%)</span>
        </div>
        ${isMedian ? `
        <div class="tooltip-stat-row">
            <span>Distancia media:</span>
            <span class="val" style="color: var(--accent-cyan);">${analysis.median_avg_dist} celdas</span>
        </div>` : ''}
    `;

    cellTooltip.style.display = 'flex';
    positionTooltip(e);
}

function positionTooltip(e) {
    const x = e.clientX + 16;
    const y = e.clientY + 16;
    cellTooltip.style.left = `${x}px`;
    cellTooltip.style.top = `${y}px`;
}

function hideCellTooltip() {
    cellTooltip.style.display = 'none';
}
