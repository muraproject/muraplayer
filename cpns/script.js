// Global variables
let currentPackage = null;
let questions = [];
let currentQuestionIndex = 0;
let userAnswers = [];
let timeLeft = 0;
let timerInterval = null;
let isTryout = false;

let allPackages = {
    cpns: [],
    pppk: [],
    tryout: []
};
// Initialize the app
let currentCategory = 'cpns';


// Helper functions
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function showScreen(screenId) {
    console.log('Showing screen:', screenId);
    document.querySelectorAll('.screen').forEach(screen => screen.classList.add('hidden'));
    document.getElementById(screenId).classList.remove('hidden');
}

async function fetchJSON(url) {
    console.log('Fetching JSON from:', url);
    try {
        const response = await fetch(url);
        const data = await response.json();
        console.log('Fetched data:', data);
        return data;
    } catch (error) {
        console.error('Error fetching JSON:', error);
        throw error;
    }
}


async function init() {
    console.log('Initializing app');
    const packageName = getUrlParameter('package');
    isTryout = getUrlParameter('mode') === 'tryout';

    if (packageName) {
        console.log('Loading specific package:', packageName);
        currentPackage = await fetchJSON(`data/${packageName}.json`);
        questions = currentPackage.questions;
        showWarningScreen();
    } else {
        console.log('Loading all package lists');
        await loadAllPackages();
        renderPackageList(allPackages[currentCategory]);
        showScreen('home-screen');
    }

    setupNavigation();
}

async function loadAllPackages() {
    const categories = ['cpns', 'pppk', 'tryout'];
    for (let category of categories) {
        const packagesData = await fetchJSON(`data/${category}-packages.json`);
        if (packagesData && packagesData.packages) {
            allPackages[category] = packagesData.packages;
        } else {
            console.error(`Invalid packages data structure for ${category}`);
        }
    }
    console.log('All packages loaded:', allPackages);
}


function renderPackageList(packages) {
    console.log('Rendering package list:', packages);
    const packageList = document.getElementById('package-list');
    if (!packageList) {
        console.error('Package list element not found');
        return;
    }
    packageList.innerHTML = packages.map(pkg => `
        <div class="col">
            <div class="card h-100 package-card" data-package="${pkg.id}">
                <div class="card-body">
                    <h5 class="card-title">${pkg.name}</h5>
                    <p class="card-text">${pkg.description}</p>
                    <a href="?package=${pkg.id}" class="btn btn-primary">Mulai Tes</a>
                </div>
            </div>
        </div>
    `).join('');
}

function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            currentCategory = e.target.dataset.category;
            navLinks.forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');

            // Reset state
            currentPackage = null;
            questions = [];
            currentQuestionIndex = 0;
            userAnswers = [];
            clearInterval(timerInterval);

            // Render package list and show home screen
            renderPackageList(allPackages[currentCategory]);
            showScreen('home-screen');
        });
    });
}

function showScreen(screenId) {
    console.log('Showing screen:', screenId);
    document.querySelectorAll('.screen').forEach(screen => screen.classList.add('hidden'));
    document.getElementById(screenId).classList.remove('hidden');

    // Tampilkan bottom navigation hanya pada home screen
    const bottomNav = document.querySelector('.navbar.fixed-bottom');
    if (bottomNav) {
        bottomNav.style.display = (screenId === 'home-screen') ? 'flex' : 'none';
    }
}

function showWarningScreen() {
    showScreen('warning-screen');
    document.getElementById('start-test').addEventListener('click', startTest);
    document.getElementById('cancel-test').addEventListener('click', () => window.location.href = '/');
}

function startTest() {
    showScreen('test-screen');
    renderQuestion();
    renderQuestionNavigation();
    if (isTryout) {
        startTimer();
    }
}

// ... (kode sebelumnya tetap sama)

function renderQuestion() {
    const question = questions[currentQuestionIndex];
    document.getElementById('question-number').textContent = `Soal ${currentQuestionIndex + 1}`;
    document.getElementById('question-text').textContent = question.text;
    
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = question.options.map((option, index) => `
        <div class="form-check mb-2">
            <input class="form-check-input" type="radio" name="questionOption" id="option${index}" value="${index}" ${userAnswers[currentQuestionIndex] === index ? 'checked' : ''}>
            <label class="form-check-label" for="option${index}">
                ${String.fromCharCode(65 + index)}. ${option}
            </label>
        </div>
    `).join('');

    optionsContainer.addEventListener('change', (e) => {
        if (e.target.type === 'radio') {
            userAnswers[currentQuestionIndex] = parseInt(e.target.value);
            updateQuestionNavigation();
        }
    });

    updateNavigation();
}

