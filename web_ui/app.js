var board = null;
var game = new Chess();
var currentCategory = "Catalan Opening Lines";
var currentMode = "interrogator";
var playerColor = 'w'; // 'w' or 'b'
var selectedRating = 1200;

var config = {
  draggable: true,
  position: 'start',
  pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png',
  onDrop: handleMove
};

board = Chessboard('myBoard', config);

function handleMove(source, target) {
  var fenBefore = game.fen();
  
  var move = game.move({
    from: source,
    to: target,
    promotion: 'q'
  });

  if (move === null) return 'snapback';

  var userUci = source + target;
  const log = document.getElementById('move-log');

  // 1. Interrogator Mode
  if (currentMode === 'interrogator') {
    fetch('/api/interrogator/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen: fenBefore, move: userUci, category: currentCategory })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'correct') {
        log.innerHTML += `<p>✅ You: ${move.san}</p>`;
        setTimeout(() => {
          game.move(data.bot_move, { sloppy: true });
          board.position(game.fen());
          log.innerHTML += `<p>🤖 Book: ${data.bot_san}</p>`; // Standard Algebraic Notation
        }, 300);
      } else if (data.status === 'reset') {
        log.innerHTML = `<p style="color: #ff5555;">${data.message}</p>`;
        setTimeout(() => { game.reset(); board.start(); }, 800);
      }
    });
  }
  
  // 2. Play vs Bot / Sparring
  else if (currentMode === 'sparring' || currentMode === 'play_bot') {
    log.innerHTML += `<p>👤 You: ${move.san}</p>`;
    
    fetch('/api/engine/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen: game.fen(), rating: selectedRating }) 
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        setTimeout(() => {
          game.move(data.bot_move, { sloppy: true });
          board.position(game.fen());
          log.innerHTML += `<p>🤖 Onyx AI: ${data.bot_san}</p>`; // Standard Algebraic Notation
        }, 400); 
      }
    });
  }
  
  // 3. Pass 'N Play
  else if (currentMode === 'pass_play') {
    const colorName = game.turn() === 'w' ? 'Black' : 'White'; 
    log.innerHTML += `<p>👥 ${colorName}: ${move.san}</p>`;
  }
}

// Check if user selected Custom Time Control
function checkCustomTime() {
    const val1 = document.getElementById('variant-selector-1').value;
    const customGrp = document.getElementById('custom-time-group');
    if (val1 === 'Custom Time Control') {
        customGrp.style.display = 'flex';
    } else {
        customGrp.style.display = 'none';
    }
}

