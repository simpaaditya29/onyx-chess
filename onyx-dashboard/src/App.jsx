import { useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';

export default function App() {
  const [game, setGame] = useState(new Chess());
  const [puzzleData, setPuzzleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Click 'Load Puzzle' to start training.");

  const loadNewPuzzle = async () => {
    setLoading(true);
    setMessage("Loading 1GB Database...");
    
    try {
      const response = await fetch('http://127.0.0.1:8080/api/puzzle?min_elo=1800');
      const data = await response.json();
      
      if (data.status === 'success') {
        setPuzzleData(data.data);
        const newGame = new Chess(data.data.FEN);
        setGame(newGame);
        
        // Tell the player whose turn it is!
        const turn = newGame.turn() === 'w' ? "White" : "Black";
        setMessage(`🔥 Puzzle Loaded! (Rating: ${data.data.Rating}) | It is ${turn}'s turn!`);
      } else {
        setMessage("Error loading puzzle.");
      }
    } catch (error) {
      console.error(error);
      setMessage("Failed to connect to Python Backend.");
    }
    
    setLoading(false);
  };

  // Safe move logic for the visual board
  function onDrop(sourceSquare, targetSquare) {
    try {
      // Create a fresh copy of the game so React knows to update the screen
      const gameCopy = new Chess(game.fen());
      
      const move = gameCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q', 
      });

      if (move === null) return false; 
      
      // Save the new board state
      setGame(gameCopy);
      setMessage("Great move! (Full sequence validation coming soon)");
      return true;
    } catch (e) {
      // If the move is illegal, chess.js throws an error and we snap the piece back
      return false;
    }
  }

  // Automatically flip the board based on whose turn it is
  const boardOrientation = game.turn() === 'w' ? 'white' : 'black';

  return (
    <div style={{ fontFamily: 'sans-serif', backgroundColor: '#121212', color: '#ffffff', minHeight: '100vh', padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h1 style={{ color: '#00ffcc', textTransform: 'uppercase', letterSpacing: '2px' }}>♟️ Onyx Chess Trainer</h1>
      
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#1e1e1e', borderRadius: '8px', width: '100%', maxWidth: '600px', textAlign: 'center' }}>
        <p style={{ margin: 0, fontSize: '18px', color: '#a0a0a0' }}>{message}</p>
      </div>

      <div style={{ width: '500px', boxShadow: '0 10px 30px rgba(0,255,204,0.2)' }}>
        <Chessboard 
          position={game.fen()} 
          onPieceDrop={onDrop}
          boardOrientation={boardOrientation}
          customDarkSquareStyle={{ backgroundColor: '#2f4f4f' }}
          customLightSquareStyle={{ backgroundColor: '#c0c0c0' }}
        />
      </div>

      <button 
        onClick={loadNewPuzzle} 
        disabled={loading}
        style={{ 
          marginTop: '30px', 
          padding: '12px 24px', 
          fontSize: '18px', 
          fontWeight: 'bold', 
          backgroundColor: '#00ffcc', 
          color: '#121212', 
          border: 'none', 
          borderRadius: '5px', 
          cursor: loading ? 'not-allowed' : 'pointer' 
        }}
      >
        {loading ? "Scanning Database..." : "Load Level 1800+ Puzzle"}
      </button>
    </div>
  );
}