function updateQuestionNavigation() {
    const buttons = document.querySelectorAll('.question-button');
    buttons.forEach((button, index) => {
        if (userAnswers[index] !== undefined) {
            button.classList.remove('btn-outline-secondary', 'btn-danger');
            button.classList.add('btn-success');
        } else {
            button.classList.remove('btn-success', 'btn-danger');
            button.classList.add('btn-outline-secondary');
        }
    });
}

function updateNavigation() {
    document.getElementById('prev-question').disabled = currentQuestionIndex === 0;
    document.getElementById('next-question').disabled = currentQuestionIndex === questions.length - 1;
    document.getElementById('clear-answer').disabled = userAnswers[currentQuestionIndex] === undefined;
}

// Tambahkan fungsi baru untuk menghapus jawaban
function clearAnswer() {
    userAnswers[currentQuestionIndex] = undefined;
    renderQuestion();
    updateQuestionNavigation();
}

// ... (kode lainnya tetap sama)

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded');
    init().catch(error => console.error('Initialization error:', error));
});

document.getElementById('next-question').addEventListener('click', () => {
    currentQuestionIndex++;
    renderQuestion();
    updateQuestionNavigation();
});

document.getElementById('prev-question').addEventListener('click', () => {
    currentQuestionIndex--;
    renderQuestion();
    updateQuestionNavigation();
});

document.getElementById('clear-answer').addEventListener('click', clearAnswer);

document.getElementById('finish-test').addEventListener('click', () => {
    if (confirm('Apakah Anda yakin ingin menyelesaikan tes?')) {
        finishTest();
    }
});

function renderQuestionNavigation() {
    const nav = document.getElementById('question-nav');
    nav.innerHTML = questions.map((_, index) => `
        <button class="btn btn-outline-secondary question-button" data-index="${index}">${index + 1}</button>
    `).join('');

    nav.addEventListener('click', (e) => {
        const button = e.target.closest('.question-button');
        if (button) {
            currentQuestionIndex = parseInt(button.dataset.index);
            renderQuestion();
        }
    });
}

function updateQuestionNavigation() {
    const buttons = document.querySelectorAll('.question-button');
    buttons.forEach((button, index) => {
        if (userAnswers[index] !== undefined) {
            button.classList.remove('btn-outline-secondary', 'btn-danger');
            button.classList.add('btn-success');
        } else if (index < currentQuestionIndex) {
            button.classList.remove('btn-outline-secondary', 'btn-success');
            button.classList.add('btn-danger');
        } else {
            button.classList.remove('btn-success', 'btn-danger');
            button.classList.add('btn-outline-secondary');
        }
    });
}

function updateNavigation() {
    document.getElementById('prev-question').disabled = currentQuestionIndex === 0;
    document.getElementById('next-question').disabled = currentQuestionIndex === questions.length - 1;
}

function startTimer() {
    timeLeft = questions.length * 90; // 1.5 minutes per question
    updateTimerDisplay();
    timerInterval = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            finishTest();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    document.getElementById('timer').textContent = `Waktu tersisa: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function finishTest() {
    clearInterval(timerInterval);
    showScreen('result-screen');
    const score = calculateScore();
    renderResults(score);
}

function calculateScore() {
    let correct = 0;
    questions.forEach((question, index) => {
        if (userAnswers[index] === question.correctAnswer) {
            correct++;
        }
    });
    return {
        correct,
        total: questions.length,
        percentage: (correct / questions.length) * 100
    };
}

function renderResults(score) {
    document.getElementById('score-summary').innerHTML = `
        <p>Jawaban Benar: ${score.correct}</p>
        <p>Total Soal: ${score.total}</p>
        <p>Persentase: ${score.percentage.toFixed(2)}%</p>
    `;

    const detailedResults = document.getElementById('detailed-results');
    detailedResults.innerHTML = questions.map((question, index) => `
        <div class="list-group-item ${userAnswers[index] === question.correctAnswer ? 'list-group-item-success' : 'list-group-item-danger'}">
            <h5 class="mb-1">Soal ${index + 1}</h5>
            <p>${question.text}</p>
            <p>Jawaban Anda: ${String.fromCharCode(65 + userAnswers[index])}. ${question.options[userAnswers[index]]}</p>
            <p>Jawaban Benar: ${String.fromCharCode(65 + question.correctAnswer)}. ${question.options[question.correctAnswer]}</p>
        </div>
    `).join('');

    // document.getElementById('back-to-home').addEventListener('click', () => window.location.href = '/index.html');
}
// document.getElementById('back-to-home').addEventListener('click', backToHome);

// Event listeners
// function backToHome() {
//     function backToHome() {
//         // Reset semua variabel global
//         currentPackage = null;
//         questions = [];
//         currentQuestionIndex = 0;
//         userAnswers = [];
//         timeLeft = 0;
//         clearInterval(timerInterval);
//         isTryout = false;
    
//         // Kembali ke domain utama
//         window.location.href = window.location.origin;
//     }
// }