// Mode Switching Logic
function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
    
    const activeNav = document.getElementById('nav-' + mode);
    if (activeNav) activeNav.classList.add('active');

    const title = document.getElementById('mode-title');
    const desc = document.getElementById('mode-desc');
    const optionsPanel = document.getElementById('mode-options');
    
    const grp1 = document.getElementById('select-group-1');
    const grp2 = document.getElementById('select-group-2');
    const grp3 = document.getElementById('select-group-3');
    const pgnGrp = document.getElementById('pgn-input-group');
    const customGrp = document.getElementById('custom-time-group');

    const lbl1 = document.getElementById('options-label-1');
    const lbl2 = document.getElementById('options-label-2');
    const sel1 = document.getElementById('variant-selector-1');
    const sel2 = document.getElementById('variant-selector-2');
    const boardElement = document.getElementById('myBoard');

    // Reset UI visibility
    optionsPanel.style.display = 'none';
    grp2.style.display = 'none';
    grp3.style.display = 'none';
    pgnGrp.style.display = 'none';
    customGrp.style.display = 'none';
    boardElement.classList.remove('blindfold-active');
    sel1.innerHTML = '';
    sel2.innerHTML = '';

    const modeDetails = {
        'play_bot': {
            title: 'Play vs Bot',
            desc: 'Select Rating, Time Control, and Side to play.',
            needsOptions: true,
            lbl1: 'Bot Rating:', opts1: ['800 (Beginner)', '1200 (Intermediate)', '1500 (Club)', '1800 (Advanced)', '2200 (Master)'],
            hasSecond: true, lbl2: 'Time Control:', opts2: ['Unlimited', '1|0 Bullet', '3|0 Blitz', '3|2 Blitz', '5|0 Blitz', '10|0 Rapid', 'Custom Time Control'],
            hasSide: true
        },
        'puzzles': {
            title: 'Puzzle Dashboard',
            desc: 'Choose puzzle difficulty and tactical theme.',
            needsOptions: true,
            lbl1: 'Difficulty Rating:', opts1: ['< 1000 (Beginner)', '1000 - 1400 (Intermediate)', '1400 - 1800 (Advanced)', '1800 - 2200 (Expert)', '2200+ (Master)'],
            hasSecond: true, lbl2: 'Theme:', opts2: ['All Themes', 'Guess the Move (GM Games)', 'Forks & Double Attacks', 'Pins & Skewers', 'Mate in 1 / Mate in 2', 'Endgame Tactics']
        },
        'interrogator': {
            title: 'Opening Coach',
            desc: 'Drill repertoire lines with instant error resets.',
            needsOptions: true,
            lbl1: 'Select Opening:', opts1: ['Catalan Opening Lines', 'Nimzo-Indian Defense', 'Sicilian Dragon', 'Caro-Kann Defense']
        },
        'pgn_analysis': {
            title: 'PGN Analysis',
            desc: 'Paste game notation or file path for evaluation.',
            needsOptions: true,
            isPgn: true
        },
        'timed_mode': {
            title: 'Timed Mode',
            desc: 'Rapid calculation drills under severe time pressure.',
            needsOptions: true,
            lbl1: 'Time Limit:', opts1: ['1 Minute Rapid-Fire', '3 Minutes Rush', '5 Minutes Survival']
        },
        'blindfold': {
            title: 'Blindfold Mode',
            desc: 'Train visualization. Board is fully playable, but pieces are invisible.'
        }
    };

    if (modeDetails[mode]) {
        title.innerText = modeDetails[mode].title;
        desc.innerText = modeDetails[mode].desc;

        if (modeDetails[mode].needsOptions) {
            optionsPanel.style.display = 'flex';

            if (modeDetails[mode].isPgn) {
                grp1.style.display = 'none';
                pgnGrp.style.display = 'block';
            } else {
                grp1.style.display = 'inline-block';
                lbl1.innerText = modeDetails[mode].lbl1;
                modeDetails[mode].opts1.forEach(o => sel1.innerHTML += `<option value="${o}">${o}</option>`);

                if (modeDetails[mode].hasSecond) {
                    grp2.style.display = 'inline-block';
                    lbl2.innerText = modeDetails[mode].lbl2;
                    modeDetails[mode].opts2.forEach(o => sel2.innerHTML += `<option value="${o}">${o}</option>`);
                }

                if (modeDetails[mode].hasSide) {
                    grp3.style.display = 'inline-block';
                }
            }
        }

        if (mode === 'blindfold') {
            boardElement.classList.add('blindfold-active');
        }
    }
}

// Apply settings and handle Side flipping (White/Black)
function loadVariant() {
    const sel1 = document.getElementById('variant-selector-1').value;
    const sideChoice = document.getElementById('variant-selector-3').value;
    const log = document.getElementById('move-log');

    // Parse Rating
    if (sel1.includes('800')) selectedRating = 800;
    else if (sel1.includes('1200')) selectedRating = 1200;
    else if (sel1.includes('1500')) selectedRating = 1500;
    else if (sel1.includes('1800')) selectedRating = 1800;
    else if (sel1.includes('2200')) selectedRating = 2200;

    // Handle Side Selection (White/Black/Random)
    if (currentMode === 'play_bot' || currentMode === 'sparring') {
        if (sideChoice === 'black') {
            playerColor = 'b';
            board.orientation('black');
            log.innerHTML = `<p style="color: var(--accent-teal);">Playing as Black vs Bot (${selectedRating}). Bot moves first...</p>`;
            game.reset();
            board.position(game.fen());
            
            // Bot plays first move as White
            fetch('/api/engine/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fen: game.fen(), rating: selectedRating })
            })
            .then(res => res.json())
            .then(data => {
                game.move(data.bot_move, { sloppy: true });
                board.position(game.fen());
                log.innerHTML += `<p>🤖 Onyx AI: ${data.bot_san}</p>`;
            });
            return;
        } else {
            playerColor = 'w';
            board.orientation('white');
        }
    }

    log.innerHTML = `<p style="color: var(--accent-teal);">Loaded: ${sel1}</p>`;
    game.reset();
    board.start();
}

// Control Buttons
document.getElementById('startBtn').addEventListener('click', function() {
  game.reset();
  board.start();
  document.getElementById('move-log').innerHTML = "";
});

document.getElementById('clearBtn').addEventListener('click', function() {
  game.clear();
  board.clear();
});