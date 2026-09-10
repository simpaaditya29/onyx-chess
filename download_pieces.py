import urllib.request
import os

def download_chess_pieces():
    # Create the assets folder automatically
    os.makedirs("assets/pieces", exist_ok=True)
    
    # High-res piece set
    pieces = ['wp', 'wn', 'wb', 'wr', 'wq', 'wk', 'bp', 'bn', 'bb', 'br', 'bq', 'bk']
    base_url = "https://images.chesscomfiles.com/chess-themes/pieces/neo/150/"
    
    print("Downloading high-res piece graphics...")
    
    for piece in pieces:
        # Save as wP.png, bK.png, etc.
        save_name = f"{piece[0]}{piece[1].upper()}.png" 
        url = f"{base_url}{piece}.png"
        filepath = os.path.join("assets/pieces", save_name)
        
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"Downloaded {save_name}")
        except Exception as e:
            print(f"Failed to download {piece}: {e}")
            
    print("\nAll pieces downloaded into the 'assets/pieces' folder!")

if __name__ == "__main__":
    download_chess_pieces()